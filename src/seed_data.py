"""
Digital Harvest v5 - Seed Data

This module populates the database with the 3 business types and their
associated products, categories, vendors, and starting data.

Business Types:
1. Clicky Clack Supply (Keyboards) - Medium volatility
2. Silicon Orchard (Tech/Crypto) - High volatility
3. Heritage Seeds (Vertical Farm) - Low volatility

Author: Matthew Jenkins
License: MIT
"""

import sqlite3
from pathlib import Path
from setup_sqlite import get_db_path


def seed_businesses(cursor):
    """Insert the 3 business types"""
    print("Seeding businesses...", end=" ")

    businesses = [
        ('keyboards', 'Clicky Clack Supply',
         'A mechanical keyboard switch retailer. Ride the trends of the enthusiast community - streamers, ASMR creators, and ergonomics advocates drive demand.',
         'MEDIUM', '⌨️', 15000.00),
        ('tech', 'Silicon Orchard',
         'A server farm and vintage tech parts dealer. High risk, high reward - crypto booms and tech news create wild price swings.',
         'HIGH', '🖥️', 25000.00),
        ('farm', 'Heritage Seeds',
         'A high-tech vertical farm growing rare produce. Steady and reliable - weather events and power outages are your main concerns.',
         'LOW', '🌱', 10000.00)
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO businesses (name, display_name, description, volatility, icon, starting_cash)
        VALUES (?, ?, ?, ?, ?, ?)
    """, businesses)
    print("OK")


def seed_keyboards_data(cursor, business_id):
    """Seed data for Clicky Clack Supply (Keyboards)"""
    print("  Seeding Clicky Clack Supply data...")

    # Categories
    categories = [
        (business_id, 'Linear Switches', '#ef4444'),    # Red
        (business_id, 'Tactile Switches', '#f59e0b'),   # Amber
        (business_id, 'Clicky Switches', '#3b82f6'),    # Blue
    ]
    cursor.executemany("""
        INSERT OR IGNORE INTO product_categories (business_id, name, color)
        VALUES (?, ?, ?)
    """, categories)

    # Get category IDs
    cursor.execute("SELECT category_id, name FROM product_categories WHERE business_id = ?", (business_id,))
    cat_map = {row[1]: row[0] for row in cursor.fetchall()}

    # Products - using attribute_1 for switch_type, attribute_2 for feel, attribute_3 for sound
    products = [
        # Linear Switches
        (business_id, cat_map['Linear Switches'], 'Gateron Red', 'GAT-RED', 320, 1.3, '0.65', 'UNLOCKED', None, 'LINEAR', 'LIGHT', 'QUIET'),
        (business_id, cat_map['Linear Switches'], 'Gateron Yellow', 'GAT-YEL', 280, 1.4, '0.65', 'UNLOCKED', None, 'LINEAR', 'MEDIUM', 'QUIET'),
        (business_id, cat_map['Linear Switches'], 'Cherry MX Black', 'CHR-BLK', 200, 1.1, '1.25', 'LOCKED', '25000', 'LINEAR', 'HEAVY', 'MODERATE'),

        # Tactile Switches
        (business_id, cat_map['Tactile Switches'], 'Gateron Brown', 'GAT-BRN', 350, 1.5, '0.65', 'UNLOCKED', None, 'TACTILE', 'LIGHT', 'MODERATE'),
        (business_id, cat_map['Tactile Switches'], 'Cherry MX Brown', 'CHR-BRN', 300, 1.2, '1.05', 'LOCKED', '15000', 'TACTILE', 'MEDIUM', 'MODERATE'),

        # Clicky Switches
        (business_id, cat_map['Clicky Switches'], 'Kailh Box White', 'KAI-WHT', 250, 1.6, '0.75', 'UNLOCKED', None, 'CLICKY', 'LIGHT', 'LOUD'),
        (business_id, cat_map['Clicky Switches'], 'Cherry MX Blue', 'CHR-BLU', 280, 1.1, '1.05', 'LOCKED', '10000', 'CLICKY', 'MEDIUM', 'LOUD'),
    ]
    cursor.executemany("""
        INSERT OR IGNORE INTO products (business_id, category_id, name, sku, base_demand, price_sensitivity, default_price, status, unlock_revenue, attribute_1, attribute_2, attribute_3)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, products)

    # Get product IDs
    cursor.execute("SELECT product_id, sku FROM products WHERE business_id = ?", (business_id,))
    prod_map = {row[1]: row[0] for row in cursor.fetchall()}

    # Vendors
    vendors = [
        # Distributors (Available)
        (business_id, 'US Switches LLC', 'DISTRIBUTOR', 'North America', 3, 0.95, '150.00', 'NET30', '25.00', 'AVAILABLE', None, None),
        (business_id, 'Switch World Express', 'DISTRIBUTOR', 'Asia', 20, 0.92, '250.00', 'NET30', '45.00', 'AVAILABLE', None, None),
        (business_id, 'KeebsForAll', 'DISTRIBUTOR', 'North America', 6, 0.97, '400.00', 'NET15', '30.00', 'AVAILABLE', None, None),
        (business_id, 'Budget Switches Co.', 'DISTRIBUTOR', 'Asia', 25, 0.90, '200.00', 'NET30', '50.00', 'AVAILABLE', None, None),
        (business_id, 'EU Keys', 'DISTRIBUTOR', 'Europe', 10, 0.94, '300.00', 'NET30', '35.00', 'AVAILABLE', None, None),

        # Manufacturers (Prospective)
        (business_id, 'Cherry Corp', 'MANUFACTURER', 'Europe', 12, 0.98, '25000.00', 'NET30', '100.00', 'PROSPECTIVE', 75, '25000'),
        (business_id, 'Gateron Manufacturing', 'MANUFACTURER', 'Asia', 30, 0.93, '10000.00', 'NET30', '150.00', 'PROSPECTIVE', 75, '10000'),
        (business_id, 'Kailh Direct', 'MANUFACTURER', 'Asia', 28, 0.94, '15000.00', 'NET30', '125.00', 'PROSPECTIVE', 75, '15000'),
    ]
    cursor.executemany("""
        INSERT OR IGNORE INTO vendors (business_id, name, vendor_type, location, base_lead_time_days, reliability_score, minimum_order_value, payment_terms, shipping_flat_fee, status, unlock_relationship, unlock_order_value)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, vendors)

    # Get vendor IDs
    cursor.execute("SELECT vendor_id, name FROM vendors WHERE business_id = ?", (business_id,))
    vendor_map = {row[1]: row[0] for row in cursor.fetchall()}

    # Vendor Products (which vendors carry which products at what cost)
    vendor_products = [
        # US Switches LLC - carries Gateron and Kailh
        (vendor_map['US Switches LLC'], prod_map['GAT-RED'], '0.45', 1),
        (vendor_map['US Switches LLC'], prod_map['GAT-YEL'], '0.45', 1),
        (vendor_map['US Switches LLC'], prod_map['GAT-BRN'], '0.45', 1),
        (vendor_map['US Switches LLC'], prod_map['KAI-WHT'], '0.52', 1),

        # Switch World Express - cheaper but slower
        (vendor_map['Switch World Express'], prod_map['GAT-RED'], '0.32', 100),
        (vendor_map['Switch World Express'], prod_map['GAT-YEL'], '0.32', 100),
        (vendor_map['Switch World Express'], prod_map['GAT-BRN'], '0.32', 100),
        (vendor_map['Switch World Express'], prod_map['KAI-WHT'], '0.40', 100),

        # KeebsForAll - premium distributor
        (vendor_map['KeebsForAll'], prod_map['GAT-RED'], '0.48', 1),
        (vendor_map['KeebsForAll'], prod_map['GAT-BRN'], '0.48', 1),
        (vendor_map['KeebsForAll'], prod_map['KAI-WHT'], '0.55', 1),

        # Budget Switches Co. - cheapest but slowest
        (vendor_map['Budget Switches Co.'], prod_map['GAT-RED'], '0.28', 500),
        (vendor_map['Budget Switches Co.'], prod_map['GAT-YEL'], '0.28', 500),
        (vendor_map['Budget Switches Co.'], prod_map['GAT-BRN'], '0.28', 500),

        # EU Keys
        (vendor_map['EU Keys'], prod_map['GAT-RED'], '0.42', 50),
        (vendor_map['EU Keys'], prod_map['GAT-BRN'], '0.42', 50),
        (vendor_map['EU Keys'], prod_map['KAI-WHT'], '0.50', 50),

        # Manufacturers - best prices, high minimums
        (vendor_map['Cherry Corp'], prod_map['CHR-BLK'], '0.65', 1000),
        (vendor_map['Cherry Corp'], prod_map['CHR-BRN'], '0.55', 1000),
        (vendor_map['Cherry Corp'], prod_map['CHR-BLU'], '0.55', 1000),

        (vendor_map['Gateron Manufacturing'], prod_map['GAT-RED'], '0.22', 2000),
        (vendor_map['Gateron Manufacturing'], prod_map['GAT-YEL'], '0.22', 2000),
        (vendor_map['Gateron Manufacturing'], prod_map['GAT-BRN'], '0.22', 2000),

        (vendor_map['Kailh Direct'], prod_map['KAI-WHT'], '0.35', 1500),
    ]
    cursor.executemany("""
        INSERT OR IGNORE INTO vendor_products (vendor_id, product_id, unit_cost, min_quantity)
        VALUES (?, ?, ?, ?)
    """, vendor_products)

    print("    - Categories: 3")
    print("    - Products: 7")
    print("    - Vendors: 8")


def seed_tech_data(cursor, business_id):
    """Seed data for Silicon Orchard (Tech/Crypto)"""
    print("  Seeding Silicon Orchard data...")

    # Categories
    categories = [
        (business_id, 'Graphics Cards', '#10b981'),     # Green
        (business_id, 'Server Components', '#6366f1'),  # Indigo
        (business_id, 'Vintage Parts', '#f59e0b'),      # Amber
    ]
    cursor.executemany("""
        INSERT OR IGNORE INTO product_categories (business_id, name, color)
        VALUES (?, ?, ?)
    """, categories)

    cursor.execute("SELECT category_id, name FROM product_categories WHERE business_id = ?", (business_id,))
    cat_map = {row[1]: row[0] for row in cursor.fetchall()}

    # Products - attribute_1: generation, attribute_2: tier, attribute_3: power_draw
    products = [
        # Graphics Cards
        (business_id, cat_map['Graphics Cards'], 'Mining GPU RX 580', 'GPU-RX580', 150, 2.0, '180.00', 'UNLOCKED', None, 'LAST_GEN', 'MID', 'HIGH'),
        (business_id, cat_map['Graphics Cards'], 'RTX 3070 Ti', 'GPU-3070TI', 80, 1.8, '450.00', 'UNLOCKED', None, 'CURRENT', 'HIGH', 'HIGH'),
        (business_id, cat_map['Graphics Cards'], 'RTX 4090', 'GPU-4090', 30, 1.5, '1600.00', 'LOCKED', '50000', 'CURRENT', 'FLAGSHIP', 'EXTREME'),

        # Server Components
        (business_id, cat_map['Server Components'], 'ECC RAM 32GB', 'RAM-ECC32', 200, 1.6, '95.00', 'UNLOCKED', None, 'DDR4', 'SERVER', 'LOW'),
        (business_id, cat_map['Server Components'], 'Xeon E5-2680', 'CPU-XEON', 120, 1.4, '150.00', 'UNLOCKED', None, 'LAST_GEN', 'SERVER', 'MEDIUM'),
        (business_id, cat_map['Server Components'], 'NVMe 2TB Enterprise', 'SSD-ENT2T', 100, 1.7, '280.00', 'LOCKED', '25000', 'CURRENT', 'ENTERPRISE', 'LOW'),

        # Vintage Parts
        (business_id, cat_map['Vintage Parts'], '3dfx Voodoo 2', 'VIN-V2', 20, 1.2, '250.00', 'UNLOCKED', None, 'VINTAGE', 'COLLECTOR', 'LOW'),
        (business_id, cat_map['Vintage Parts'], 'Sound Blaster AWE64', 'VIN-SB64', 35, 1.3, '80.00', 'UNLOCKED', None, 'VINTAGE', 'COLLECTOR', 'LOW'),
    ]
    cursor.executemany("""
        INSERT OR IGNORE INTO products (business_id, category_id, name, sku, base_demand, price_sensitivity, default_price, status, unlock_revenue, attribute_1, attribute_2, attribute_3)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, products)

    cursor.execute("SELECT product_id, sku FROM products WHERE business_id = ?", (business_id,))
    prod_map = {row[1]: row[0] for row in cursor.fetchall()}

    # Vendors
    vendors = [
        (business_id, 'TechWholesale Direct', 'DISTRIBUTOR', 'North America', 4, 0.94, '500.00', 'NET30', '50.00', 'AVAILABLE', None, None),
        (business_id, 'Shenzhen Components', 'DISTRIBUTOR', 'Asia', 18, 0.88, '1000.00', 'NET30', '120.00', 'AVAILABLE', None, None),
        (business_id, 'RetroTech Traders', 'BOUTIQUE', 'North America', 7, 0.96, '200.00', 'NET15', '25.00', 'AVAILABLE', None, None),
        (business_id, 'GPU Mining Surplus', 'DISTRIBUTOR', 'North America', 5, 0.92, '300.00', 'NET30', '40.00', 'AVAILABLE', None, None),

        # Manufacturers
        (business_id, 'NVIDIA Partner Direct', 'MANUFACTURER', 'Asia', 25, 0.97, '50000.00', 'NET30', '500.00', 'PROSPECTIVE', 75, '50000'),
        (business_id, 'Intel Server Division', 'MANUFACTURER', 'North America', 14, 0.98, '30000.00', 'NET30', '200.00', 'PROSPECTIVE', 75, '30000'),
    ]
    cursor.executemany("""
        INSERT OR IGNORE INTO vendors (business_id, name, vendor_type, location, base_lead_time_days, reliability_score, minimum_order_value, payment_terms, shipping_flat_fee, status, unlock_relationship, unlock_order_value)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, vendors)

    cursor.execute("SELECT vendor_id, name FROM vendors WHERE business_id = ?", (business_id,))
    vendor_map = {row[1]: row[0] for row in cursor.fetchall()}

    vendor_products = [
        # TechWholesale Direct
        (vendor_map['TechWholesale Direct'], prod_map['GPU-RX580'], '120.00', 5),
        (vendor_map['TechWholesale Direct'], prod_map['GPU-3070TI'], '380.00', 2),
        (vendor_map['TechWholesale Direct'], prod_map['RAM-ECC32'], '70.00', 10),
        (vendor_map['TechWholesale Direct'], prod_map['CPU-XEON'], '100.00', 5),

        # Shenzhen Components - cheaper but risky
        (vendor_map['Shenzhen Components'], prod_map['GPU-RX580'], '85.00', 20),
        (vendor_map['Shenzhen Components'], prod_map['GPU-3070TI'], '320.00', 10),
        (vendor_map['Shenzhen Components'], prod_map['RAM-ECC32'], '55.00', 50),
        (vendor_map['Shenzhen Components'], prod_map['CPU-XEON'], '75.00', 20),

        # RetroTech Traders - vintage specialist
        (vendor_map['RetroTech Traders'], prod_map['VIN-V2'], '150.00', 1),
        (vendor_map['RetroTech Traders'], prod_map['VIN-SB64'], '45.00', 1),

        # GPU Mining Surplus
        (vendor_map['GPU Mining Surplus'], prod_map['GPU-RX580'], '95.00', 10),

        # Manufacturers
        (vendor_map['NVIDIA Partner Direct'], prod_map['GPU-3070TI'], '280.00', 50),
        (vendor_map['NVIDIA Partner Direct'], prod_map['GPU-4090'], '1100.00', 20),

        (vendor_map['Intel Server Division'], prod_map['RAM-ECC32'], '50.00', 100),
        (vendor_map['Intel Server Division'], prod_map['CPU-XEON'], '65.00', 50),
        (vendor_map['Intel Server Division'], prod_map['SSD-ENT2T'], '180.00', 25),
    ]
    cursor.executemany("""
        INSERT OR IGNORE INTO vendor_products (vendor_id, product_id, unit_cost, min_quantity)
        VALUES (?, ?, ?, ?)
    """, vendor_products)

    print("    - Categories: 3")
    print("    - Products: 8")
    print("    - Vendors: 6")


def seed_farm_data(cursor, business_id):
    """Seed data for Heritage Seeds (Vertical Farm)"""
    print("  Seeding Heritage Seeds data...")

    # Categories
    categories = [
        (business_id, 'Leafy Greens', '#22c55e'),      # Green
        (business_id, 'Herbs', '#a855f7'),              # Purple
        (business_id, 'Microgreens', '#06b6d4'),        # Cyan
    ]
    cursor.executemany("""
        INSERT OR IGNORE INTO product_categories (business_id, name, color)
        VALUES (?, ?, ?)
    """, categories)

    cursor.execute("SELECT category_id, name FROM product_categories WHERE business_id = ?", (business_id,))
    cat_map = {row[1]: row[0] for row in cursor.fetchall()}

    # Products - attribute_1: grow_time, attribute_2: shelf_life, attribute_3: light_needs
    products = [
        # Leafy Greens
        (business_id, cat_map['Leafy Greens'], 'Butter Lettuce', 'LG-BUTTER', 400, 1.2, '3.50', 'UNLOCKED', None, '30_DAYS', '7_DAYS', 'MEDIUM'),
        (business_id, cat_map['Leafy Greens'], 'Red Romaine', 'LG-REDROM', 350, 1.3, '4.00', 'UNLOCKED', None, '35_DAYS', '10_DAYS', 'MEDIUM'),
        (business_id, cat_map['Leafy Greens'], 'Tokyo Bekana', 'LG-TOKYO', 200, 1.4, '5.50', 'LOCKED', '20000', '25_DAYS', '5_DAYS', 'LOW'),

        # Herbs
        (business_id, cat_map['Herbs'], 'Sweet Basil', 'HB-BASIL', 500, 1.1, '2.50', 'UNLOCKED', None, '21_DAYS', '5_DAYS', 'HIGH'),
        (business_id, cat_map['Herbs'], 'Cilantro', 'HB-CILANT', 450, 1.2, '2.75', 'UNLOCKED', None, '21_DAYS', '7_DAYS', 'MEDIUM'),
        (business_id, cat_map['Herbs'], 'Thai Basil', 'HB-THAI', 250, 1.3, '4.00', 'LOCKED', '15000', '28_DAYS', '5_DAYS', 'HIGH'),

        # Microgreens
        (business_id, cat_map['Microgreens'], 'Sunflower Shoots', 'MG-SUNFL', 300, 1.4, '6.00', 'UNLOCKED', None, '10_DAYS', '5_DAYS', 'MEDIUM'),
        (business_id, cat_map['Microgreens'], 'Pea Shoots', 'MG-PEA', 350, 1.3, '5.50', 'UNLOCKED', None, '12_DAYS', '7_DAYS', 'LOW'),
        (business_id, cat_map['Microgreens'], 'Wasabi Microgreens', 'MG-WASABI', 100, 1.5, '12.00', 'LOCKED', '30000', '14_DAYS', '3_DAYS', 'HIGH'),
    ]
    cursor.executemany("""
        INSERT OR IGNORE INTO products (business_id, category_id, name, sku, base_demand, price_sensitivity, default_price, status, unlock_revenue, attribute_1, attribute_2, attribute_3)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, products)

    cursor.execute("SELECT product_id, sku FROM products WHERE business_id = ?", (business_id,))
    prod_map = {row[1]: row[0] for row in cursor.fetchall()}

    # Vendors (seed suppliers)
    vendors = [
        (business_id, 'Green Thumb Seeds', 'DISTRIBUTOR', 'North America', 5, 0.96, '100.00', 'NET30', '15.00', 'AVAILABLE', None, None),
        (business_id, 'Hydro Supply Co', 'DISTRIBUTOR', 'North America', 3, 0.98, '150.00', 'NET15', '20.00', 'AVAILABLE', None, None),
        (business_id, 'Asian Seed Imports', 'DISTRIBUTOR', 'Asia', 14, 0.90, '200.00', 'NET30', '40.00', 'AVAILABLE', None, None),
        (business_id, 'Organic Farms Direct', 'BOUTIQUE', 'North America', 7, 0.97, '75.00', 'NET15', '12.00', 'AVAILABLE', None, None),

        # Manufacturers
        (business_id, 'Johnny Seeds Commercial', 'MANUFACTURER', 'North America', 10, 0.99, '5000.00', 'NET30', '50.00', 'PROSPECTIVE', 75, '5000'),
        (business_id, 'Rijk Zwaan Wholesale', 'MANUFACTURER', 'Europe', 21, 0.97, '8000.00', 'NET30', '100.00', 'PROSPECTIVE', 75, '8000'),
    ]
    cursor.executemany("""
        INSERT OR IGNORE INTO vendors (business_id, name, vendor_type, location, base_lead_time_days, reliability_score, minimum_order_value, payment_terms, shipping_flat_fee, status, unlock_relationship, unlock_order_value)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, vendors)

    cursor.execute("SELECT vendor_id, name FROM vendors WHERE business_id = ?", (business_id,))
    vendor_map = {row[1]: row[0] for row in cursor.fetchall()}

    # For farm, unit_cost represents cost per "grow cycle" worth of seeds
    vendor_products = [
        # Green Thumb Seeds
        (vendor_map['Green Thumb Seeds'], prod_map['LG-BUTTER'], '0.80', 50),
        (vendor_map['Green Thumb Seeds'], prod_map['LG-REDROM'], '0.90', 50),
        (vendor_map['Green Thumb Seeds'], prod_map['HB-BASIL'], '0.50', 100),
        (vendor_map['Green Thumb Seeds'], prod_map['HB-CILANT'], '0.55', 100),
        (vendor_map['Green Thumb Seeds'], prod_map['MG-SUNFL'], '1.20', 50),
        (vendor_map['Green Thumb Seeds'], prod_map['MG-PEA'], '1.00', 50),

        # Hydro Supply Co - faster, slightly more expensive
        (vendor_map['Hydro Supply Co'], prod_map['LG-BUTTER'], '0.95', 25),
        (vendor_map['Hydro Supply Co'], prod_map['HB-BASIL'], '0.60', 50),
        (vendor_map['Hydro Supply Co'], prod_map['MG-SUNFL'], '1.40', 25),
        (vendor_map['Hydro Supply Co'], prod_map['MG-PEA'], '1.20', 25),

        # Asian Seed Imports - specialty items
        (vendor_map['Asian Seed Imports'], prod_map['LG-TOKYO'], '1.50', 100),
        (vendor_map['Asian Seed Imports'], prod_map['HB-THAI'], '1.00', 100),
        (vendor_map['Asian Seed Imports'], prod_map['MG-WASABI'], '3.50', 50),

        # Organic Farms Direct - premium organic
        (vendor_map['Organic Farms Direct'], prod_map['LG-BUTTER'], '1.10', 20),
        (vendor_map['Organic Farms Direct'], prod_map['HB-BASIL'], '0.70', 30),
        (vendor_map['Organic Farms Direct'], prod_map['HB-CILANT'], '0.75', 30),

        # Manufacturers - bulk pricing
        (vendor_map['Johnny Seeds Commercial'], prod_map['LG-BUTTER'], '0.45', 500),
        (vendor_map['Johnny Seeds Commercial'], prod_map['LG-REDROM'], '0.50', 500),
        (vendor_map['Johnny Seeds Commercial'], prod_map['HB-BASIL'], '0.30', 1000),
        (vendor_map['Johnny Seeds Commercial'], prod_map['HB-CILANT'], '0.32', 1000),
        (vendor_map['Johnny Seeds Commercial'], prod_map['MG-SUNFL'], '0.70', 500),
        (vendor_map['Johnny Seeds Commercial'], prod_map['MG-PEA'], '0.60', 500),

        (vendor_map['Rijk Zwaan Wholesale'], prod_map['LG-TOKYO'], '0.90', 500),
        (vendor_map['Rijk Zwaan Wholesale'], prod_map['HB-THAI'], '0.60', 500),
        (vendor_map['Rijk Zwaan Wholesale'], prod_map['MG-WASABI'], '2.00', 200),
    ]
    cursor.executemany("""
        INSERT OR IGNORE INTO vendor_products (vendor_id, product_id, unit_cost, min_quantity)
        VALUES (?, ?, ?, ?)
    """, vendor_products)

    print("    - Categories: 3")
    print("    - Products: 9")
    print("    - Vendors: 6")


def seed_recurring_expenses():
    """Seed default recurring expenses (applied per user when they start a game)"""
    # These will be added when a user starts a new game
    return [
        ('Warehouse Rent', 'Operating Expenses', '1200.00', 'MONTHLY'),
        ('Warehouse Utilities', 'Operating Expenses', '250.00', 'MONTHLY'),
        ('Inventory Software', 'Software Expenses', '75.00', 'MONTHLY'),
    ]


def seed_all():
    """Main function to seed all data"""
    db_path = get_db_path()

    if not db_path.exists():
        print(f"[ERROR] Database not found at {db_path}")
        print("Run setup_sqlite.py first to create the database.")
        return False

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    print("=" * 60)
    print("Digital Harvest v5 - Seeding Database")
    print("=" * 60)
    print()

    try:
        # Seed businesses
        seed_businesses(cursor)

        # Get business IDs
        cursor.execute("SELECT business_id, name FROM businesses")
        business_map = {row[1]: row[0] for row in cursor.fetchall()}

        print()

        # Seed each business's data
        seed_keyboards_data(cursor, business_map['keyboards'])
        print()
        seed_tech_data(cursor, business_map['tech'])
        print()
        seed_farm_data(cursor, business_map['farm'])

        conn.commit()

        print()
        print("=" * 60)
        print("[OK] Seed data inserted successfully!")
        print("=" * 60)

        # Summary
        cursor.execute("SELECT COUNT(*) FROM businesses")
        print(f"  Businesses: {cursor.fetchone()[0]}")
        cursor.execute("SELECT COUNT(*) FROM product_categories")
        print(f"  Product Categories: {cursor.fetchone()[0]}")
        cursor.execute("SELECT COUNT(*) FROM products")
        print(f"  Products: {cursor.fetchone()[0]}")
        cursor.execute("SELECT COUNT(*) FROM vendors")
        print(f"  Vendors: {cursor.fetchone()[0]}")
        cursor.execute("SELECT COUNT(*) FROM vendor_products")
        print(f"  Vendor-Product Links: {cursor.fetchone()[0]}")

        return True

    except sqlite3.Error as err:
        print(f"\n[ERROR] Error seeding database: {err}")
        conn.rollback()
        return False

    finally:
        conn.close()


if __name__ == "__main__":
    seed_all()
