import random
import datetime
import mysql.connector
import uuid
import math

# --- DATABASE CONFIGURATION ---
DB_CONFIG = {
    'user': 'root',
    'password': 'Hecther',
    'host': 'Yoga-Master',
    'port': 3306,
    'database': 'digital_harvest'
}

# --- BUSINESS SIMULATOR CLASS (Copied from api.py) ---
# This is the most up-to-date version of the simulation engine
class BusinessSimulator:
    def __init__(self, db_config):
        self.db_connection = mysql.connector.connect(**db_config)
        self.cursor = self.db_connection.cursor(dictionary=True)
        print("Successfully connected to MySQL database.")
        self._load_state()
        print(f"Business simulation loaded. Cash: ${self.cash:,.2f}, Date: {self.current_date.date()}.")

    def _load_state(self):
        self.cursor.execute("SELECT state_key, state_value FROM business_state")
        state = {row['state_key']: row['state_value'] for row in self.cursor.fetchall()}
        self.cash = float(state.get('cash_on_hand', 20000.00))
        self.current_date = datetime.datetime.strptime(state.get('current_date', '2025-01-01 09:00:00'), "%Y-%m-%d %H:%M:%S")
        self.simulation_start_date = datetime.datetime.strptime(state.get('start_date', self.current_date.strftime("%Y-%m-%d %H:%M:%S")), "%Y-%m-%d %H:%M:%S")

    def _save_state(self):
        query = "INSERT INTO business_state (state_key, state_value) VALUES (%s, %s) ON DUPLICATE KEY UPDATE state_value = VALUES(state_value)"
        self.cursor.execute(query, ('cash_on_hand', str(self.cash)))
        self.cursor.execute(query, ('current_date', self.current_date.strftime("%Y-%m-%d %H:%M:%S")))
        self.cursor.execute(query, ('start_date', self.simulation_start_date.strftime("%Y-%m-%d %H:%M:%S")))
        self.db_connection.commit()

    def get_current_stock(self, product_id):
        query = ("SELECT quantity_on_hand_after FROM inventory_ledger WHERE product_id = %s ORDER BY transaction_date DESC, entry_id DESC LIMIT 1")
        self.cursor.execute(query, (product_id,))
        result = self.cursor.fetchone()
        return result['quantity_on_hand_after'] if result else 0

    def get_avg_cost(self, product_id):
        query = ("SELECT unit_cost FROM inventory_ledger WHERE product_id = %s AND type = 'Purchase' ORDER BY transaction_date DESC LIMIT 10")
        self.cursor.execute(query, (product_id,))
        results = self.cursor.fetchall()
        if not results: return 0.0
        return float(sum(r['unit_cost'] for r in results) / len(results))

    def purchase_inventory(self, product_id, quantity, unit_cost):
        total_cost = quantity * unit_cost
        if self.cash < total_cost:
            print(f"ERROR: Not enough cash. Need ${total_cost:,.2f}, have ${self.cash:,.2f}")
            return

        transaction_uuid = str(uuid.uuid4())
        try:
            self.cash -= total_cost
            current_stock = self.get_current_stock(product_id)
            new_stock = current_stock + quantity
            
            inv_query = ("INSERT INTO inventory_ledger (transaction_uuid, transaction_date, product_id, type, description, "
                         "quantity_change, unit_cost, total_value, quantity_on_hand_after) "
                         "VALUES (%s, %s, %s, 'Purchase', 'Stock Purchase', %s, %s, %s, %s)")
            self.cursor.execute(inv_query, (transaction_uuid, self.current_date, product_id, quantity, unit_cost, -total_cost, new_stock))
            inv_entry_id = self.cursor.lastrowid

            fin_query = ("INSERT INTO financial_ledger (transaction_uuid, transaction_date, account, description, debit, credit) "
                         "VALUES (%s, %s, %s, %s, %s, %s)")
            self.cursor.execute(fin_query, (transaction_uuid, self.current_date, 'Inventory', f'Purchase inv_id:{inv_entry_id}', total_cost, 0.00))
            self.cursor.execute(fin_query, (transaction_uuid, self.current_date, 'Cash', f'Payment inv_id:{inv_entry_id}', 0.00, total_cost))

            self.db_connection.commit()
            self._save_state()
            print(f"SUCCESS: Purchased {quantity} units of product ID {product_id}.")
        except mysql.connector.Error as err:
            self.db_connection.rollback()
            self.cash += total_cost
            print(f"ERROR: Purchase failed due to a database error: {err}")

    def simulate_day_sales(self, user_prices):
        query = "SELECT p.*, c.name as category_name FROM products p JOIN categories c ON p.category_id = c.category_id"
        self.cursor.execute(query)
        products = self.cursor.fetchall()
        for product in products:
            stock = self.get_current_stock(product['product_id'])
            if stock <= 0: continue
            
            user_price_str = user_prices.get(str(product['product_id']))
            if not user_price_str: continue
            user_price = float(user_price_str)
            
            avg_cost = self.get_avg_cost(product['product_id'])
            potential_sales = self._calculate_potential_sales(product, user_price, avg_cost)
            units_sold = min(int(potential_sales), stock)
            
            if units_sold > 0:
                self._process_sale_transaction(product, units_sold, user_price, avg_cost)

    def _calculate_potential_sales(self, product, user_price, avg_cost):
        days_since_start = (self.current_date - self.simulation_start_date).days
        years_since_start = days_since_start / 365.25
        trend_factor = (1.10) ** years_since_start
        day_of_year = self.current_date.timetuple().tm_yday
        seasonal_factor = 1 + 0.4 * math.sin(2 * math.pi * (day_of_year - 80) / 365.25)
        weekday = self.current_date.weekday()
        weekly_factor = [0.9, 0.95, 1.0, 1.1, 1.4, 1.5, 1.2][weekday]
        competitor_price = avg_cost * 1.5 if avg_cost > 0 else user_price
        price_factor = 1
        if competitor_price > 0:
            price_factor = max(0, 1 - product['price_sensitivity'] * ((user_price - competitor_price) / competitor_price))
        base_demand = product['base_demand']
        adjusted_demand = base_demand * trend_factor * seasonal_factor * weekly_factor * price_factor
        return adjusted_demand * (1 + random.uniform(-0.1, 0.1))

    def _process_sale_transaction(self, product, units_sold, user_price, avg_cost):
        revenue = units_sold * user_price
        cost_of_goods_sold = units_sold * avg_cost
        transaction_fee = revenue * 0.03
        shipping_fee = 4.50
        transaction_uuid = str(uuid.uuid4())
        
        try:
            current_stock = self.get_current_stock(product['product_id'])
            new_stock = current_stock - units_sold
            self.cash += revenue
            self.cash -= (transaction_fee + shipping_fee)
            
            inv_query = ("INSERT INTO inventory_ledger (transaction_uuid, transaction_date, product_id, type, description, quantity_change, unit_price, total_value, quantity_on_hand_after) VALUES (%s, %s, %s, 'Sale', 'Customer Sale', %s, %s, %s, %s)")
            self.cursor.execute(inv_query, (transaction_uuid, self.current_date, product['product_id'], -units_sold, user_price, revenue, new_stock))
            inv_entry_id = self.cursor.lastrowid

            fin_query = ("INSERT INTO financial_ledger (transaction_uuid, transaction_date, account, description, debit, credit) VALUES (%s, %s, %s, %s, %s, %s)")
            self.cursor.execute(fin_query, (transaction_uuid, self.current_date, 'Cash', f'Sale inv_id:{inv_entry_id}', revenue, 0.00))
            self.cursor.execute(fin_query, (transaction_uuid, self.current_date, 'Sales Revenue', f'Sale of {product["name"]}', 0.00, revenue))
            self.cursor.execute(fin_query, (transaction_uuid, self.current_date, 'COGS', f'Cost for inv_id:{inv_entry_id}', cost_of_goods_sold, 0.00))
            self.cursor.execute(fin_query, (transaction_uuid, self.current_date, 'Inventory', f'Cost for inv_id:{inv_entry_id}', 0.00, cost_of_goods_sold))
            self.cursor.execute(fin_query, (transaction_uuid, self.current_date, 'Transaction Fees', f'Fee for inv_id:{inv_entry_id}', transaction_fee, 0.00))
            self.cursor.execute(fin_query, (transaction_uuid, self.current_date, 'Cash', f'Fee for inv_id:{inv_entry_id}', 0.00, transaction_fee))
            self.cursor.execute(fin_query, (transaction_uuid, self.current_date, 'Shipping Expense', f'Shipping for inv_id:{inv_entry_id}', shipping_fee, 0.00))
            self.cursor.execute(fin_query, (transaction_uuid, self.current_date, 'Cash', f'Shipping for inv_id:{inv_entry_id}', 0.00, shipping_fee))

            self.db_connection.commit()
            print(f"  - SOLD: {units_sold} of {product['name']}. Revenue: ${revenue:,.2f}")
        except mysql.connector.Error as err:
            self.db_connection.rollback()
            self.cash -= (revenue - transaction_fee - shipping_fee)
            print(f"  - FAILED SALE: Database error for {product['name']}. Transaction rolled back. Error: {err}")

    def _process_recurring_expenses(self):
        self.cursor.execute("SELECT * FROM recurring_expenses")
        expenses = self.cursor.fetchall()
        today = self.current_date.date()
        for exp in expenses:
            due = False
            last_processed = exp['last_processed_date']
            if exp['frequency'] == 'DAILY' and (last_processed is None or last_processed < today):
                due = True
            elif exp['frequency'] == 'MONTHLY' and self.current_date.day == 1 and (last_processed is None or last_processed.month < today.month or last_processed.year < today.year):
                due = True
            if due:
                print(f"  - PROCESSING RECURRING EXPENSE: {exp['description']}")
                if self.record_expense(exp['account'], exp['description'], exp['amount'], is_recurring=True):
                    self.cursor.execute("UPDATE recurring_expenses SET last_processed_date = %s WHERE expense_id = %s", (today, exp['expense_id']))
                    self.db_connection.commit()

    def record_expense(self, account, description, amount, is_recurring=False):
        if self.cash < amount:
            print(f"  - WARNING: Not enough cash for expense '{description}'. Skipping.")
            return False
        self.cash -= amount
        transaction_uuid = str(uuid.uuid4())
        fin_query = ("INSERT INTO financial_ledger (transaction_uuid, transaction_date, account, description, debit, credit) VALUES (%s, %s, %s, %s, %s, %s)")
        self.cursor.execute(fin_query, (transaction_uuid, self.current_date, account, description, amount, 0.00))
        self.cursor.execute(fin_query, (transaction_uuid, self.current_date, 'Cash', description, 0.00, amount))
        if not is_recurring:
             self.db_connection.commit()
             self._save_state()
        return True

    def advance_time(self, days, daily_prices):
        for i in range(days):
            day_str = self.current_date.strftime("%Y-%m-%d")
            print(f"\n--- Simulating Day: {day_str} ({i+1}/{days}) ---")
            self._process_recurring_expenses()
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

