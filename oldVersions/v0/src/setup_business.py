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

# --- DATA DEFINITIONS ---
CATEGORIES_TO_ADD = [
    "Linear Switches", "Tactile Switches", "Clicky Switches"
]

PRODUCTS_TO_ADD = [
    # Linear Switches
    {"category_name": "Linear Switches", "name": "Gateron Yellow (10-pack)", "base_demand": 150, "price_sensitivity": 0.8, "default_cost": 2.40, "default_price": 4.50},
    {"category_name": "Linear Switches", "name": "Cherry MX Red (10-pack)", "base_demand": 120, "price_sensitivity": 0.7, "default_cost": 3.00, "default_price": 5.50},
    {"category_name": "Linear Switches", "name": "Kailh Box Red (10-pack)", "base_demand": 90, "price_sensitivity": 0.85, "default_cost": 2.80, "default_price": 5.00},
    {"category_name": "Linear Switches", "name": "Gateron Oil King (10-pack)", "base_demand": 70, "price_sensitivity": 0.5, "default_cost": 6.50, "default_price": 11.00},
    {"category_name": "Linear Switches", "name": "JWK Black Linear (10-pack)", "base_demand": 85, "price_sensitivity": 0.6, "default_cost": 5.50, "default_price": 9.50},
    {"category_name": "Linear Switches", "name": "Akko CS Jelly Black (10-pack)", "base_demand": 130, "price_sensitivity": 0.9, "default_cost": 2.90, "default_price": 5.20},
    {"category_name": "Linear Switches", "name": "Durock POM Linear (10-pack)", "base_demand": 60, "price_sensitivity": 0.55, "default_cost": 6.00, "default_price": 10.50},
    
    # Tactile Switches
    {"category_name": "Tactile Switches", "name": "Cherry MX Brown (10-pack)", "base_demand": 140, "price_sensitivity": 0.75, "default_cost": 3.10, "default_price": 5.60},
    {"category_name": "Tactile Switches", "name": "Gateron Brown (10-pack)", "base_demand": 160, "price_sensitivity": 0.8, "default_cost": 2.50, "default_price": 4.60},
    {"category_name": "Tactile Switches", "name": "Boba U4T (10-pack)", "base_demand": 80, "price_sensitivity": 0.4, "default_cost": 6.50, "default_price": 11.50},
    {"category_name": "Tactile Switches", "name": "Zealios V2 67g (10-pack)", "base_demand": 50, "price_sensitivity": 0.3, "default_cost": 9.00, "default_price": 15.00},
    {"category_name": "Tactile Switches", "name": "Kailh Box Royal (10-pack)", "base_demand": 75, "price_sensitivity": 0.6, "default_cost": 4.00, "default_price": 7.50},
    {"category_name": "Tactile Switches", "name": "Akko CS Lavender Purple (10-pack)", "base_demand": 110, "price_sensitivity": 0.8, "default_cost": 3.00, "default_price": 5.80},
    {"category_name": "Tactile Switches", "name": "Durock T1 (10-pack)", "base_demand": 65, "price_sensitivity": 0.5, "default_cost": 5.80, "default_price": 10.00},

    # Clicky Switches
    {"category_name": "Clicky Switches", "name": "Cherry MX Blue (10-pack)", "base_demand": 100, "price_sensitivity": 0.8, "default_cost": 3.20, "default_price": 5.70},
    {"category_name": "Clicky Switches", "name": "Gateron Blue (10-pack)", "base_demand": 115, "price_sensitivity": 0.85, "default_cost": 2.60, "default_price": 4.70},
    {"category_name": "Clicky Switches", "name": "Kailh Box White (10-pack)", "base_demand": 95, "price_sensitivity": 0.7, "default_cost": 3.50, "default_price": 6.00},
    {"category_name": "Clicky Switches", "name": "Kailh Box Jade (10-pack)", "base_demand": 85, "price_sensitivity": 0.6, "default_cost": 4.50, "default_price": 8.00},
    {"category_name": "Clicky Switches", "name": "Kailh Box Navy (10-pack)", "base_demand": 80, "price_sensitivity": 0.6, "default_cost": 4.50, "default_price": 8.00},
    {"category_name": "Clicky Switches", "name": "Zealio Clickiez 75g (10-pack)", "base_demand": 45, "price_sensitivity": 0.35, "default_cost": 11.00, "default_price": 18.00},
]

RECURRING_EXPENSES_TO_ADD = [
    {"description": "Owner's Salary", "account": "Salaries & Wages", "amount": 2500.00, "frequency": "MONTHLY"},
    {"description": "E-commerce Platform Fee", "account": "Software", "amount": 79.00, "frequency": "MONTHLY"},
    {"description": "Warehouse & Storage", "account": "Rent", "amount": 350.00, "frequency": "MONTHLY"},
    {"description": "Software Subscriptions", "account": "Software", "amount": 120.00, "frequency": "MONTHLY"},
    {"description": "Marketing Ad Budget", "account": "Marketing", "amount": 50.00, "frequency": "DAILY"},
]

# --- SCHEMA DEFINITION (SQL) ---
TABLES = {}

TABLES['categories'] = (
    "CREATE TABLE `categories` ("
    "  `category_id` INT AUTO_INCREMENT PRIMARY KEY,"
    "  `name` VARCHAR(255) NOT NULL UNIQUE"
    ") ENGINE=InnoDB")

TABLES['products'] = (
    "CREATE TABLE `products` ("
    "  `product_id` INT AUTO_INCREMENT PRIMARY KEY,"
    "  `name` VARCHAR(255) NOT NULL UNIQUE,"
    "  `category_id` INT NOT NULL,"
    "  `base_demand` INT NOT NULL,"
    "  `price_sensitivity` FLOAT NOT NULL,"
    "  `default_cost` DECIMAL(10, 2) NOT NULL,"
    "  `default_price` DECIMAL(10, 2) NOT NULL,"
    "  FOREIGN KEY (`category_id`) REFERENCES `categories` (`category_id`)"
    ") ENGINE=InnoDB")

