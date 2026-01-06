"""
Migration 009: Add start_date column to game_state

Tracks the in-game date when the business was started (for maturity calculation).
For existing games, we'll calculate start_date from the earliest ledger entry.
"""

def run(conn):
    """Run the migration."""
    cursor = conn.cursor()

    # Check if column already exists
    cursor.execute("PRAGMA table_info(game_state)")
    columns = [row[1] for row in cursor.fetchall()]

    if 'start_date' in columns:
        return True  # Already migrated

    # Add start_date column
    cursor.execute("ALTER TABLE game_state ADD COLUMN start_date TEXT")

    # For existing games, calculate start_date from the earliest ledger entry
    # or fall back to current_date minus some reasonable estimate
    cursor.execute("""
        UPDATE game_state
        SET start_date = (
            SELECT MIN(date(transaction_date))
            FROM financial_ledger
            WHERE financial_ledger.user_id = game_state.user_id
        )
        WHERE start_date IS NULL
    """)

    # For any remaining NULL values, use current_date as start_date
    cursor.execute("""
        UPDATE game_state
        SET start_date = current_date
        WHERE start_date IS NULL
    """)

    conn.commit()
    return True
