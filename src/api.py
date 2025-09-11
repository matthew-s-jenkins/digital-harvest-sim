from flask import Flask, jsonify, request
from flask_cors import CORS
import random
import datetime
import mysql.connector

# --- DATABASE CONFIGURATION ---
DB_CONFIG = {
    'user': 'root',
    'password': 'Hecther', # IMPORTANT: Use your actual password
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

    def _save_state(self):
        query = "INSERT INTO business_state (state_key, state_value) VALUES (%s, %s) ON DUPLICATE KEY UPDATE state_value = VALUES(state_value)"
        self.cursor.execute(query, ('cash_on_hand', str(self.cash)))
        self.cursor.execute(query, ('current_date', self.current_date.strftime("%Y-%m-%d %H:%M:%S")))
        self.db_connection.commit()

    def get_last_sale_price(self, product_id):
        query = ("SELECT unit_price FROM inventory_ledger "
                 "WHERE product_id = %s AND type = 'Sale' "
                 "ORDER BY transaction_date DESC, entry_id DESC LIMIT 1")
        self.cursor.execute(query, (product_id,))
        result = self.cursor.fetchone()
        return float(result['unit_price']) if result else None

    def get_last_purchase_price(self, product_id):
        """Gets the most recent purchase price for a product."""
        query = ("SELECT unit_cost FROM inventory_ledger "
                 "WHERE product_id = %s AND type = 'Purchase' "
                 "ORDER BY transaction_date DESC, entry_id DESC LIMIT 1")
        self.cursor.execute(query, (product_id,))
        result = self.cursor.fetchone()
        return float(result['unit_cost']) if result else None
    
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
                "product_id": p['product_id'],
                "name": p['name'],
                "stock": stock,
                "avg_cost": avg_cost,
                "value": value,
                "last_sale_price": last_sale_price,
                "last_purchase_price": last_purchase_price
            })
            
        return {
            "date": self.current_date.strftime('%Y-%m-%d'),
            "cash": self.cash,
            "lifetime_revenue": float(revenue),
            "inventory": inventory_details,
            "total_inventory_value": total_inv_value
        }

    def get_current_stock(self, product_id):
        query = ("SELECT quantity_on_hand_after FROM inventory_ledger "
                 "WHERE product_id = %s ORDER BY transaction_date DESC, entry_id DESC LIMIT 1")
        self.cursor.execute(query, (product_id,))
        result = self.cursor.fetchone()
        return result['quantity_on_hand_after'] if result else 0

    def get_avg_cost(self, product_id):
        query = ("SELECT unit_cost FROM inventory_ledger "
                 "WHERE product_id = %s AND type = 'Purchase' ORDER BY transaction_date DESC LIMIT 10")
        self.cursor.execute(query, (product_id,))
        results = self.cursor.fetchall()
        if not results: return 0.0
        return float(sum(r['unit_cost'] for r in results) / len(results))

    def purchase_inventory(self, product_id, quantity, unit_cost):
        total_cost = quantity * unit_cost
        if self.cash < total_cost:
            return {"success": False, "message": f"Not enough cash. Need ${total_cost:,.2f}, have ${self.cash:,.2f}"}

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
        return {"success": True, "message": f"Purchased {quantity} units."}

    def advance_time(self, days, daily_prices):
        for _ in range(days):
            self.simulate_day_sales(daily_prices)
            self.current_date += datetime.timedelta(days=1)
        self._save_state()
        return {"success": True, "message": f"Advanced simulation by {days} days."}

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

# --- FLASK API SETUP ---
app = Flask(__name__)
CORS(app)
sim = BusinessSimulator(db_config=DB_CONFIG)

# --- API ENDPOINTS ---
@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify(sim.get_full_status())

@app.route('/api/purchase', methods=['POST'])
def purchase():
    data = request.json
    result = sim.purchase_inventory(
        data.get('product_id'), data.get('quantity'), data.get('unit_cost')
    )
    return jsonify(result)

@app.route('/api/advance_time', methods=['POST'])
def advance():
    data = request.json
    result = sim.advance_time(data.get('days', 1), data.get('prices', {}))
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True, port=5000)