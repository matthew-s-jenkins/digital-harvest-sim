"""
Digital Harvest v5 - SQLite Database Setup & Initialization

This module creates and initializes the Digital Harvest SQLite database schema.
Built on the Perfect Books foundation with added inventory and sales simulation.

Database Schema Overview:
------------------------
FINANCIAL (from Perfect Books):
- users: User authentication and account management
- accounts: Financial accounts (checking, savings, credit cards, loans, etc.)
- financial_ledger: Double-entry accounting ledger (immutable audit trail)
- expense_categories: User-defined expense categorization with colors
- recurring_expenses: Automated monthly bill payments with categories
- loans: Debt tracking with payment schedules
- schema_version: Track applied database migrations

GAME STATE:
- game_state: Current game date, selected business type
- businesses: Available business types (Keyboards, Tech, Farm)

INVENTORY & PRODUCTS:
- product_categories: Product groupings (e.g., Linear Switches, Tactile Switches)
- products: SKU catalog with demand parameters
- inventory_layers: FIFO cost tracking for inventory
- player_product_settings: Player's pricing decisions

SUPPLY CHAIN:
- vendors: Supplier catalog with lead times and terms
- vendor_products: Which vendors carry which products
- volume_discounts: Tiered pricing based on order quantity
- purchase_orders: Inbound orders from vendors
- purchase_order_items: Line items in purchase orders

MARKETING & EVENTS:
- marketing_campaigns: Player-initiated demand boosts
- market_events: Random market demand shifts

Key Design Features:
- Foreign key constraints for referential integrity
- Indexes on frequently queried columns for performance
- Cascade deletes for user data (complete user removal)
- TEXT storage for monetary values (preserves exact precision)
- FIFO inventory costing via inventory_layers
- Double-entry accounting for all financial transactions

Author: Matthew Jenkins
License: MIT
"""

import sqlite3
from pathlib import Path
from datetime import datetime


def get_db_path():
    """Return the path to the SQLite database file"""
    return Path(__file__).parent / "data" / "digitalharvest.db"


