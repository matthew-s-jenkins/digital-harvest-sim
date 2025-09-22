import mysql.connector
import datetime
import math
import random
from decimal import Decimal

# --- DATABASE CONFIGURATION ---
DB_CONFIG = {
    'user': 'root',
    'password': 'Hecther',
    'host': 'Yoga-Master',
    'port': 3306,
    'database': 'digital_harvest_v1'
}

class BusinessSimulator:
    """
    The headless core engine for the Digital Harvest v1 simulation.
    Manages game state and all core business logic.
    """
    def __init__(self):
        self.db_connection = mysql.connector.connect(**DB_CONFIG)
        self.cursor = self.db_connection.cursor(dictionary=True, buffered=True)
        self._load_state()
        print(f"✅ Business simulation engine initialized. Cash: ${self.cash:,.2f}, Date: {self.current_date.date()}")
    
    def _load_state(self):
        """Loads the current game state from the database."""
        self.cursor.execute("SELECT state_key, state_value FROM business_state")
        state = {row['state_key']: row['state_value'] for row in self.cursor.fetchall()}
        self.cash = Decimal(state.get('cash_on_hand', '20000.00'))
        self.current_date = datetime.datetime.strptime(state.get('current_date', '2025-01-01 09:00:00'), "%Y-%m-%d %H:%M:%S")
        self.simulation_start_date = datetime.datetime.strptime(state.get('start_date', self.current_date.strftime("%Y-%m-%d %H:%M:%S")), "%Y-%m-%d %H:%M:%S")

    def _save_state(self):
        """Saves the current game state to the database."""
        query = "INSERT INTO business_state (state_key, state_value) VALUES (%s, %s) ON DUPLICATE KEY UPDATE state_value = VALUES(state_value)"
        self.cursor.execute(query, ('cash_on_hand', str(self.cash)))
        self.cursor.execute(query, ('current_date', self.current_date.strftime("%Y-%m-%d %H:%M:%S")))
        self.db_connection.commit()

    def _get_current_stock(self, product_id):
        """Gets the current inventory quantity for a single product."""
        query = ("SELECT quantity_on_hand_after FROM inventory_ledger "
                 "WHERE product_id = %s ORDER BY transaction_date DESC, entry_id DESC LIMIT 1")
        self.cursor.execute(query, (product_id,))
        result = self.cursor.fetchone()
        return result['quantity_on_hand_after'] if result else 0

    def _get_unit_cost(self, vendor_id, product_id, quantity):
        """Finds the correct unit cost for a given quantity from a vendor, considering volume discounts."""
        query = ("SELECT vd.unit_cost FROM volume_discounts vd "
                 "JOIN vendor_products vp ON vd.vendor_product_id = vp.vendor_product_id "
                 "WHERE vp.vendor_id = %s AND vp.product_id = %s "
                 "AND vd.min_quantity <= %s AND (vd.max_quantity IS NULL OR vd.max_quantity >= %s)")
        self.cursor.execute(query, (vendor_id, product_id, quantity, quantity))
        result = self.cursor.fetchone()
        return result['unit_cost'] if result else None
        
    def _get_average_cost(self, product_id):
        """Calculates the average cost of a product based on the last 10 purchases."""
        query = ("SELECT unit_cost FROM inventory_ledger WHERE product_id = %s AND type = 'Purchase' "
                 "ORDER BY transaction_date DESC, entry_id DESC LIMIT 10")
        self.cursor.execute(query, (product_id,))
        results = self.cursor.fetchall()
        if not results:
            # Fallback to default cost if no purchase history
            cost_query = "SELECT vd.unit_cost FROM volume_discounts vd JOIN vendor_products vp ON vd.vendor_product_id = vp.vendor_product_id WHERE vp.product_id = %s ORDER BY vd.unit_cost ASC LIMIT 1"
            self.cursor.execute(cost_query, (product_id,))
            res = self.cursor.fetchone()
            return res['unit_cost'] if res else Decimal(0)
        
        total_cost = sum(r['unit_cost'] for r in results)
        return total_cost / len(results)

    def get_status_summary(self):
        """Queries the database and returns a dictionary with the current business status."""
        summary = {
            'cash': float(self.cash),
            'date': self.current_date,
            'inventory': [],
            'open_pos': []
        }
        inv_query = "SELECT p.product_id, p.name, s.current_selling_price FROM products p JOIN player_product_settings s ON p.product_id = s.product_id"
        self.cursor.execute(inv_query)
        products = self.cursor.fetchall()
        for prod in products:
            stock = self._get_current_stock(prod['product_id'])
            if stock > 0:
                summary['inventory'].append({
                    'id': prod['product_id'],
                    'name': prod['name'],
                    'stock': stock,
                    'price': float(prod['current_selling_price'])
                })
        po_query = "SELECT p.order_id, v.name as vendor_name, p.expected_arrival_date FROM purchase_orders p JOIN vendors v ON p.vendor_id = v.vendor_id WHERE p.status = 'PENDING'"
        self.cursor.execute(po_query)
        summary['open_pos'] = self.cursor.fetchall()
        return summary
        
    def get_all_vendors(self):
        """Returns a list of all vendors, ensuring money values are floats."""
        query = "SELECT vendor_id, name, location, minimum_order_value, base_lead_time_days, relationship_score FROM vendors"
        self.cursor.execute(query)
        vendors = self.cursor.fetchall()
        for vendor in vendors:
            vendor['minimum_order_value'] = float(vendor['minimum_order_value'])
        return vendors

    def get_products_for_vendor(self, vendor_id):
        """Returns a list of products sold by a specific vendor, ensuring money values are floats."""
        query = ("SELECT p.product_id, p.name, vd.unit_cost, vd.min_quantity "
                 "FROM products p "
                 "JOIN vendor_products vp ON p.product_id = vp.product_id "
                 "JOIN volume_discounts vd ON vp.vendor_product_id = vd.vendor_product_id "
                 "WHERE vp.vendor_id = %s "
                 "ORDER BY p.name, vd.min_quantity")
        self.cursor.execute(query, (vendor_id,))
        products = self.cursor.fetchall()
        for product in products:
            product['unit_cost'] = float(product['unit_cost'])
        return products

    def set_selling_price(self, product_id, new_price):
        """Updates the selling price for a player-owned product."""
        try:
            new_price = Decimal(new_price)
            if new_price < 0:
                print("ERROR: Price cannot be negative.")
                return False
            
            query = "UPDATE player_product_settings SET current_selling_price = %s WHERE product_id = %s"
            self.cursor.execute(query, (new_price, product_id))
            self.db_connection.commit()
            print(f"SUCCESS: Price for product {product_id} updated to ${new_price:,.2f}")
            return True
        except Exception as e:
            print(f"ERROR setting price: {e}")
            self.db_connection.rollback()
            return False

    def place_order(self, vendor_id, items):
        """
        Places a purchase order with a vendor.
        :param vendor_id: The ID of the vendor to order from.
        :param items: A dictionary of {product_id: quantity}.
        """
        try:
            self.cursor.execute("SELECT minimum_order_value, base_lead_time_days FROM vendors WHERE vendor_id = %s", (vendor_id,))
            vendor = self.cursor.fetchone()
            if not vendor:
                print("ERROR: Vendor not found.")
                return False

            total_value = Decimal('0.0')
            line_items = []
            for product_id, quantity in items.items():
                unit_cost = self._get_unit_cost(vendor_id, product_id, quantity)
                if unit_cost is None:
                    print(f"ERROR: Product ID {product_id} is not sold by this vendor or quantity is outside tiers.")
                    return False
                total_value += unit_cost * quantity
                line_items.append({'product_id': product_id, 'quantity': quantity, 'unit_cost': unit_cost})

            if total_value < vendor['minimum_order_value']:
                print(f"ERROR: Order total ${total_value:,.2f} is below vendor's minimum of ${vendor['minimum_order_value']:,.2f}")
                return False
            
            if self.cash < total_value:
                print(f"ERROR: Not enough cash. Order requires ${total_value:,.2f}, you have ${self.cash:,.2f}")
                return False
            
            self.cash -= total_value
            
            order_date = self.current_date
            expected_arrival = order_date + datetime.timedelta(days=vendor['base_lead_time_days'])
            po_query = ("INSERT INTO purchase_orders (vendor_id, order_date, expected_arrival_date, status) "
                        "VALUES (%s, %s, %s, 'PENDING')")
            self.cursor.execute(po_query, (vendor_id, order_date, expected_arrival))
            order_id = self.cursor.lastrowid

            poi_query = ("INSERT INTO purchase_order_items (order_id, product_id, quantity, unit_cost) "
                         "VALUES (%s, %s, %s, %s)")
            for item in line_items:
                self.cursor.execute(poi_query, (order_id, item['product_id'], item['quantity'], item['unit_cost']))

            fin_query = ("INSERT INTO financial_ledger (transaction_uuid, transaction_date, account, description, debit, credit) "
                         "VALUES (%s, %s, %s, %s, %s, %s)")
            uuid = str(datetime.datetime.now())
            self.cursor.execute(fin_query, (uuid, self.current_date, 'Inventory', f'Payment for PO #{order_id}', total_value, 0))
            self.cursor.execute(fin_query, (uuid, self.current_date, 'Cash', f'Payment for PO #{order_id}', 0, total_value))

            self._save_state()
            self.db_connection.commit()
            print(f"SUCCESS: Purchase Order #{order_id} placed for ${total_value:,.2f}")
            return True

        except Exception as e:
            print(f"ERROR placing order: {e}")
            self.db_connection.rollback()
            return False

    def advance_time(self, days_to_advance=1):
        """The main simulation loop. Advances time day by day."""
        print(f"\n advancing simulation by {days_to_advance} day(s)...")
        for i in range(days_to_advance):
            self._check_for_arrivals()
            self._process_sales()
            self._apply_recurring_expenses()
            self.current_date += datetime.timedelta(days=1)
            print(f"  -> Day advanced to {self.current_date.date()}")

        self._save_state()
        print("✅ Simulation advance complete.")

    def _check_for_arrivals(self):
        """Checks for any POs scheduled to arrive today and adds them to inventory."""
        query = "SELECT * FROM purchase_orders WHERE expected_arrival_date <= %s AND status = 'PENDING'"
        self.cursor.execute(query, (self.current_date,))
        arriving_orders = self.cursor.fetchall()

        for order in arriving_orders:
            print(f"  -> 📦 Shipment for PO #{order['order_id']} has arrived!")
            items_query = "SELECT * FROM purchase_order_items WHERE order_id = %s"
            self.cursor.execute(items_query, (order['order_id'],))
            items = self.cursor.fetchall()
            
            for item in items:
                current_stock = self._get_current_stock(item['product_id'])
                new_stock = current_stock + item['quantity']
                
                inv_query = ("INSERT INTO inventory_ledger (transaction_uuid, transaction_date, product_id, type, description, "
                             "quantity_change, unit_cost, total_value, quantity_on_hand_after) "
                             "VALUES (%s, %s, %s, 'Purchase', %s, %s, %s, %s, %s)")
                self.cursor.execute(inv_query, (
                    str(order['order_id']), self.current_date, item['product_id'], f"PO #{order['order_id']} arrived",
                    item['quantity'], item['unit_cost'], 0, new_stock
                ))
            
            update_po_query = "UPDATE purchase_orders SET status = 'DELIVERED', actual_arrival_date = %s WHERE order_id = %s"
            self.cursor.execute(update_po_query, (self.current_date, order['order_id']))
        if arriving_orders:
            self.db_connection.commit()

    def _process_sales(self):
        """Calculates and records sales for all products for the current day."""
        query = ("SELECT p.product_id, p.base_demand, p.price_sensitivity, s.current_selling_price, s.default_price "
                 "FROM products p JOIN player_product_settings s ON p.product_id = s.product_id")
        self.cursor.execute(query)
        products = self.cursor.fetchall()

        # --- UPDATED: Full dynamic sales calculation ---
        days_since_start = (self.current_date - self.simulation_start_date).days
        years_since_start = days_since_start / 365.25
        
        # 1. Long-term Growth Trend (e.g., 10% annual growth)
        trend_factor = Decimal(1.10) ** Decimal(years_since_start)
        
        # 2. Seasonality (peaks in spring/holidays, lows in summer)
        day_of_year = self.current_date.timetuple().tm_yday
        seasonal_factor = Decimal(1 + 0.3 * math.sin(2 * math.pi * (day_of_year - 80) / 365.25))
        
        # 3. Weekly Variance
        weekday = self.current_date.weekday() # Monday is 0, Sunday is 6
        weekly_factor = [Decimal('0.9'), Decimal('0.95'), Decimal('1.0'), Decimal('1.1'), Decimal('1.4'), Decimal('1.5'), Decimal('1.2')][weekday]

        for prod in products:
            stock = self._get_current_stock(prod['product_id'])
            if stock <= 0:
                continue

            # 4. Price Sensitivity
            price_diff_pct = (prod['current_selling_price'] - prod['default_price']) / prod['default_price']
            price_factor = Decimal(1 - (prod['price_sensitivity'] * float(price_diff_pct)))
            price_factor = max(0, price_factor)
            
            # Combine all factors
            daily_base_demand = Decimal(prod['base_demand'] / 7)
            adjusted_demand = daily_base_demand * trend_factor * seasonal_factor * weekly_factor * price_factor
            
            # Add random noise for realism
            calculated_demand = round(adjusted_demand * Decimal(random.uniform(0.9, 1.1)))
            
            units_sold = min(calculated_demand, stock)

            if units_sold > 0:
                # ... (rest of the sales processing logic is unchanged) ...
                revenue = units_sold * prod['current_selling_price']
                self.cash += revenue
                new_stock = stock - int(units_sold)
                uuid = f"sale-{self.current_date.date()}-{prod['product_id']}"
                avg_cost = self._get_average_cost(prod['product_id'])
                cost_of_goods_sold = units_sold * avg_cost
                
                inv_query = ("INSERT INTO inventory_ledger (transaction_uuid, transaction_date, product_id, type, description, "
                             "quantity_change, unit_price, total_value, quantity_on_hand_after) "
                             "VALUES (%s, %s, %s, 'Sale', 'Customer Sale', %s, %s, %s, %s)")
                self.cursor.execute(inv_query, (uuid, self.current_date, prod['product_id'], -units_sold, prod['current_selling_price'], revenue, new_stock))
                
                fin_query = ("INSERT INTO financial_ledger (transaction_uuid, transaction_date, account, description, debit, credit) "
                             "VALUES (%s, %s, %s, %s, %s, %s)")
                self.cursor.execute(fin_query, (uuid, self.current_date, 'Cash', f'Sale', revenue, 0))
                self.cursor.execute(fin_query, (uuid, self.current_date, 'Sales Revenue', f'Sale', 0, revenue))
                self.cursor.execute(fin_query, (uuid, self.current_date, 'COGS', f'Cost for sale', cost_of_goods_sold, 0))
                self.cursor.execute(fin_query, (uuid, self.current_date, 'Inventory', f'Cost for sale', 0, cost_of_goods_sold))

        self.db_connection.commit()

    def _apply_recurring_expenses(self):
        """Applies any due recurring expenses for the current day."""
        query = "SELECT * FROM recurring_expenses WHERE last_processed_date IS NULL OR last_processed_date < %s"
        self.cursor.execute(query, (self.current_date.date(),))
        due_expenses = self.cursor.fetchall()
        
        today = self.current_date.date()
        for exp in due_expenses:
            process = False
            last_processed = exp['last_processed_date']
            
            if exp['frequency'] == 'MONTHLY' and today.day == 1:
                if last_processed is None or last_processed.month < today.month or last_processed.year < today.year:
                    process = True
            # Add logic for 'WEEKLY' and 'DAILY' if needed
            
            if process:
                self.cash -= exp['amount']
                print(f"  -> 💸 Applied recurring expense: {exp['description']} (${exp['amount']})")
                
                fin_query = ("INSERT INTO financial_ledger (transaction_uuid, transaction_date, account, description, debit, credit) "
                             "VALUES (%s, %s, %s, %s, %s, %s)")
                uuid = f"exp-{self.current_date.date()}-{exp['expense_id']}"
                self.cursor.execute(fin_query, (uuid, self.current_date, exp['account'], exp['description'], exp['amount'], 0))
                self.cursor.execute(fin_query, (uuid, self.current_date, 'Cash', exp['description'], 0, exp['amount']))
                
                # Update last processed date
                update_query = "UPDATE recurring_expenses SET last_processed_date = %s WHERE expense_id = %s"
                self.cursor.execute(update_query, (today, exp['expense_id']))
                
        self.db_connection.commit()