import random
import datetime
import mysql.connector
from mysql.connector import errorcode

# --- DATABASE CONFIGURATION ---
DB_CONFIG = {
    'user': 'root',
    'password': 'Hecther',
    'host': 'Yoga-Master',
    'port': 3306,
    'database': 'digital_harvest'
}

class BusinessSimulator:
    def __init__(self, db_config):
        try:
            self.db_connection = mysql.connector.connect(**db_config)
            self.cursor = self.db_connection.cursor(dictionary=True)
            print("Successfully connected to MySQL database.")
            self._load_state()
        except mysql.connector.Error as err:
            print(f"Database connection failed: {err}")
            exit(1)

        print(f"Business simulation loaded. Cash: ${self.cash:,.2f}, Date: {self.current_date.date()}.")

    def _load_state(self):
        """Loads cash and date from the database, or sets defaults."""
        self.cursor.execute("SELECT state_key, state_value FROM business_state")
        state = {row['state_key']: row['state_value'] for row in self.cursor.fetchall()}
        self.cash = float(state.get('cash_on_hand', 20000.00))
        self.current_date = datetime.datetime.strptime(state.get('current_date', '2025-01-01 09:00:00'), "%Y-%m-%d %H:%M:%S")

    def _save_state(self):
        """Saves the current cash and date to the database."""
        query = "INSERT INTO business_state (state_key, state_value) VALUES (%s, %s) ON DUPLICATE KEY UPDATE state_value = VALUES(state_value)"
        self.cursor.execute(query, ('cash_on_hand', str(self.cash)))
        self.cursor.execute(query, ('current_date', self.current_date.strftime("%Y-%m-%d %H:%M:%S")))
        self.db_connection.commit()

    def get_current_stock(self, product_id):
        """Gets the most recent quantity on hand for a product from the ledger."""
        query = ("SELECT quantity_on_hand_after FROM inventory_ledger "
                 "WHERE product_id = %s ORDER BY transaction_date DESC, entry_id DESC LIMIT 1")
        self.cursor.execute(query, (product_id,))
        result = self.cursor.fetchone()
        return result['quantity_on_hand_after'] if result else 0

    def get_avg_cost(self, product_id):
        """Calculates a simplified weighted average cost of current inventory."""
        # This is a simple average of the last 10 purchase costs. A real system might use FIFO/LIFO.
        query = ("SELECT unit_cost FROM inventory_ledger "
                 "WHERE product_id = %s AND type = 'Purchase' ORDER BY transaction_date DESC LIMIT 10")
        self.cursor.execute(query, (product_id,))
        results = self.cursor.fetchall()
        if not results:
            return 0.0
        return float(sum(r['unit_cost'] for r in results) / len(results))

    def purchase_inventory(self, product_id, quantity, unit_cost):
        """Records a purchase in both the inventory and financial ledgers."""
        total_cost = quantity * unit_cost
        if self.cash < total_cost:
            print(f"Not enough cash. Need ${total_cost:,.2f}, have ${self.cash:,.2f}")
            return

        self.cash -= total_cost
        
        current_stock = self.get_current_stock(product_id)
        new_stock = current_stock + quantity
        inv_query = ("INSERT INTO inventory_ledger (transaction_date, product_id, type, description, "
                     "quantity_change, unit_cost, total_value, quantity_on_hand_after) "
                     "VALUES (%s, %s, 'Purchase', 'Stock Purchase', %s, %s, %s, %s)")
        self.cursor.execute(inv_query, (self.current_date, product_id, quantity, unit_cost, -total_cost, new_stock))

        fin_query = ("INSERT INTO financial_ledger (transaction_date, account, description, debit, credit) "
                     "VALUES (%s, %s, %s, %s, %s)")
        self.cursor.execute(fin_query, (self.current_date, 'Inventory', f'Purchase of product {product_id}', total_cost, 0.00))
        self.cursor.execute(fin_query, (self.current_date, 'Cash', f'Payment for product {product_id}', 0.00, total_cost))

        self._save_state()
        print(f"Purchased {quantity} units of product ID {product_id} for ${total_cost:,.2f}.")

    def simulate_day_sales(self, user_prices):
        """Simulates a full day of sales."""
        query = "SELECT product_id, name, base_demand, price_sensitivity FROM products"
        self.cursor.execute(query)
        products = self.cursor.fetchall()

        for product in products:
            product_id = product['product_id']
            stock = self.get_current_stock(product_id)
            if stock <= 0:
                continue

            user_price = user_prices.get(product['name'])
            if not user_price:
                continue
            
            avg_cost = self.get_avg_cost(product_id)
            competitor_price = avg_cost * 1.5 if avg_cost > 0 else user_price
            price_factor = max(0, 1 - product['price_sensitivity'] * ((user_price - competitor_price) / competitor_price)) if competitor_price > 0 else 1
            potential_sales = product['base_demand'] * price_factor * (1 + random.uniform(-0.2, 0.2))
            units_sold = min(int(potential_sales), stock)
            
            if units_sold > 0:
                revenue = units_sold * user_price
                cost_of_goods_sold = units_sold * avg_cost
                self.cash += revenue
                
                new_stock = stock - units_sold
                inv_query = ("INSERT INTO inventory_ledger (transaction_date, product_id, type, description, "
                             "quantity_change, unit_price, total_value, quantity_on_hand_after) "
                             "VALUES (%s, %s, 'Sale', 'Customer Sale', %s, %s, %s, %s)")
                self.cursor.execute(inv_query, (self.current_date, product_id, -units_sold, user_price, revenue, new_stock))

                fin_query = ("INSERT INTO financial_ledger (transaction_date, account, description, debit, credit) "
                             "VALUES (%s, %s, %s, %s, %s)")
                self.cursor.execute(fin_query, (self.current_date, 'Cash', f'Sale of {product["name"]}', revenue, 0.00))
                self.cursor.execute(fin_query, (self.current_date, 'Sales Revenue', f'Sale of {product["name"]}', 0.00, revenue))
                self.cursor.execute(fin_query, (self.current_date, 'COGS', f'Cost for {product["name"]}', cost_of_goods_sold, 0.00))
                self.cursor.execute(fin_query, (self.current_date, 'Inventory', f'Cost for {product["name"]}', 0.00, cost_of_goods_sold))

                print(f"  - SOLD: {units_sold} of {product['name']}. Revenue: ${revenue:,.2f}")

    def record_expense(self, account, description, amount):
        """Records a general business expense."""
        if self.cash < amount:
            print(f"Not enough cash for expense. Need ${amount:,.2f}, have ${self.cash:,.2f}")
            return
        
        self.cash -= amount
        
        fin_query = ("INSERT INTO financial_ledger (transaction_date, account, description, debit, credit) "
                     "VALUES (%s, %s, %s, %s, %s)")
        self.cursor.execute(fin_query, (self.current_date, account, description, amount, 0.00))
        self.cursor.execute(fin_query, (self.current_date, 'Cash', description, 0.00, amount))
        
        self._save_state()
        print(f"Expense recorded: {description} for ${amount:,.2f}")

    def advance_time(self, days, daily_prices):
        for _ in range(days):
            day_str = self.current_date.strftime("%Y-%m-%d")
            print(f"\n--- Simulating Day: {day_str} ---")
            self.simulate_day_sales(daily_prices)
            self.current_date += datetime.timedelta(days=1)
        self._save_state()
        print(f"\n--- Advanced simulation by {days} days ---")
    
    def print_status(self):
        print("\n================== BUSINESS STATUS ==================")
        print(f"Date: {self.current_date.strftime('%Y-%m-%d')}")
        print(f"Cash on Hand: ${self.cash:,.2f}")
        
        self.cursor.execute("SELECT SUM(credit) as total_rev FROM financial_ledger WHERE account = 'Sales Revenue'")
        revenue = self.cursor.fetchone()['total_rev'] or 0.0
        print(f"Lifetime Revenue: ${float(revenue):,.2f}")

        print("--- Current Inventory ---")
        self.cursor.execute("SELECT product_id, name FROM products")
        products = self.cursor.fetchall()
        total_inv_value = 0
        for p in products:
            stock = self.get_current_stock(p['product_id'])
            avg_cost = self.get_avg_cost(p['product_id'])
            value = stock * avg_cost
            total_inv_value += value
            if stock > 0:
                print(f"  - {p['name']} (ID: {p['product_id']}): {stock} units (Avg Cost: ${avg_cost:,.2f}, Value: ${value:,.2f})")
        print(f"Total Inventory Value: ${total_inv_value:,.2f}")
        print("=====================================================")

    def reset_simulation(self, new_cash, new_date_str):
        print("\n--- RESETTING SIMULATION DATA ---")
        try:
            self.cursor.execute("TRUNCATE TABLE inventory_ledger")
            self.cursor.execute("TRUNCATE TABLE financial_ledger")
            print("  - Ledgers cleared.")
            
            self.cash = new_cash
            self.current_date = datetime.datetime.strptime(f"{new_date_str} 09:00:00", "%Y-%m-%d %H:%M:%S")
            self._save_state()
            
            print("--- RESET COMPLETE ---")
        except mysql.connector.Error as err:
            print(f"An error occurred during reset: {err}")
            self.db_connection.rollback()
    
    def __del__(self):
        try:
            if self.db_connection.is_connected():
                self._save_state()
                self.cursor.close()
                self.db_connection.close()
                print("\nMySQL connection closed.")
        except Exception:
            pass

