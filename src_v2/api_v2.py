from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin
from engine_v2 import BusinessSimulator
from decimal import Decimal
import datetime
import json

# --- FLASK API SETUP & ENDPOINTS ---
app = Flask(__name__)
CORS(app, origins=["http://localhost:8080", "http://127.0.0.1:8080", "http://localhost:*", "http://127.0.0.1:*"])
sim = BusinessSimulator()

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()
        return super(CustomJSONEncoder, self).default(obj)

app.json_encoder = CustomJSONEncoder

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify(sim.get_status_summary())

@app.route('/api/vendors', methods=['GET'])
def get_vendors():
    return jsonify(sim.get_all_vendors())

@app.route('/api/vendors/<int:vendor_id>/products', methods=['GET'])
def get_vendor_products(vendor_id):
    return jsonify(sim.get_products_for_vendor(vendor_id))

@app.route('/api/sales_history', methods=['GET'])
def get_sales_history():
    return jsonify(sim.get_sales_history())
    
@app.route('/api/shipping_preview', methods=['POST'])
@cross_origin()
def get_shipping_preview():
    data = request.json
    vendor_id = data.get('vendor_id')
    subtotal = data.get('subtotal')
    if vendor_id is None or subtotal is None:
        return jsonify({"error": "Missing vendor_id or subtotal"}), 400
    
    shipping_cost = sim.calculate_shipping_preview(vendor_id, subtotal)
    return jsonify({"shipping_cost": shipping_cost})

@app.route('/api/order', methods=['POST'])
@cross_origin()
def place_order():
    data = request.json
    vendor_id = data.get('vendor_id')
    items = {int(k): v for k, v in data.get('items', {}).items()}
    
    if not vendor_id or not items:
        return jsonify({"success": False, "message": "Missing vendor_id or items."}), 400
        
    success = sim.place_order(vendor_id, items)
    if success:
        return jsonify({"success": True, "message": "Order placed successfully."})
    else:
        return jsonify({"success": False, "message": "Order failed. Check console for details (e.g., below MOV)."}), 400

@app.route('/api/advance_time', methods=['POST'])
@cross_origin()
def advance_time():
    data = request.json
    days = data.get('days', 1)
    result = sim.advance_time(days)
    status = sim.get_status_summary()
    return jsonify({'status': status, 'result': result})

@app.route('/api/dashboard_data', methods=['GET'])
def get_dashboard_data():
    inventory_by_category = sim.get_inventory_value_by_category()
    return jsonify({
        'inventory_by_category': inventory_by_category
    })

@app.route('/api/expenses', methods=['GET'])
def get_expenses():
    return jsonify(sim.get_all_expenses())

@app.route('/api/loans/offers', methods=['GET'])
def get_loan_offers():
    return jsonify(sim.get_loan_offers())

@app.route('/api/loans/accept', methods=['POST'])
@cross_origin()
def accept_loan():
    data = request.json
    offer_id = data.get('offer_id')
    if not offer_id:
        return jsonify({"success": False, "message": "Missing offer_id."}), 400
    
    success, message = sim.accept_loan(offer_id)
    if success:
        return jsonify({"success": True, "message": message})
    else:
        return jsonify({"success": False, "message": message}), 400

# --- MARKETING ENDPOINTS ---
@app.route('/api/marketing/offers', methods=['GET'])
def get_marketing_offers():
    return jsonify(sim.get_campaign_offers())

@app.route('/api/marketing/targets', methods=['GET'])
def get_marketing_targets():
    return jsonify(sim.get_campaign_targets())

@app.route('/api/marketing/active', methods=['GET'])
def get_active_campaigns():
    return jsonify(sim.get_active_campaigns())

@app.route('/api/marketing/launch', methods=['POST'])
@cross_origin()
def launch_campaign():
    data = request.json
    offer_id = data.get('offer_id')
    target_id = data.get('target_id') # Can be null

    if offer_id is None:
        return jsonify({"success": False, "message": "Missing offer_id"}), 400
    
    success, message = sim.launch_campaign(offer_id, target_id)
    if success:
        return jsonify({"success": True, "message": message})
    else:
        return jsonify({"success": False, "message": message}), 400

# --- NEW ENDPOINTS for Milestone 3 ---
@app.route('/api/inventory', methods=['GET'])
def get_inventory():
    return jsonify(sim.get_inventory())

@app.route('/api/products/price', methods=['POST'])
@cross_origin()
def set_product_price():
    data = request.json
    product_id = data.get('product_id')
    new_price = data.get('price')

    if product_id is None or new_price is None:
        return jsonify({"success": False, "message": "Missing product_id or price."}), 400

    success, message = sim.set_product_price(product_id, new_price)
    if success:
        return jsonify({"success": True, "message": message})
    else:
        return jsonify({"success": False, "message": message}), 400

@app.route('/api/unlocks', methods=['GET'])
def get_unlocks():
    return jsonify(sim.get_unlocks())

@app.route('/api/market_events/active', methods=['GET'])
def get_active_market_events():
    return jsonify(sim.get_active_events())

@app.route('/api/debug/last_simulation', methods=['GET'])
def get_last_simulation_log():
    # Return recent sales, arrivals, expenses from last advance_time call
    conn, cursor = sim._get_db_connection()
    
    # Get recent sales
    cursor.execute("""
        SELECT p.name, il.quantity_change, il.transaction_date 
        FROM inventory_ledger il 
        JOIN products p ON il.product_id = p.product_id 
        WHERE il.type = 'Sale' AND il.transaction_date >= %s 
        ORDER BY il.transaction_date DESC LIMIT 20
    """, (sim.current_date - datetime.timedelta(days=1),))
    recent_sales = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return jsonify({
        'recent_sales': recent_sales,
        'current_date': sim.current_date.isoformat()
    })

@app.route('/api/debug/sales_setup', methods=['GET'])
def debug_sales_setup():
    conn, cursor = sim._get_db_connection()
    
    # Check unlocked products
    cursor.execute("SELECT product_id, name, status FROM products WHERE status = 'UNLOCKED'")
    unlocked_products = cursor.fetchall()
    
    # Check player settings
    cursor.execute("SELECT * FROM player_product_settings")
    player_settings = cursor.fetchall()
    
    # Check current stock levels
    cursor.execute("""
        SELECT p.product_id, p.name, 
               COALESCE(stock.current_stock, 0) as current_stock
        FROM products p
        LEFT JOIN (
            SELECT product_id, quantity_on_hand_after as current_stock 
            FROM inventory_ledger il1 
            WHERE entry_id = (SELECT MAX(entry_id) FROM inventory_ledger il2 WHERE il1.product_id = il2.product_id)
        ) stock ON p.product_id = stock.product_id
        WHERE p.status = 'UNLOCKED'
    """)
    stock_levels = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return jsonify({
        'unlocked_products': unlocked_products,
        'player_settings': player_settings,
        'stock_levels': stock_levels
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
