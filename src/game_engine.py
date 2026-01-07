"""
Digital Harvest v5 - Game Engine

Core game logic including:
- Sales demand calculation (8 multipliers)
- Time advancement processing
- Daily sales generation with batching for performance
- Market events and campaigns
"""

import sqlite3
import math
import random
import uuid
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from contextlib import contextmanager

# Weekly sales pattern (Monday=0 through Sunday=6)
WEEKLY_FACTORS = [0.90, 0.95, 1.00, 1.10, 1.40, 1.50, 1.20]

# Volatility multipliers by business type
VOLATILITY_RANGES = {
    'LOW': (0.95, 1.05),      # Farm - stable
    'MEDIUM': (0.85, 1.15),   # Keyboards - moderate swings
    'HIGH': (0.85, 1.15),     # Tech - reduced from (0.70, 1.30) for balance
}

# Business maturity settings
MATURITY_DAYS = 90  # Days to reach full sales velocity
MATURITY_MIN = 0.05  # Starting demand multiplier (5%)
MIN_DAYS_FOR_EVENTS = 14  # Don't trigger market events until day 14


def get_maturity_factor(days_elapsed: int) -> float:
    """
    Calculate business maturity factor for demand scaling.

    New businesses start very slow and build customer base over 90 days.
    This creates realistic gameplay where players must manage cash flow
    carefully during the early months.

    Returns:
        float: Multiplier from 0.05 (5%) on day 1 to 1.0 (100%) on day 90+

    Day-by-day impact:
        Day 1:  ~5% of normal sales
        Day 7:  ~15% of normal sales
        Day 14: ~22% of normal sales
        Day 30: ~38% of normal sales
        Day 60: ~62% of normal sales
        Day 90+: 100% (full velocity)
    """
    if days_elapsed >= MATURITY_DAYS:
        return 1.0

    if days_elapsed <= 0:
        return MATURITY_MIN

    # Smooth curve: starts at 5%, grows to 100% over 90 days
    progress = days_elapsed / MATURITY_DAYS
    return MATURITY_MIN + (1.0 - MATURITY_MIN) * (progress ** 0.6)

# Market event definitions (can be extended per business)
MARKET_EVENTS = {
    'keyboards': [
        {
            'name': 'Streamer Craze',
            'description': 'Popular streamers are showcasing keyboard builds, boosting demand for smooth, quiet switches.',
            'target_attributes': {'attribute_1': 'LINEAR', 'attribute_3': 'QUIET'},
            'boost': 1.50,
            'duration_days': 14,
        },
        {
            'name': 'Ergonomics Trend',
            'description': 'A new study on workplace ergonomics is boosting demand for tactile switches.',
            'target_attributes': {'attribute_1': 'TACTILE'},
            'boost': 1.30,
            'duration_days': 20,
        },
        {
            'name': 'ASMR Popularity',
            'description': 'ASMR videos featuring clicky keyboards are driving demand for loud switches.',
            'target_attributes': {'attribute_3': 'LOUD'},
            'boost': 1.75,
            'duration_days': 10,
        },
    ],
    'tech': [
        {
            'name': 'Crypto Bull Run',
            'description': 'Cryptocurrency prices are surging, miners are stockpiling GPUs.',
            'target_attributes': {'attribute_1': 'MINING'},
            'boost': 2.00,
            'duration_days': 21,
        },
        {
            'name': 'AI Boom',
            'description': 'New AI models require massive compute, server components in high demand.',
            'target_attributes': {'attribute_1': 'SERVER'},
            'boost': 1.60,
            'duration_days': 30,
        },
        {
            'name': 'Retro Gaming Revival',
            'description': 'Nostalgia wave hits - vintage hardware prices are skyrocketing.',
            'target_attributes': {'attribute_1': 'VINTAGE'},
            'boost': 1.80,
            'duration_days': 14,
        },
    ],
    'farm': [
        {
            'name': 'Farm-to-Table Movement',
            'description': 'Restaurants are prioritizing local greens, demand surging.',
            'target_attributes': {'attribute_1': 'LEAFY'},
            'boost': 1.40,
            'duration_days': 28,
        },
        {
            'name': 'Superfood Craze',
            'description': 'Health influencers are promoting microgreens as superfoods.',
            'target_attributes': {'attribute_1': 'MICRO'},
            'boost': 1.60,
            'duration_days': 21,
        },
        {
            'name': 'Cocktail Renaissance',
            'description': 'Craft cocktail bars are buying fresh herbs in bulk.',
            'target_attributes': {'attribute_1': 'HERB'},
            'boost': 1.35,
            'duration_days': 14,
        },
    ],
}


