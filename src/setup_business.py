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
# ... (omitted for brevity, no changes here) ...
CATEGORIES_TO_ADD = [
    "Standard Linear", "Standard Tactile", "Premium Tactile", "House Brand"
]
PRODUCTS_TO_ADD = [
    { "category_name": "Standard Linear", "name": "Gateron Yellow Switches (10-pack)", "base_demand": 150, "price_sensitivity": 0.8 },
    { "category_name": "Premium Tactile", "name": "Zealios V2 Tactile Switches (10-pack)", "base_demand": 40, "price_sensitivity": 0.4 },
    { "category_name": "House Brand", "name": "DH 'Aurora' Linear Switches (10-pack)", "base_demand": 200, "price_sensitivity": 0.9 },
]

# --- SCHEMA DEFINITION (SQL) ---
TABLES = {}

TABLES['categories'] = (
# ... (omitted for brevity, no changes here) ...
    "CREATE TABLE `categories` ("
    "  `category_id` INT AUTO_INCREMENT PRIMARY KEY,"
    "  `name` VARCHAR(255) NOT NULL UNIQUE"
    ") ENGINE=InnoDB")

TABLES['products'] = (
# ... (omitted for brevity, no changes here) ...
    "CREATE TABLE `products` ("
    "  `product_id` INT AUTO_INCREMENT PRIMARY KEY,"
    "  `name` VARCHAR(255) NOT NULL UNIQUE,"
    "  `category_id` INT NOT NULL,"
    "  `base_demand` INT NOT NULL,"
    "  `price_sensitivity` FLOAT NOT NULL,"
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
# ... (omitted for brevity, no changes here) ...
    "CREATE TABLE `business_state` ("
    "  `state_key` VARCHAR(50) PRIMARY KEY,"
    "  `state_value` VARCHAR(255) NOT NULL"
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
        for category_name in CATEGORIES_TO_ADD:
            cursor.execute("INSERT INTO categories (name) VALUES (%s)", (category_name,))
        db_connection.commit()
        
        cursor.execute("SELECT category_id, name FROM categories")
        category_map = {name: cat_id for cat_id, name in cursor.fetchall()}

        for product in PRODUCTS_TO_ADD:
            category_id = category_map[product['category_name']]
            cursor.execute(
                "INSERT INTO products (name, category_id, base_demand, price_sensitivity) VALUES (%s, %s, %s, %s)",
                (product['name'], category_id, product['base_demand'], product['price_sensitivity'])
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