def create_database():
    """
    Create a fresh Digital Harvest SQLite database with all tables.

    [WARNING]  WARNING: If the database already exists, this will NOT drop it.
    Use reset_database() if you want to start fresh.
    """
    db_path = get_db_path()

    # Create data directory if it doesn't exist
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Connect to SQLite database (creates file if doesn't exist)
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Enable foreign key constraints (CRITICAL for data integrity)
    cursor.execute("PRAGMA foreign_keys = ON;")

    print(f"--- Creating Digital Harvest v5 Database ---")
    print(f"Location: {db_path}")
    print()

    try:
        # =================================================================
        # TABLE 1: users - User authentication
        # =================================================================
        print("Creating table 'users'...", end=" ")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("OK")

        # =================================================================
        # TABLE 2: accounts - Financial accounts
        # =================================================================
        print("Creating table 'accounts'...", end=" ")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                account_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                type TEXT CHECK(type IN ('CHECKING', 'SAVINGS', 'CREDIT_CARD', 'CASH', 'LOAN', 'FIXED_ASSET', 'EQUITY')) NOT NULL,
                balance TEXT NOT NULL DEFAULT '0.00',
                interest_rate REAL DEFAULT NULL,
                last_interest_date TEXT DEFAULT NULL,
                credit_limit TEXT DEFAULT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_accounts_user_id ON accounts(user_id);")
        print("OK")

        # =================================================================
        # TABLE 3: parent_categories - Category groups for organization
        # =================================================================
        print("Creating table 'parent_categories'...", end=" ")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS parent_categories (
                parent_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                type TEXT CHECK(type IN ('income', 'expense', 'both')) NOT NULL DEFAULT 'expense',
                display_order INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("OK")

        # =================================================================
        # TABLE 4: expense_categories - User-defined categories
        # =================================================================
        print("Creating table 'expense_categories'...", end=" ")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS expense_categories (
                category_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                color TEXT DEFAULT '#6366f1',
                parent_id INTEGER DEFAULT NULL,
                is_default INTEGER DEFAULT 0,
                is_monthly INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (parent_id) REFERENCES parent_categories(parent_id) ON DELETE SET NULL,
                UNIQUE(user_id, name)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_categories_user_id ON expense_categories(user_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_categories_parent_id ON expense_categories(parent_id);")
        print("OK")

        # =================================================================
        # TABLE 5: financial_ledger - Double-entry accounting ledger
        # =================================================================
        print("Creating table 'financial_ledger'...", end=" ")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS financial_ledger (
                entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                transaction_uuid TEXT NOT NULL,
                transaction_date TEXT NOT NULL,
                account TEXT NOT NULL,
                description TEXT,
                debit TEXT DEFAULT '0.00',
                credit TEXT DEFAULT '0.00',
                category_id INTEGER DEFAULT NULL,
                is_reversal INTEGER DEFAULT 0,
                reversal_of_id INTEGER DEFAULT NULL,
                is_business INTEGER DEFAULT 0,
                business_id INTEGER DEFAULT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (business_id) REFERENCES businesses(business_id) ON DELETE SET NULL
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ledger_user_date ON financial_ledger(user_id, transaction_date DESC);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ledger_category ON financial_ledger(category_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ledger_reversal ON financial_ledger(is_reversal);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ledger_business ON financial_ledger(business_id);")
        print("OK")

        # =================================================================
        # TABLE 6: recurring_expenses - Automated bill payments
        # =================================================================
        print("Creating table 'recurring_expenses'...", end=" ")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recurring_expenses (
                expense_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                description TEXT NOT NULL,
                amount TEXT NOT NULL,
                frequency TEXT CHECK(frequency IN ('DAILY', 'WEEKLY', 'BI_WEEKLY', 'MONTHLY', 'QUARTERLY', 'YEARLY')) NOT NULL DEFAULT 'MONTHLY',
                due_day_of_month INTEGER NOT NULL DEFAULT 1,
                last_processed_date TEXT DEFAULT NULL,
                payment_account_id INTEGER DEFAULT NULL,
                category_id INTEGER DEFAULT NULL,
                is_variable INTEGER DEFAULT 0,
                estimated_amount TEXT DEFAULT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (category_id) REFERENCES expense_categories(category_id) ON DELETE SET NULL
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_recurring_expenses_user_id ON recurring_expenses(user_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_recurring_expenses_category_id ON recurring_expenses(category_id);")
        print("OK")

        # =================================================================
        # TABLE 7: recurring_income - Automated income deposits
        # =================================================================
        print("Creating table 'recurring_income'...", end=" ")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recurring_income (
                income_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT DEFAULT NULL,
                amount TEXT NOT NULL,
                frequency TEXT CHECK(frequency IN ('DAILY', 'WEEKLY', 'BI_WEEKLY', 'MONTHLY', 'QUARTERLY', 'YEARLY')) NOT NULL DEFAULT 'MONTHLY',
                due_day_of_month INTEGER NOT NULL DEFAULT 1,
                destination_account_id INTEGER NOT NULL,
                category_id INTEGER DEFAULT NULL,
                last_processed_date TEXT DEFAULT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                is_variable INTEGER DEFAULT 0,
                estimated_amount TEXT DEFAULT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (destination_account_id) REFERENCES accounts(account_id) ON DELETE CASCADE,
                FOREIGN KEY (category_id) REFERENCES expense_categories(category_id) ON DELETE SET NULL
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_recurring_income_user_id ON recurring_income(user_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_recurring_income_category_id ON recurring_income(category_id);")
        print("OK")

        # =================================================================
        # TABLE 8: loans - Debt tracking with payment schedules
        # =================================================================
        print("Creating table 'loans'...", end=" ")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS loans (
                loan_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                principal_amount TEXT NOT NULL,
                outstanding_balance TEXT NOT NULL,
                interest_rate REAL NOT NULL,
                monthly_payment TEXT NOT NULL,
                next_payment_date TEXT NOT NULL,
                status TEXT CHECK(status IN ('ACTIVE', 'PAID')) NOT NULL DEFAULT 'ACTIVE',
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_loans_user_id ON loans(user_id);")
        print("OK")

        # =================================================================
        # TABLE 9: budgets - Monthly category budgets
        # =================================================================
        print("Creating table 'budgets'...", end=" ")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                budget_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                category_id INTEGER NOT NULL,
                monthly_limit TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (category_id) REFERENCES expense_categories(category_id) ON DELETE CASCADE,
                UNIQUE(user_id, category_id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_budgets_user ON budgets(user_id);")
        print("OK")

        # =================================================================
        # TABLE 10: savings_goals - Financial goal tracking
        # =================================================================
        print("Creating table 'savings_goals'...", end=" ")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS savings_goals (
                goal_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                target_amount TEXT NOT NULL,
                current_amount TEXT DEFAULT '0.00',
                target_date TEXT,
                color TEXT DEFAULT '#10b981',
                icon TEXT DEFAULT 'piggy-bank',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT DEFAULT NULL,
                account_id INTEGER DEFAULT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (account_id) REFERENCES accounts(account_id) ON DELETE SET NULL
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_goals_user ON savings_goals(user_id);")
        print("OK")

        # =================================================================
        # TABLE 11: schema_version - Migration tracking
        # =================================================================
        print("Creating table 'schema_version'...", end=" ")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY,
                description TEXT NOT NULL,
                applied_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("OK")

        # =================================================================
        # GAME-SPECIFIC TABLES (Digital Harvest v5)
        # =================================================================
        print()
        print("--- Creating Game Tables ---")
        print()

        # =================================================================
        # TABLE 12: businesses - Available business types
        # =================================================================
        print("Creating table 'businesses'...", end=" ")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS businesses (
                business_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                display_name TEXT NOT NULL,
                description TEXT,
                volatility TEXT CHECK(volatility IN ('LOW', 'MEDIUM', 'HIGH')) NOT NULL,
                icon TEXT DEFAULT '📦',
                starting_cash REAL DEFAULT 10000.00
            )
        """)
        print("OK")

        # =================================================================
        # TABLE 13: game_state - Player's current game state (one per user+business)
        # =================================================================
        print("Creating table 'game_state'...", end=" ")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS game_state (
                user_id INTEGER NOT NULL,
                business_id INTEGER NOT NULL,
                current_date TEXT NOT NULL,
                starting_cash TEXT DEFAULT '50000.00',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, business_id),
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (business_id) REFERENCES businesses(business_id)
            )
        """)
        print("OK")

        # =================================================================
        # TABLE 14: product_categories - Product groupings
        # =================================================================
        print("Creating table 'product_categories'...", end=" ")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS product_categories (
                category_id INTEGER PRIMARY KEY AUTOINCREMENT,
                business_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                color TEXT DEFAULT '#6366f1',
                FOREIGN KEY (business_id) REFERENCES businesses(business_id),
                UNIQUE(business_id, name)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_product_categories_business ON product_categories(business_id);")
        print("OK")

        # =================================================================
        # TABLE 15: products - SKU catalog
        # =================================================================
        print("Creating table 'products'...", end=" ")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                business_id INTEGER NOT NULL,
                category_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                sku TEXT NOT NULL,
                base_demand INTEGER NOT NULL DEFAULT 100,
                price_sensitivity REAL NOT NULL DEFAULT 1.5,
                default_price TEXT NOT NULL,
                status TEXT CHECK(status IN ('LOCKED', 'UNLOCKED')) DEFAULT 'UNLOCKED',
                unlock_revenue TEXT DEFAULT NULL,
                attribute_1 TEXT DEFAULT NULL,
                attribute_2 TEXT DEFAULT NULL,
                attribute_3 TEXT DEFAULT NULL,
                FOREIGN KEY (business_id) REFERENCES businesses(business_id),
                FOREIGN KEY (category_id) REFERENCES product_categories(category_id),
                UNIQUE(business_id, sku)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_business ON products(business_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id);")
        print("OK")

        # =================================================================
        # TABLE 16: vendors - Supplier catalog
        # =================================================================
        print("Creating table 'vendors'...", end=" ")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vendors (
                vendor_id INTEGER PRIMARY KEY AUTOINCREMENT,
                business_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                vendor_type TEXT CHECK(vendor_type IN ('MANUFACTURER', 'DISTRIBUTOR', 'BOUTIQUE')) NOT NULL,
                location TEXT NOT NULL,
                base_lead_time_days INTEGER NOT NULL DEFAULT 7,
                reliability_score REAL DEFAULT 0.95,
                minimum_order_value TEXT DEFAULT '100.00',
                payment_terms TEXT DEFAULT 'NET30',
                shipping_flat_fee TEXT DEFAULT '25.00',
                status TEXT CHECK(status IN ('AVAILABLE', 'PROSPECTIVE', 'LOCKED')) DEFAULT 'AVAILABLE',
                unlock_relationship INTEGER DEFAULT NULL,
                unlock_order_value TEXT DEFAULT NULL,
                FOREIGN KEY (business_id) REFERENCES businesses(business_id),
                UNIQUE(business_id, name)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_vendors_business ON vendors(business_id);")
        print("OK")

        # =================================================================
        # TABLE 17: vendor_products - Which vendors carry which products
        # =================================================================
        print("Creating table 'vendor_products'...", end=" ")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vendor_products (
                vendor_product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                vendor_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                unit_cost TEXT NOT NULL,
                min_quantity INTEGER DEFAULT 1,
                FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE,
                UNIQUE(vendor_id, product_id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_vendor_products_vendor ON vendor_products(vendor_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_vendor_products_product ON vendor_products(product_id);")
        print("OK")

        # =================================================================
        # TABLE 18: volume_discounts - Tiered pricing
        # =================================================================
        print("Creating table 'volume_discounts'...", end=" ")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS volume_discounts (
                discount_id INTEGER PRIMARY KEY AUTOINCREMENT,
                vendor_product_id INTEGER NOT NULL,
                min_quantity INTEGER NOT NULL,
                max_quantity INTEGER DEFAULT NULL,
                unit_cost TEXT NOT NULL,
                FOREIGN KEY (vendor_product_id) REFERENCES vendor_products(vendor_product_id) ON DELETE CASCADE
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_volume_discounts_vp ON volume_discounts(vendor_product_id);")
        print("OK")

        # =================================================================
        # TABLE 19: player_product_settings - Player's pricing decisions
        # =================================================================
        print("Creating table 'player_product_settings'...", end=" ")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS player_product_settings (
                setting_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                current_price TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE,
                UNIQUE(user_id, product_id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_player_settings_user ON player_product_settings(user_id);")
        print("OK")

        # =================================================================
        # TABLE 20: vendor_relationships - Player's relationship with vendors
        # =================================================================
        print("Creating table 'vendor_relationships'...", end=" ")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vendor_relationships (
                relationship_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                vendor_id INTEGER NOT NULL,
                relationship_score INTEGER DEFAULT 50,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id) ON DELETE CASCADE,
                UNIQUE(user_id, vendor_id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_vendor_rel_user ON vendor_relationships(user_id);")
        print("OK")

        # =================================================================
        # TABLE 21: inventory_layers - FIFO cost tracking
        # =================================================================
        print("Creating table 'inventory_layers'...", end=" ")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventory_layers (
                layer_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity_received INTEGER NOT NULL,
                quantity_remaining INTEGER NOT NULL,
                unit_cost TEXT NOT NULL,
                received_date TEXT NOT NULL,
                purchase_order_id INTEGER DEFAULT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE,
                FOREIGN KEY (purchase_order_id) REFERENCES purchase_orders(order_id) ON DELETE SET NULL
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_inventory_user_product ON inventory_layers(user_id, product_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_inventory_received ON inventory_layers(received_date);")
        print("OK")

        # =================================================================
        # TABLE 22: purchase_orders - Inbound orders
        # =================================================================
        print("Creating table 'purchase_orders'...", end=" ")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS purchase_orders (
                order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                vendor_id INTEGER NOT NULL,
                order_date TEXT NOT NULL,
                expected_arrival_date TEXT NOT NULL,
                actual_arrival_date TEXT DEFAULT NULL,
                status TEXT CHECK(status IN ('PENDING', 'IN_TRANSIT', 'DELAYED', 'DELIVERED', 'CANCELLED')) DEFAULT 'PENDING',
                total_amount TEXT NOT NULL,
                shipping_cost TEXT DEFAULT '0.00',
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_po_user ON purchase_orders(user_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_po_status ON purchase_orders(status);")
        print("OK")

        # =================================================================
        # TABLE 23: purchase_order_items - Line items in POs
        # =================================================================
        print("Creating table 'purchase_order_items'...", end=" ")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS purchase_order_items (
                item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                unit_cost TEXT NOT NULL,
                FOREIGN KEY (order_id) REFERENCES purchase_orders(order_id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products(product_id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_poi_order ON purchase_order_items(order_id);")
        print("OK")

        # =================================================================
        # TABLE 24: accounts_payable - Bills owed to vendors
        # =================================================================
        print("Creating table 'accounts_payable'...", end=" ")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS accounts_payable (
                payable_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                vendor_id INTEGER NOT NULL,
                purchase_order_id INTEGER NOT NULL,
                amount_due TEXT NOT NULL,
                creation_date TEXT NOT NULL,
                due_date TEXT NOT NULL,
                paid_date TEXT DEFAULT NULL,
                status TEXT CHECK(status IN ('UNPAID', 'PAID', 'OVERDUE')) DEFAULT 'UNPAID',
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id),
                FOREIGN KEY (purchase_order_id) REFERENCES purchase_orders(order_id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ap_user ON accounts_payable(user_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ap_status ON accounts_payable(status);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ap_due ON accounts_payable(due_date);")
        print("OK")

        # =================================================================
        # TABLE 25: marketing_campaigns - Player-initiated promotions
        # =================================================================
        print("Creating table 'marketing_campaigns'...", end=" ")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS marketing_campaigns (
                campaign_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                campaign_type TEXT CHECK(campaign_type IN ('PRODUCT', 'CATEGORY', 'ALL')) NOT NULL,
                target_id INTEGER DEFAULT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                demand_boost REAL NOT NULL DEFAULT 1.25,
                cost TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_campaigns_user ON marketing_campaigns(user_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_campaigns_dates ON marketing_campaigns(start_date, end_date);")
        print("OK")

        # =================================================================
        # TABLE 26: market_events - Random market shifts
        # =================================================================
        print("Creating table 'market_events'...", end=" ")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS market_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                demand_boost REAL NOT NULL DEFAULT 1.30,
                target_attribute TEXT DEFAULT NULL,
                target_value TEXT DEFAULT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_user ON market_events(user_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_dates ON market_events(start_date, end_date);")
        print("OK")

        # =================================================================
        # TABLE 27: daily_sales_summary - Aggregated daily sales (performance)
        # =================================================================
        print("Creating table 'daily_sales_summary'...", end=" ")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_sales_summary (
                summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                sale_date TEXT NOT NULL,
                product_id INTEGER NOT NULL,
                units_sold INTEGER NOT NULL DEFAULT 0,
                revenue TEXT NOT NULL DEFAULT '0.00',
                cogs TEXT NOT NULL DEFAULT '0.00',
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products(product_id),
                UNIQUE(user_id, sale_date, product_id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sales_user_date ON daily_sales_summary(user_id, sale_date);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sales_product ON daily_sales_summary(product_id);")
        print("OK")

        # Commit all changes
        conn.commit()
        print()
        print("[OK] Database schema created successfully!")
        print(f"[OK] Database file: {db_path}")

        # Seed the database with initial data (businesses, products, vendors)
        try:
            from seed_data import seed_all
            seed_all()
        except ImportError:
            from src.seed_data import seed_all
            seed_all()

        return True

    except sqlite3.Error as err:
        print(f"\n[ERROR] Error creating database: {err}")
        conn.rollback()
        return False

    finally:
        conn.close()


def reset_database():
    """
    [WARNING]  DANGER: Delete the existing database and create a fresh one.
    All data will be permanently lost!
    """
    db_path = get_db_path()

    if db_path.exists():
        print(f"[WARNING]  WARNING: Deleting existing database at {db_path}")
        db_path.unlink()
        print("[OK] Old database deleted")

    return create_database()


def verify_schema():
    """Verify that all tables and indexes exist"""
    db_path = get_db_path()

    if not db_path.exists():
        print("[ERROR] Database does not exist")
        return False

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Expected tables
    expected_tables = [
        # Financial (from Perfect Books)
        'users',
        'accounts',
        'expense_categories',
        'financial_ledger',
        'recurring_expenses',
        'recurring_income',
        'loans',
        'budgets',
        'savings_goals',
        'schema_version',
        # Game-specific (Digital Harvest v5)
        'businesses',
        'game_state',
        'product_categories',
        'products',
        'vendors',
        'vendor_products',
        'volume_discounts',
        'player_product_settings',
        'vendor_relationships',
        'inventory_layers',
        'purchase_orders',
        'purchase_order_items',
        'accounts_payable',
        'marketing_campaigns',
        'market_events',
        'daily_sales_summary'
    ]

    print("Verifying database schema...")
    print()

    # Check each table exists
    for table in expected_tables:
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
        if cursor.fetchone():
            print(f"[OK] Table '{table}' exists")
        else:
            print(f"[ERROR] Table '{table}' MISSING")
            conn.close()
            return False

    # Check foreign keys are enabled
    cursor.execute("PRAGMA foreign_keys;")
    fk_status = cursor.fetchone()[0]
    print()
    print(f"Foreign key enforcement: {'[OK] ENABLED' if fk_status else '[ERROR] DISABLED (WARNING!)'}")

    conn.close()
    print()
    print("[OK] Schema verification complete")
    return True


def get_table_info(table_name):
    """Display schema information for a specific table"""
    db_path = get_db_path()

    if not db_path.exists():
        print("[ERROR] Database does not exist")
        return

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = cursor.fetchall()

    print(f"\nTable: {table_name}")
    print("=" * 80)
    print(f"{'Column':<25} {'Type':<15} {'NotNull':<10} {'Default':<20}")
    print("-" * 80)

    for col in columns:
        cid, name, col_type, notnull, default_val, pk = col
        print(f"{name:<25} {col_type:<15} {str(bool(notnull)):<10} {str(default_val):<20}")

    # Show indexes
    cursor.execute(f"PRAGMA index_list({table_name});")
    indexes = cursor.fetchall()

    if indexes:
        print()
        print("Indexes:")
        for idx in indexes:
            seq, name, unique, origin, partial = idx
            print(f"  - {name} {'(UNIQUE)' if unique else ''}")

    conn.close()


if __name__ == "__main__":
    print("=" * 80)
    print("Digital Harvest v5 - SQLite Database Setup")
    print("=" * 80)
    print()

    db_path = get_db_path()

    if db_path.exists():
        print(f"Database already exists at: {db_path}")
        print()
        choice = input("Choose an option:\n  1. Verify existing schema\n  2. Reset database ([WARNING]  DELETES ALL DATA)\n  3. Cancel\n\nChoice: ")

        if choice == '1':
            verify_schema()
        elif choice == '2':
            confirm = input("\n[WARNING]  WARNING: This will DELETE ALL DATA. Type 'DELETE' to confirm: ")
            if confirm == 'DELETE':
                reset_database()
                verify_schema()
            else:
                print("Reset cancelled.")
        else:
            print("Cancelled.")
    else:
        print("No existing database found. Creating new database...")
        print()
        create_database()
        verify_schema()