TABLES['inventory_ledger'] = (
    "CREATE TABLE `inventory_ledger` ("
    "  `entry_id` INT AUTO_INCREMENT PRIMARY KEY,"
    "  `transaction_uuid` VARCHAR(36) NOT NULL,"
    "  `transaction_date` DATETIME NOT NULL,"
    "  `product_id` INT NOT NULL,"
    "  `type` VARCHAR(50) NOT NULL,"
    "  `description` VARCHAR(255),"
    "  `quantity_change` INT NOT NULL,"
    "  `unit_cost` DECIMAL(10, 2) DEFAULT 0.00,"
    "  `unit_price` DECIMAL(10, 2) DEFAULT 0.00,"
    "  `total_value` DECIMAL(10, 2) NOT NULL,"
    "  `quantity_on_hand_after` INT NOT NULL,"
    "  FOREIGN KEY (`product_id`) REFERENCES `products` (`product_id`),"
    "  INDEX `idx_transaction_uuid` (`transaction_uuid`)"
    ") ENGINE=InnoDB")

TABLES['financial_ledger'] = (
    "CREATE TABLE `financial_ledger` ("
    "  `entry_id` INT AUTO_INCREMENT PRIMARY KEY,"
    "  `transaction_uuid` VARCHAR(36) NOT NULL,"
    "  `transaction_date` DATETIME NOT NULL,"
    "  `account` VARCHAR(100) NOT NULL,"
    "  `description` VARCHAR(255),"
    "  `debit` DECIMAL(10, 2) DEFAULT 0.00,"
    "  `credit` DECIMAL(10, 2) DEFAULT 0.00,"
    "  INDEX `idx_transaction_uuid` (`transaction_uuid`)"
    ") ENGINE=InnoDB")

TABLES['business_state'] = (
    "CREATE TABLE `business_state` ("
    "  `state_key` VARCHAR(50) PRIMARY KEY,"
    "  `state_value` VARCHAR(255) NOT NULL"
    ") ENGINE=InnoDB")

TABLES['recurring_expenses'] = (
    "CREATE TABLE `recurring_expenses` ("
    "  `expense_id` INT AUTO_INCREMENT PRIMARY KEY,"
    "  `description` VARCHAR(255) NOT NULL,"
    "  `account` VARCHAR(100) NOT NULL,"
    "  `amount` DECIMAL(10, 2) NOT NULL,"
    "  `frequency` ENUM('DAILY', 'MONTHLY') NOT NULL,"
    "  `last_processed_date` DATE DEFAULT NULL"
    ") ENGINE=InnoDB")


# --- SETUP FUNCTIONS ---
def main():
    db_connection = None
    try:
        db_connection = mysql.connector.connect(
            user=DB_CONFIG['user'], password=DB_CONFIG['password'],
            host=DB_CONFIG['host'], port=DB_CONFIG['port']
        )
        cursor = db_connection.cursor()
        db_name = DB_CONFIG['database']
        print(f"--- Resetting Database: '{db_name}' ---")
        cursor.execute(f"DROP DATABASE IF EXISTS {db_name}")
        print(f"  - Dropped database '{db_name}' (if it existed).")
        cursor.execute(f"CREATE DATABASE {db_name} DEFAULT CHARACTER SET 'utf8'")
        print(f"  - Created new database '{db_name}'.")
        db_connection.database = db_name
        print(f"Successfully connected to database '{db_name}'.")

        print("\n--- Creating Tables ---")
        for table_name, table_description in TABLES.items():
            try:
                print(f"Creating table '{table_name}': ", end='')
                cursor.execute(table_description)
                print("OK")
            except mysql.connector.Error as err:
                print(f"Error creating table {table_name}: {err.msg}")
        
        print("\n--- Populating Initial Data ---")
        # Categories
        for category_name in CATEGORIES_TO_ADD:
            cursor.execute("INSERT INTO categories (name) VALUES (%s)", (category_name,))
        db_connection.commit()
        
        # Products
        cursor.execute("SELECT category_id, name FROM categories")
        category_map = {name: cat_id for cat_id, name in cursor.fetchall()}

        for product in PRODUCTS_TO_ADD:
            category_id = category_map[product['category_name']]
            cursor.execute(
                "INSERT INTO products (name, category_id, base_demand, price_sensitivity, default_cost, default_price) VALUES (%s, %s, %s, %s, %s, %s)",
                (product['name'], category_id, product['base_demand'], product['price_sensitivity'], product['default_cost'], product['default_price'])
            )
        db_connection.commit()

        # Recurring Expenses
        for exp in RECURRING_EXPENSES_TO_ADD:
            cursor.execute(
                "INSERT INTO recurring_expenses (description, account, amount, frequency) VALUES (%s, %s, %s, %s)",
                (exp['description'], exp['account'], exp['amount'], exp['frequency'])
            )
        db_connection.commit()
        print("  - Initial data populated.")

    except mysql.connector.Error as err:
        print(f"Database setup failed: {err}")
    finally:
        if db_connection and db_connection.is_connected():
            cursor.close()
            db_connection.close()
            print("\nSetup complete. MySQL connection closed.")

if __name__ == "__main__":
    confirm = input(
        "WARNING: This script will completely reset your database, deleting all existing data.\n"
        "Are you sure you want to proceed? (y/n): "
    ).lower()
    if confirm == 'y':
        main()
    else:
        print("Setup cancelled.")