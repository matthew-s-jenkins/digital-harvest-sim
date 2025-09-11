from flask import Flask, jsonify, request
from flask_cors import CORS
import random
import datetime
import mysql.connector
import uuid
import math # Import the math library for seasonal calculations

# --- DATABASE CONFIGURATION ---
DB_CONFIG = {
    'user': 'root',
    'password': 'Hecther',
    'host': 'Yoga-Master',
    'port': 3306,
    'database': 'digital_harvest'
}

# --- BUSINESS SIMULATOR CLASS (The Engine) ---
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
        self.cursor.execute("SELECT state_key, state_value FROM business_state")
        state = {row['state_key']: row['state_value'] for row in self.cursor.fetchall()}
        self.cash = float(state.get('cash_on_hand', 20000.00))
        self.current_date = datetime.datetime.strptime(state.get('current_date', '2025-01-01 09:00:00'), "%Y-%m-%d %H:%M:%S")
        # Store the initial start date of the entire simulation for trend calculation
        self.simulation_start_date = datetime.datetime.strptime(state.get('start_date', self.current_date.strftime("%Y-%m-%d %H:%M:%S")), "%Y-%m-%d %H:%M:%S")

    def _save_state(self):
        query = "INSERT INTO business_state (state_key, state_value) VALUES (%s, %s) ON DUPLICATE KEY UPDATE state_value = VALUES(state_value)"
        self.cursor.execute(query, ('cash_on_hand', str(self.cash)))
        self.cursor.execute(query, ('current_date', self.current_date.strftime("%Y-%m-%d %H:%M:%S")))
        # Save the absolute start date so the trend is consistent
        self.cursor.execute(query, ('start_date', self.simulation_start_date.strftime("%Y-%m-%d %H:%M:%S")))
        self.db_connection.commit()

    def get_last_sale_price(self, product_id):
        query = ("SELECT unit_price FROM inventory_ledger WHERE product_id = %s AND type = 'Sale' ORDER BY transaction_date DESC, entry_id DESC LIMIT 1")
        self.cursor.execute(query, (product_id,))
        result = self.cursor.fetchone()
        return float(result['unit_price']) if result else None

    def get_last_purchase_price(self, product_id):
        query = ("SELECT unit_cost FROM inventory_ledger WHERE product_id = %s AND type = 'Purchase' ORDER BY transaction_date DESC, entry_id DESC LIMIT 1")
        self.cursor.execute(query, (product_id,))
        result = self.cursor.fetchone()
        return float(result['unit_cost']) if result else None

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
    
    def get_full_status(self):
        self.cursor.execute("SELECT SUM(credit) as total_rev FROM financial_ledger WHERE account = 'Sales Revenue'")
        revenue = self.cursor.fetchone()['total_rev'] or 0.0
        
        self.cursor.execute("SELECT product_id, name FROM products ORDER BY product_id")
        products = self.cursor.fetchall()
        inventory_details = []
        total_inv_value = 0
        for p in products:
            stock = self.get_current_stock(p['product_id'])
            avg_cost = self.get_avg_cost(p['product_id'])
            last_sale_price = self.get_last_sale_price(p['product_id'])
            last_purchase_price = self.get_last_purchase_price(p['product_id'])
            value = stock * avg_cost
            total_inv_value += value
            inventory_details.append({
                "product_id": p['product_id'], "name": p['name'], "stock": stock,
                "avg_cost": avg_cost, "value": value, "last_sale_price": last_sale_price,
                "last_purchase_price": last_purchase_price
            })
            
        return {
            "date": self.current_date.strftime('%Y-%m-%d'), "cash": self.cash,
            "lifetime_revenue": float(revenue), "inventory": inventory_details,
            "total_inventory_value": total_inv_value
        }

    def purchase_inventory(self, product_id, quantity, unit_cost):
        total_cost = quantity * unit_cost
        if self.cash < total_cost:
            return {"success": False, "message": f"Not enough cash."}
        
        transaction_uuid = str(uuid.uuid4())
        try:
            self.cash -= total_cost
            current_stock = self.get_current_stock(product_id)
            new_stock = current_stock + quantity
            
            inv_query = ("INSERT INTO inventory_ledger (transaction_uuid, transaction_date, product_id, type, description, "
                         "quantity_change, unit_cost, total_value, quantity_on_hand_after) "
                         "VALUES (%s, %s, %s, 'Purchase', 'Stock Purchase', %s, %s, %s, %s)")
            self.cursor.execute(inv_query, (transaction_uuid, self.current_date, product_id, quantity, unit_cost, -total_cost, new_stock))

            fin_query = ("INSERT INTO financial_ledger (transaction_uuid, transaction_date, account, description, debit, credit) "
                         "VALUES (%s, %s, %s, %s, %s, %s)")
            self.cursor.execute(fin_query, (transaction_uuid, self.current_date, 'Inventory', f'Purchase of product {product_id}', total_cost, 0.00))
            self.cursor.execute(fin_query, (transaction_uuid, self.current_date, 'Cash', f'Payment for product {product_id}', 0.00, total_cost))

            self.db_connection.commit()
            self._save_state()
            return {"success": True, "message": f"Purchased {quantity} units."}
        except mysql.connector.Error as err:
            self.db_connection.rollback()
            self.cash += total_cost
            return {"success": False, "message": f"Database error: {err}"}

    def simulate_day_sales(self, user_prices):
        query = "SELECT product_id, name, base_demand, price_sensitivity FROM products"
        self.cursor.execute(query)
        products = self.cursor.fetchall()
        for product in products:
            product_id = product['product_id']
            stock = self.get_current_stock(product_id)
            if stock <= 0: continue
            user_price = user_prices.get(str(product_id))
            if not user_price: continue
            
            avg_cost = self.get_avg_cost(product_id)
            potential_sales = self._calculate_potential_sales(product, user_price, avg_cost)
            units_sold = min(int(potential_sales), stock)
            
            if units_sold > 0:
                self._process_sale_transaction(product, units_sold, user_price, avg_cost)
    
    def _calculate_potential_sales(self, product, user_price, avg_cost):
        """
        Calculates potential sales based on a multi-factor model including
        trends, seasonality, weekly cycles, and price sensitivity.
        """
        # 1. Long-Term Trend (e.g., 10% annual growth)
        days_since_start = (self.current_date - self.simulation_start_date).days
        years_since_start = days_since_start / 365.25
        trend_factor = (1.10) ** years_since_start

        # 2. Seasonal Pattern (Sine wave peaking in late November)
        day_of_year = self.current_date.timetuple().tm_yday
        # Shift the sine wave so the peak is around day 330 (late November)
        seasonal_factor = 1 + 0.4 * math.sin(2 * math.pi * (day_of_year - (330 - 91.25)) / 365.25)

        # 3. Weekly Cycle (Weekends are busier)
        weekday = self.current_date.weekday() # Monday is 0, Sunday is 6
        if weekday in [4, 5]: # Friday, Saturday
            weekly_factor = 1.5
        elif weekday == 6: # Sunday
            weekly_factor = 1.2
        else: # Weekdays
            weekly_factor = 0.9
        
        # 4. Price Sensitivity
        competitor_price = avg_cost * 1.5 if avg_cost > 0 else user_price
        price_factor = 1
        if competitor_price > 0:
            price_factor = max(0, 1 - product['price_sensitivity'] * ((user_price - competitor_price) / competitor_price))

        # 5. Combine all factors with some randomness
        base_demand = product['base_demand']
        adjusted_demand = base_demand * trend_factor * seasonal_factor * weekly_factor * price_factor
        
        return adjusted_demand * (1 + random.uniform(-0.1, 0.1)) # Add a little noise

    def _process_sale_transaction(self, product, units_sold, user_price, avg_cost):
        revenue = units_sold * user_price
        cost_of_goods_sold = units_sold * avg_cost
        transaction_uuid = str(uuid.uuid4())
        
        try:
            current_stock = self.get_current_stock(product['product_id'])
            new_stock = current_stock - units_sold
            self.cash += revenue
            
            inv_query = ("INSERT INTO inventory_ledger (transaction_uuid, transaction_date, product_id, type, description, "
                         "quantity_change, unit_price, total_value, quantity_on_hand_after) "
                         "VALUES (%s, %s, %s, 'Sale', 'Customer Sale', %s, %s, %s, %s)")
            self.cursor.execute(inv_query, (transaction_uuid, self.current_date, product['product_id'], -units_sold, user_price, revenue, new_stock))

            fin_query = ("INSERT INTO financial_ledger (transaction_uuid, transaction_date, account, description, debit, credit) "
                         "VALUES (%s, %s, %s, %s, %s, %s)")
            self.cursor.execute(fin_query, (transaction_uuid, self.current_date, 'Cash', f'Sale of {product["name"]}', revenue, 0.00))
            self.cursor.execute(fin_query, (transaction_uuid, self.current_date, 'Sales Revenue', f'Sale of {product["name"]}', 0.00, revenue))
            self.cursor.execute(fin_query, (transaction_uuid, self.current_date, 'COGS', f'Cost for {product["name"]}', cost_of_goods_sold, 0.00))
            self.cursor.execute(fin_query, (transaction_uuid, self.current_date, 'Inventory', f'Cost for {product["name"]}', 0.00, cost_of_goods_sold))

            self.db_connection.commit()
            print(f"  - SOLD: {units_sold} of {product['name']}. Revenue: ${revenue:,.2f}")

        except mysql.connector.Error as err:
            self.db_connection.rollback()
            self.cash -= revenue
            print(f"  - FAILED SALE: Database error for {product['name']}. Transaction rolled back. Error: {err}")

    def advance_time(self, days, daily_prices):
        for _ in range(days):
            self.simulate_day_sales(daily_prices)
            self.current_date += datetime.timedelta(days=1)
        self._save_state()
        return {"success": True, "message": f"Advanced simulation by {days} days."}

# --- FLASK API SETUP & ENDPOINTS ---
app = Flask(__name__)
CORS(app)
sim = BusinessSimulator(db_config=DB_CONFIG)

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify(sim.get_full_status())

@app.route('/api/purchase', methods=['POST'])
def purchase():
    data = request.json
    result = sim.purchase_inventory(data.get('product_id'), data.get('quantity'), data.get('unit_cost'))
    return jsonify(result)

@app.route('/api/advance_time', methods=['POST'])
def advance():
    data = request.json
    result = sim.advance_time(data.get('days', 1), data.get('prices', {}))
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True, port=5000)