# --- MAIN INTERACTIVE SCRIPT ---

def get_product_list(sim):
    # This is the line that was changed
    sim.cursor.execute("SELECT product_id, name FROM products ORDER BY product_id")
    return sim.cursor.fetchall()

def handle_purchase(sim):
    products = get_product_list(sim)
    print("\n--- Purchase Inventory ---")
    for p in products:
        print(f"ID {p['product_id']}: {p['name']}")
    try:
        product_id = int(input("Enter the product ID to purchase: "))
        if product_id not in [p['product_id'] for p in products]:
            print("Invalid product ID.")
            return
        quantity = int(input("Enter quantity to purchase: "))
        unit_cost = float(input("Enter the cost per unit: $"))
        sim.purchase_inventory(product_id, quantity, unit_cost)
    except ValueError:
        print("Invalid input.")

def handle_set_prices(user_prices, sim):
    products = get_product_list(sim)
    print("\n--- Set Prices ---")
    for p in products:
        current_price = f"(current: ${user_prices.get(p['name']):,.2f})" if p['name'] in user_prices else "(not set)"
        price_in = input(f"  - Set price for {p['name']} {current_price}: $")
        if price_in:
            try:
                user_prices[p['name']] = float(price_in)
            except ValueError:
                print("Invalid price.")
    return user_prices