# --- MAIN INTERACTIVE SCRIPT ---

def get_product_list(sim):
    sim.cursor.execute("SELECT product_id, name, default_cost, default_price FROM products ORDER BY product_id")
    return sim.cursor.fetchall()

def handle_purchase(sim):
    products = get_product_list(sim)
    print("\n--- Purchase Inventory ---")
    for p in products:
        print(f"ID {p['product_id']}: {p['name']} (Suggest Cost: ${p['default_cost']})")
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
        current_price = f"(current: ${user_prices.get(str(p['product_id'])):,.2f})" if str(p['product_id']) in user_prices else f"(suggest: ${p['default_price']})"
        price_in = input(f"  - Set price for {p['name']} {current_price}: $")
        if price_in:
            try:
                user_prices[str(p['product_id'])] = float(price_in)
            except ValueError:
                print("Invalid price.")
    return user_prices

def handle_expense(sim):
    print("\n--- Record One-Off Expense ---")
    try:
        account = input("Enter expense account (e.g., Rent, Utilities, Marketing): ")
        description = input("Enter a brief description: ")
        amount = float(input("Enter the total amount: $"))
        sim.record_expense(account, description, amount)
    except ValueError:
        print("Invalid amount.")

def main():
    print("==============================================")
    print("      Welcome to Digital Harvest v2.0         ")
    print("==============================================")
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
        elif action == 'E': handle_expense(sim)
        elif action == 'A':
            if not user_prices:
                print("\n*** WARNING: You haven't set any prices. Please set them before advancing time. ***")
                continue
            try:
                days = int(input("How many days to simulate? "))
                sim.advance_time(days, user_prices)
            except ValueError:
                print("Invalid number.")
        elif action == 'R':
            print("Reset functionality must be run from the API/UI for now.")
        elif action == 'Q':
            break
        else:
            print("Invalid command.")

if __name__ == "__main__":
    main()