class GameEngine:
    """Core game logic engine for Digital Harvest."""

    def __init__(self, db_path: str):
        self.db_path = db_path

    @contextmanager
    def get_db(self):
        """Get a database connection with foreign keys enabled."""
        conn = sqlite3.connect(self.db_path, isolation_level=None)  # autocommit mode
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
        finally:
            conn.close()

    def get_game_state(self, user_id: int, business_id: int) -> dict:
        """Get or create game state for a user/business combination.

        Each user can have up to 3 games (one per business type).
        """
        with self.get_db() as conn:
            row = conn.execute("""
                SELECT * FROM game_state
                WHERE user_id = ? AND business_id = ?
            """, (user_id, business_id)).fetchone()

            if row:
                state = dict(row)
                # Normalize column names for consistency
                state['current_game_date'] = state.get('current_date', state.get('current_game_date'))
                state['start_date'] = state.get('created_at', state.get('start_date', state['current_game_date']))
                return state

            # Create new game state for this user+business combination
            start_date = datetime.now().strftime('%Y-%m-%d')
            conn.execute("""
                INSERT INTO game_state (user_id, business_id, current_date, start_date)
                VALUES (?, ?, ?, ?)
            """, (user_id, business_id, start_date, start_date))

            return {
                'user_id': user_id,
                'business_id': business_id,
                'current_game_date': start_date,
                'start_date': start_date,
            }

    def calculate_demand(
        self,
        product: dict,
        current_date: datetime,
        start_date: datetime,
        player_price: Decimal,
        campaign_boost: float,
        event_boost: float,
        volatility: str,
    ) -> int:
        """
        Calculate daily demand for a product using 9 multipliers.

        Returns the number of units demanded (before stock limiting).
        """
        # 1. Base demand (stored as daily average)
        daily_base = float(product['base_demand'])

        # 2. Business maturity factor (NEW - ramps 5% to 100% over 90 days)
        days_elapsed = (current_date - start_date).days
        maturity = get_maturity_factor(days_elapsed)

        # 3. Trend factor (10% YoY growth)
        years = days_elapsed / 365.25
        trend = 1.10 ** years

        # 4. Seasonal factor (sine wave, ±30%)
        day_of_year = current_date.timetuple().tm_yday
        seasonal = 1 + 0.3 * math.sin(2 * math.pi * (day_of_year - 80) / 365.25)

        # 5. Weekly factor (weekend spike)
        weekly = WEEKLY_FACTORS[current_date.weekday()]

        # 6. Price factor (sensitivity-based)
        default_price = Decimal(product['default_price'])
        if default_price > 0:
            price_diff_pct = float((player_price - default_price) / default_price)
            price_sensitivity = float(product['price_sensitivity'])
            price_factor = max(0.0, 1 - (price_sensitivity * price_diff_pct))
        else:
            price_factor = 1.0

        # 7. Campaign boost (passed in)
        # 8. Event boost (passed in)

        # 9. Random variance (based on volatility)
        vol_min, vol_max = VOLATILITY_RANGES.get(volatility, (0.90, 1.10))
        random_factor = random.uniform(vol_min, vol_max)

        # Calculate final demand (maturity factor is the key limiter early game)
        calculated = daily_base * maturity * trend * seasonal * weekly * price_factor * campaign_boost * event_boost * random_factor

        return max(0, int(calculated))

    def get_active_campaigns(self, user_id: int, business_id: int, date: datetime) -> list:
        """Get campaigns active on a given date."""
        date_str = date.strftime('%Y-%m-%d')
        with self.get_db() as conn:
            rows = conn.execute("""
                SELECT * FROM marketing_campaigns
                WHERE user_id = ?
                  AND start_date <= ? AND end_date >= ?
            """, (user_id, date_str, date_str)).fetchall()
            return [dict(r) for r in rows]

    def get_active_events(self, user_id: int, date: datetime) -> list:
        """Get market events active on a given date."""
        date_str = date.strftime('%Y-%m-%d')
        with self.get_db() as conn:
            rows = conn.execute("""
                SELECT * FROM market_events
                WHERE user_id = ?
                  AND start_date <= ? AND end_date >= ?
            """, (user_id, date_str, date_str)).fetchall()
            return [dict(r) for r in rows]

    def get_campaign_boost(self, product: dict, campaigns: list) -> float:
        """Calculate combined campaign boost for a product."""
        boost = 1.0
        for campaign in campaigns:
            applies = False

            if campaign['campaign_type'] == 'PRODUCT':
                applies = (campaign['target_id'] == product['product_id'])
            elif campaign['campaign_type'] == 'CATEGORY':
                applies = (campaign['target_id'] == product['category_id'])
            elif campaign['campaign_type'] == 'ALL':
                applies = True

            if applies:
                boost *= float(campaign['demand_boost'])

        return boost

    def get_event_boost(self, product: dict, events: list) -> float:
        """Calculate combined event boost for a product."""
        boost = 1.0
        for event in events:
            # Check if product matches event target attributes
            target_attr = event.get('target_attribute')
            target_val = event.get('target_value')

            if target_attr and target_val:
                product_val = product.get(target_attr)
                if product_val and target_val.upper() in str(product_val).upper():
                    boost *= float(event['demand_boost'])

        return boost

    def get_current_stock(self, user_id: int, product_id: int) -> int:
        """Get current stock for a product using FIFO layers."""
        with self.get_db() as conn:
            result = conn.execute("""
                SELECT COALESCE(SUM(quantity_remaining), 0) as stock
                FROM inventory_layers
                WHERE user_id = ? AND product_id = ? AND quantity_remaining > 0
            """, (user_id, product_id)).fetchone()
            return result['stock'] if result else 0

    def get_fifo_cost(self, user_id: int, product_id: int, quantity: int) -> tuple:
        """
        Calculate FIFO cost for selling quantity units.
        Returns (total_cost, layers_consumed) where layers_consumed is a list of (layer_id, qty).
        """
        with self.get_db() as conn:
            layers = conn.execute("""
                SELECT layer_id, quantity_remaining, unit_cost
                FROM inventory_layers
                WHERE user_id = ? AND product_id = ? AND quantity_remaining > 0
                ORDER BY received_date ASC, layer_id ASC
            """, (user_id, product_id)).fetchall()

            total_cost = Decimal('0.00')
            layers_consumed = []
            remaining_to_sell = quantity

            for layer in layers:
                if remaining_to_sell <= 0:
                    break

                take = min(remaining_to_sell, layer['quantity_remaining'])
                cost = Decimal(str(layer['unit_cost'])) * take
                total_cost += cost
                layers_consumed.append((layer['layer_id'], take))
                remaining_to_sell -= take

            return total_cost, layers_consumed

    def consume_inventory(self, conn, user_id: int, product_id: int, layers_consumed: list):
        """Consume inventory from FIFO layers."""
        for layer_id, qty in layers_consumed:
            conn.execute("""
                UPDATE inventory_layers
                SET quantity_remaining = quantity_remaining - ?
                WHERE layer_id = ?
            """, (qty, layer_id))

    def process_sale(
        self,
        conn,
        user_id: int,
        business_id: int,
        product: dict,
        units_sold: int,
        selling_price: Decimal,
        sale_date: datetime,
        cogs: Decimal,
    ):
        """
        Record a sale in the ledger using double-entry accounting.

        Creates:
        - Debit Cash, Credit Sales Revenue (for revenue)
        - Debit COGS, Credit Inventory (for cost)
        """
        if units_sold <= 0:
            return

        revenue = selling_price * units_sold
        transaction_uuid = f"sale-{sale_date.strftime('%Y%m%d')}-{product['product_id']}-{uuid.uuid4().hex[:8]}"
        date_str = sale_date.strftime('%Y-%m-%d')

        # Revenue entry
        conn.execute("""
            INSERT INTO financial_ledger
            (user_id, transaction_date, account, debit, credit, description, transaction_uuid, business_id)
            VALUES (?, ?, 'Cash', ?, 0, ?, ?, ?)
        """, (user_id, date_str, str(revenue), f"Sale of {units_sold} {product['name']}", transaction_uuid, business_id))

        conn.execute("""
            INSERT INTO financial_ledger
            (user_id, transaction_date, account, debit, credit, description, transaction_uuid, business_id)
            VALUES (?, ?, 'Sales Revenue', 0, ?, ?, ?, ?)
        """, (user_id, date_str, str(revenue), f"Sale of {units_sold} {product['name']}", transaction_uuid, business_id))

        # COGS entry
        conn.execute("""
            INSERT INTO financial_ledger
            (user_id, transaction_date, account, debit, credit, description, transaction_uuid, business_id)
            VALUES (?, ?, 'COGS', ?, 0, ?, ?, ?)
        """, (user_id, date_str, str(cogs), f"Cost of {units_sold} {product['name']}", transaction_uuid, business_id))

        conn.execute("""
            INSERT INTO financial_ledger
            (user_id, transaction_date, account, debit, credit, description, transaction_uuid, business_id)
            VALUES (?, ?, 'Inventory', 0, ?, ?, ?, ?)
        """, (user_id, date_str, str(cogs), f"Cost of {units_sold} {product['name']}", transaction_uuid, business_id))

    def process_day(
        self,
        user_id: int,
        business_id: int,
        game_date: datetime,
        start_date: datetime,
        volatility: str,
    ) -> dict:
        """
        Process a single day of gameplay.

        Returns dict with:
        - sales: list of {product_id, units_sold, revenue, cogs}
        - events_started: list of new events
        - deliveries: list of arrived POs
        - bills_paid: list of AP payments
        - expenses: list of recurring expenses applied
        """
        results = {
            'date': game_date.strftime('%Y-%m-%d'),
            'sales': [],
            'events_started': [],
            'deliveries': [],
            'bills_paid': [],
            'expenses': [],
        }

        with self.get_db() as conn:
            # Get products for this business
            products = conn.execute("""
                SELECT p.*, pps.current_price
                FROM products p
                LEFT JOIN player_product_settings pps
                    ON p.product_id = pps.product_id AND pps.user_id = ?
                WHERE p.business_id = ? AND p.status = 'UNLOCKED'
            """, (user_id, business_id)).fetchall()

            # Get business info
            business = conn.execute("""
                SELECT * FROM businesses WHERE business_id = ?
            """, (business_id,)).fetchone()

            # Get active campaigns and events
            campaigns = self.get_active_campaigns(user_id, business_id, game_date)
            events = self.get_active_events(user_id, game_date)

            # Process sales for each product
            for prod_row in products:
                product = dict(prod_row)

                # Get selling price (use player's price or default)
                if product['current_price']:
                    selling_price = Decimal(product['current_price'])
                else:
                    selling_price = Decimal(product['default_price'])

                # Calculate demand
                campaign_boost = self.get_campaign_boost(product, campaigns)
                event_boost = self.get_event_boost(product, events)

                demand = self.calculate_demand(
                    product=product,
                    current_date=game_date,
                    start_date=start_date,
                    player_price=selling_price,
                    campaign_boost=campaign_boost,
                    event_boost=event_boost,
                    volatility=volatility,
                )

                # Limit by stock
                stock = self.get_current_stock(user_id, product['product_id'])
                units_sold = min(demand, stock)

                if units_sold > 0:
                    # Calculate FIFO cost (uses separate connection for read)
                    cogs, layers_consumed = self.get_fifo_cost(
                        user_id, product['product_id'], units_sold
                    )

                    # Consume inventory (pass the current connection)
                    self.consume_inventory(conn, user_id, product['product_id'], layers_consumed)

                    # Record sale in ledger
                    self.process_sale(
                        conn, user_id, business_id, product,
                        units_sold, selling_price, game_date, cogs
                    )

                    revenue = selling_price * units_sold

                    results['sales'].append({
                        'product_id': product['product_id'],
                        'product_name': product['name'],
                        'units_sold': units_sold,
                        'revenue': float(revenue),
                        'cogs': float(cogs),
                        'demand': demand,
                        'stock_remaining': stock - units_sold,
                    })

            # Check for random market events (4% daily chance)
            # Don't trigger events until business is established (day 14+)
            days_elapsed = (game_date - start_date).days
            if days_elapsed >= MIN_DAYS_FOR_EVENTS and random.random() < 0.04:
                new_event = self._trigger_random_event(conn, user_id, business['name'], game_date)
                if new_event:
                    results['events_started'].append(new_event)

            # Process deliveries (POs arriving today)
            deliveries = self._process_deliveries(conn, user_id, business_id, game_date)
            results['deliveries'] = deliveries

            # Process AP payments (bills due today)
            bills = self._process_bills(conn, user_id, business_id, game_date)
            results['bills_paid'] = bills

            # Process recurring expenses (1st of month)
            if game_date.day == 1:
                expenses = self._process_recurring_expenses(conn, user_id, business_id, game_date)
                results['expenses'] = expenses

            # Update daily sales summary for performance
            self._update_daily_summary(conn, user_id, business_id, game_date, results['sales'])

        return results

    def _trigger_random_event(self, conn, user_id: int, business_name: str, game_date: datetime) -> dict:
        """Trigger a random market event for this user."""
        events_for_business = MARKET_EVENTS.get(business_name, [])
        if not events_for_business:
            return None

        event_template = random.choice(events_for_business)
        start_date = game_date.strftime('%Y-%m-%d')
        end_date = (game_date + timedelta(days=event_template['duration_days'])).strftime('%Y-%m-%d')

        # Determine target attribute and value
        target_attr = None
        target_val = None
        for attr, val in event_template['target_attributes'].items():
            target_attr = attr
            target_val = val
            break

        conn.execute("""
            INSERT INTO market_events
            (user_id, name, description, target_attribute, target_value, demand_boost, start_date, end_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id, event_template['name'], event_template['description'],
            target_attr, target_val, event_template['boost'], start_date, end_date
        ))

        return {
            'name': event_template['name'],
            'description': event_template['description'],
            'end_date': end_date,
        }

    def _process_deliveries(self, conn, user_id: int, business_id: int, game_date: datetime) -> list:
        """Process purchase orders arriving today."""
        date_str = game_date.strftime('%Y-%m-%d')
        deliveries = []

        # Find POs arriving today (join with vendors to get business_id filter)
        pos = conn.execute("""
            SELECT po.*, v.name as vendor_name, v.payment_terms
            FROM purchase_orders po
            JOIN vendors v ON po.vendor_id = v.vendor_id
            WHERE po.user_id = ?
              AND v.business_id = ?
              AND po.expected_arrival_date = ?
              AND po.status = 'IN_TRANSIT'
        """, (user_id, business_id, date_str)).fetchall()

        for po in pos:
            po_dict = dict(po)
            order_id = po['order_id']

            # Mark as delivered
            conn.execute("""
                UPDATE purchase_orders SET status = 'DELIVERED', actual_arrival_date = ?
                WHERE order_id = ?
            """, (date_str, order_id))

            # Get order items
            items = conn.execute("""
                SELECT poi.*, p.name as product_name
                FROM purchase_order_items poi
                JOIN products p ON poi.product_id = p.product_id
                WHERE poi.order_id = ?
            """, (order_id,)).fetchall()

            # Add inventory layers (FIFO)
            for item in items:
                conn.execute("""
                    INSERT INTO inventory_layers
                    (user_id, product_id, quantity_received, quantity_remaining, unit_cost, received_date, purchase_order_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id, item['product_id'], item['quantity'], item['quantity'],
                    item['unit_cost'], date_str, order_id
                ))

            # Create AP entry (bill due based on payment terms)
            payment_terms = po['payment_terms'] or 'NET30'
            days = int(payment_terms.replace('NET', ''))
            due_date = (game_date + timedelta(days=days)).strftime('%Y-%m-%d')

            conn.execute("""
                INSERT INTO accounts_payable
                (user_id, vendor_id, purchase_order_id, amount_due, creation_date, due_date, status)
                VALUES (?, ?, ?, ?, ?, ?, 'UNPAID')
            """, (user_id, po['vendor_id'], order_id, po['total_amount'], date_str, due_date))

            # Record in ledger: Debit Inventory, Credit AP
            transaction_uuid = f"po-{order_id}-received"
            conn.execute("""
                INSERT INTO financial_ledger
                (user_id, transaction_date, account, debit, credit, description, transaction_uuid, business_id)
                VALUES (?, ?, 'Inventory', ?, 0, ?, ?, ?)
            """, (user_id, date_str, po['total_amount'], f"PO #{order_id} from {po['vendor_name']}", transaction_uuid, business_id))

            conn.execute("""
                INSERT INTO financial_ledger
                (user_id, transaction_date, account, debit, credit, description, transaction_uuid, business_id)
                VALUES (?, ?, 'Accounts Payable', 0, ?, ?, ?, ?)
            """, (user_id, date_str, po['total_amount'], f"PO #{order_id} from {po['vendor_name']}", transaction_uuid, business_id))

            deliveries.append({
                'order_id': order_id,
                'vendor': po['vendor_name'],
                'total': float(po['total_amount']),
                'items': [dict(i) for i in items],
            })

        return deliveries

    def _process_bills(self, conn, user_id: int, business_id: int, game_date: datetime) -> list:
        """Process AP bills due today."""
        date_str = game_date.strftime('%Y-%m-%d')
        bills_paid = []

        # Join with vendors to filter by business_id
        bills = conn.execute("""
            SELECT ap.*, v.name as vendor_name
            FROM accounts_payable ap
            JOIN vendors v ON ap.vendor_id = v.vendor_id
            WHERE ap.user_id = ?
              AND v.business_id = ?
              AND ap.due_date = ? AND ap.status = 'UNPAID'
        """, (user_id, business_id, date_str)).fetchall()

        for bill in bills:
            payable_id = bill['payable_id']

            # Mark as paid
            conn.execute("""
                UPDATE accounts_payable SET status = 'PAID', paid_date = ?
                WHERE payable_id = ?
            """, (date_str, payable_id))

            # Record in ledger: Debit AP, Credit Cash
            transaction_uuid = f"ap-{payable_id}-paid"
            conn.execute("""
                INSERT INTO financial_ledger
                (user_id, transaction_date, account, debit, credit, description, transaction_uuid, business_id)
                VALUES (?, ?, 'Accounts Payable', ?, 0, ?, ?, ?)
            """, (user_id, date_str, bill['amount_due'], f"Payment to {bill['vendor_name']}", transaction_uuid, business_id))

            conn.execute("""
                INSERT INTO financial_ledger
                (user_id, transaction_date, account, debit, credit, description, transaction_uuid, business_id)
                VALUES (?, ?, 'Cash', 0, ?, ?, ?, ?)
            """, (user_id, date_str, bill['amount_due'], f"Payment to {bill['vendor_name']}", transaction_uuid, business_id))

            bills_paid.append({
                'payable_id': payable_id,
                'vendor': bill['vendor_name'],
                'amount': float(bill['amount_due']),
            })

        return bills_paid

    def _process_recurring_expenses(self, conn, user_id: int, business_id: int, game_date: datetime) -> list:
        """Process recurring expenses on the 1st of the month."""
        date_str = game_date.strftime('%Y-%m-%d')
        expenses_applied = []

        # Get recurring expenses for this user (frequency check: MONTHLY and due on 1st)
        # Note: recurring_expenses doesn't have is_active, just check frequency and due_day
        expenses = conn.execute("""
            SELECT * FROM recurring_expenses
            WHERE user_id = ? AND frequency = 'MONTHLY' AND due_day_of_month = 1
        """, (user_id,)).fetchall()

        for expense in expenses:
            transaction_uuid = f"expense-{date_str}-{expense['expense_id']}"

            # Record in ledger: Debit Expense, Credit Cash
            # Use 'Operating Expenses' as account name since category_id is just an ID
            expense_account = 'Operating Expenses'

            conn.execute("""
                INSERT INTO financial_ledger
                (user_id, transaction_date, account, debit, credit, description, transaction_uuid, business_id)
                VALUES (?, ?, ?, ?, 0, ?, ?, ?)
            """, (user_id, date_str, expense_account, expense['amount'], expense['description'], transaction_uuid, business_id))

            conn.execute("""
                INSERT INTO financial_ledger
                (user_id, transaction_date, account, debit, credit, description, transaction_uuid, business_id)
                VALUES (?, ?, 'Cash', 0, ?, ?, ?, ?)
            """, (user_id, date_str, expense['amount'], expense['description'], transaction_uuid, business_id))

            expenses_applied.append({
                'name': expense['description'],
                'amount': float(expense['amount']),
            })

        return expenses_applied

    def _update_daily_summary(self, conn, user_id: int, business_id: int, game_date: datetime, sales: list):
        """Update daily sales summary for performance queries."""
        date_str = game_date.strftime('%Y-%m-%d')

        for sale in sales:
            conn.execute("""
                INSERT INTO daily_sales_summary
                (user_id, product_id, sale_date, units_sold, revenue, cogs)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                user_id, sale['product_id'], date_str,
                sale['units_sold'], str(sale['revenue']), str(sale['cogs'])
            ))

    def advance_time(self, user_id: int, business_id: int, days: int) -> list:
        """
        Advance game time by the specified number of days.

        Returns a list of daily results for the event log.
        """
        state = self.get_game_state(user_id, business_id)
        current_date = datetime.strptime(state['current_game_date'][:10], '%Y-%m-%d')
        # start_date may include time if from created_at, so just take first 10 chars
        start_date = datetime.strptime(state['start_date'][:10], '%Y-%m-%d')

        # Get business volatility
        with self.get_db() as conn:
            business = conn.execute("""
                SELECT volatility FROM businesses WHERE business_id = ?
            """, (business_id,)).fetchone()
            volatility = business['volatility'] if business else 'MEDIUM'

        all_results = []

        for day_offset in range(days):
            game_date = current_date + timedelta(days=day_offset + 1)
            day_result = self.process_day(
                user_id, business_id, game_date, start_date, volatility
            )
            all_results.append(day_result)

        # Update game state with new date
        new_date = (current_date + timedelta(days=days)).strftime('%Y-%m-%d')
        with self.get_db() as conn:
            conn.execute("""
                UPDATE game_state SET current_date = ?
                WHERE user_id = ? AND business_id = ?
            """, (new_date, user_id, business_id))

        return all_results

    def get_cash_balance(self, user_id: int, business_id: int = None) -> Decimal:
        """Get current cash balance from ledger."""
        with self.get_db() as conn:
            query = """
                SELECT
                    COALESCE(SUM(debit), 0) - COALESCE(SUM(credit), 0) as balance
                FROM financial_ledger
                WHERE user_id = ? AND account = 'Cash'
            """
            params = [user_id]

            if business_id:
                query += " AND business_id = ?"
                params.append(business_id)

            result = conn.execute(query, params).fetchone()
            return Decimal(str(result['balance'])) if result else Decimal('0.00')

    def get_inventory_value(self, user_id: int, business_id: int = None) -> Decimal:
        """Get total inventory value from FIFO layers."""
        with self.get_db() as conn:
            query = """
                SELECT COALESCE(SUM(quantity_remaining * unit_cost), 0) as value
                FROM inventory_layers il
                JOIN products p ON il.product_id = p.product_id
                WHERE il.user_id = ? AND il.quantity_remaining > 0
            """
            params = [user_id]

            if business_id:
                query += " AND p.business_id = ?"
                params.append(business_id)

            result = conn.execute(query, params).fetchone()
            return Decimal(str(result['value'])) if result else Decimal('0.00')

    def get_30_day_sales(self, user_id: int, business_id: int) -> list:
        """Get last 30 days of sales for chart."""
        state = self.get_game_state(user_id, business_id)
        current_date = datetime.strptime(state['current_game_date'], '%Y-%m-%d')
        start_of_range = (current_date - timedelta(days=29)).strftime('%Y-%m-%d')

        with self.get_db() as conn:
            rows = conn.execute("""
                SELECT sale_date, SUM(revenue) as total_revenue, SUM(units_sold) as total_units
                FROM daily_sales_summary
                WHERE user_id = ? AND business_id = ?
                  AND sale_date >= ?
                GROUP BY sale_date
                ORDER BY sale_date
            """, (user_id, business_id, start_of_range)).fetchall()

            return [dict(r) for r in rows]