def handle_expense(sim):
    print("\n--- Record Expense ---")
    try:
        account = input("Enter expense account (e.g., Rent, Utilities, Marketing): ")
        description = input("Enter a brief description: ")
        amount = float(input("Enter the total amount: $"))
        sim.record_expense(account, description, amount)
    except ValueError:
        print("Invalid amount.")

def handle_reset(sim):
    print("\n--- Reset Simulation ---")
    if input("Are you sure you want to reset all data? (y/n): ").lower() == 'y':
        try:
            cash = float(input("Enter new starting cash: "))
            date = input("Enter new start date (YYYY-MM-DD): ")
            sim.reset_simulation(cash, date)
            return {} # Return empty prices dict
        except ValueError:
            print("Invalid input.")
    return None

def main():
    sim = BusinessSimulator(db_config=DB_CONFIG)
    user_prices = {}

    while True:
        sim.print_status()
        print("\n--- Main Menu ---")
        print("[P]urchase Inventory  [S]et Prices      [E]xpense")
        print("[A]dvance Time        [R]eset           [Q]uit")
        
        action = input("> ").upper()
        
        if action == 'P': handle_purchase(sim)
        elif action == 'S': user_prices = handle_set_prices(user_prices, sim)
        elif action == 'A':
            if not user_prices:
                print("\n*** WARNING: You haven't set any prices. Please set prices before advancing time. ***")
                continue
            try:
                days = int(input("How many days to simulate? "))
                sim.advance_time(days, user_prices)
            except ValueError:
                print("Invalid number.")
        elif action == 'E': handle_expense(sim)
        elif action == 'R':
            new_prices = handle_reset(sim)
            if new_prices is not None:
                user_prices = new_prices
        elif action == 'Q': break
        else: print("Invalid command.")

if __name__ == "__main__":
    main()

