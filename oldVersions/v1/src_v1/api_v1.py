from flask import Flask, jsonify, request
from flask_cors import CORS
from engine_v1 import BusinessSimulator
from decimal import Decimal
import json

# --- FLASK API SETUP & ENDPOINTS ---
app = Flask(__name__)
CORS(app) # Allows the React UI to talk to this API
sim = BusinessSimulator()

# Custom JSON encoder to handle Decimal types
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
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

@app.route('/api/order', methods=['POST'])
def place_order():
    data = request.json
    vendor_id = data.get('vendor_id')
    # Convert product_id keys from string to int
    items = {int(k): v for k, v in data.get('items', {}).items()}
    
    if not vendor_id or not items:
        return jsonify({"success": False, "message": "Missing vendor_id or items."}), 400
        
    success = sim.place_order(vendor_id, items)
    if success:
        return jsonify({"success": True, "message": "Order placed successfully."})
    else:
        # The engine prints detailed errors, so a generic message is fine here
        return jsonify({"success": False, "message": "Order failed. Check console for details."}), 400

@app.route('/api/advance_time', methods=['POST'])
def advance_time():
    data = request.json
    days = data.get('days', 1)
    sim.advance_time(days)
    return jsonify(sim.get_status_summary())

if __name__ == '__main__':
    app.run(debug=True, port=5000)