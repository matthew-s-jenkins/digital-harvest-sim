# Digital Harvest - Business Simulation Game

[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org/)
[![React](https://img.shields.io/badge/React-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://reactjs.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)

> A business simulation game built on real-world accounting principles. Run a keyboard shop, tech store, or vertical farm while learning inventory management, supply chain logistics, and financial decision-making.

---

## Quick Start

### Windows
Double-click `START_WINDOWS.bat`

### Mac/Linux
```bash
chmod +x START_MAC.command
./START_MAC.command
```

That's it! The game opens automatically in your browser at `http://127.0.0.1:5002`

---

## About the Game

**Digital Harvest** is an interactive business simulation where you manage a retail operation with real accounting accuracy. Choose from three business types:

- **Clicky Clack Supply** (Keyboards) - Medium volatility, driven by streamers and enthusiast trends
- **Silicon Orchard** (Tech) - High volatility, crypto booms and tech news create wild swings
- **Heritage Seeds** (Vertical Farm) - Low volatility, steady and reliable

### Core Gameplay

1. **Purchase Inventory** - Order products from vendors with different prices, minimums, and lead times
2. **Watch Sales Happen** - Customers buy based on demand patterns, seasonality, and your pricing
3. **Manage Cash Flow** - Pay bills on time, track expenses, and grow your business
4. **Advance Time** - Each day brings new sales, deliveries, and challenges

### What Makes It Realistic

- **Double-Entry Accounting**: Every transaction creates balanced debit/credit entries
- **FIFO Inventory Costing**: Oldest inventory sells first, just like real businesses
- **Lead Time Management**: Orders take time to arrive based on vendor distance
- **Bill Payment**: Pay vendors on time or face cash flow challenges

---

## Features

### Multiple Businesses
Run up to 3 businesses simultaneously - one of each type. Switch between them anytime.

### Automatic Backups
Your data is automatically backed up to `Documents/DigitalHarvest_Data`:
- Latest backup always available
- Daily backups kept for 3 days
- Weekly backups kept for 4 weeks

### Portable Database
Uses SQLite - no database server required. Your entire game is in a single file that moves with the project.

### Clean Web Interface
Modern React + Tailwind CSS interface with:
- Real-time financial dashboard
- Inventory management
- Vendor ordering with live minimum order warnings
- Toast notifications instead of browser alerts
- Dark/light theme support

---

## Requirements

- **Python 3.8+** ([Download](https://www.python.org/downloads/))
- A modern web browser

Python packages are installed automatically on first run, or manually with:
```bash
pip install -r requirements.txt
```

---

## Project Structure

```
digital-harvest/
├── start.py                 # Main launcher (handles setup, backups, migrations)
├── START_WINDOWS.bat        # Windows double-click launcher
├── START_MAC.command        # Mac double-click launcher
│
├── src/
│   ├── api.py              # Flask REST API (runs on port 8888)
│   ├── game_engine.py      # Core game simulation engine
│   ├── setup_sqlite.py     # Database initialization
│   ├── seed_data.py        # Products, vendors, and initial data
│   └── migration_runner.py # Schema migration system
│
├── game.html               # Main game interface (React)
├── login.html              # User authentication
├── register.html           # New user registration
├── select-business.html    # Business type selection
├── setup.html              # Initial account setup
└── themes.js               # Dark/light theme support
```

---

## Technical Details

### Database Schema

The game uses a normalized SQLite database with:

| Table | Purpose |
|-------|---------|
| `users` | Player accounts with secure password hashing |
| `businesses` | Three business types with unique products |
| `game_state` | Per-user, per-business game progress |
| `products` | Product catalog with pricing and demand curves |
| `vendors` | Suppliers with minimums, lead times, pricing |
| `inventory_layers` | FIFO cost tracking for accurate COGS |
| `financial_ledger` | Double-entry accounting transactions |
| `purchase_orders` | Order tracking with delivery dates |
| `accounts_payable` | Bills and payment status |

### API Endpoints

All endpoints use `/api/` prefix and require authentication (except register/login):

- `POST /api/register` - Create account
- `POST /api/login` - Authenticate
- `GET /api/game/state` - Current game state
- `POST /api/game/start` - Start new game for business
- `POST /api/game/advance_time` - Progress simulation
- `POST /api/game/purchase_order` - Create vendor order
- `GET /api/game/financials` - P&L and balance sheet

---

## Development

### Running in Debug Mode

```bash
cd src
python api.py
```

The API runs with Flask debug mode for development.

### Database Reset

Delete `src/data/digitalharvest.db` and restart. A fresh database will be created.

### Migrations

Schema changes are handled automatically via `migration_runner.py`. Migration files in `migrations/schema/` are applied in order on startup.

---

## Background

This project started as a data analysis tool - I wanted to generate realistic business data for Power BI dashboards. But to make the data meaningful, the underlying simulation had to be accurate: proper inventory tracking, cost accounting, and double-entry bookkeeping.

The result is a game that teaches business principles through hands-on experience while generating data realistic enough for actual analysis.

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

**Built with Python, Flask, React, and SQLite**
