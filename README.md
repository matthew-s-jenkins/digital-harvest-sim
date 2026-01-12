# Digital Harvest - Business Simulation Game

[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org/)
[![React](https://img.shields.io/badge/React-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://reactjs.org/)
[![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)

> A business simulation game built on real-world accounting principles. Run a keyboard shop, tech store, or vertical farm while learning inventory management, supply chain logistics, and financial decision-making.

### 🚀 Live Demo

**[Play Digital Harvest](https://digital-harvest-sim-4cff42aff69b.herokuapp.com/)** - Register an account and start your business empire!

Choose from three unique businesses:
- ⌨️ **Keyp Collected** - Mechanical keyboard switches
- 💻 **Silicon Orchard** - Tech parts and vintage computing
- 🌱 **Heritage Seeds** - Vertical farm produce

*Note: Demo runs on Heroku's free tier with ephemeral storage - data is not persistent and resets when the dyno restarts.*

---

## 📋 Table of Contents

- [About the Game](#-about-the-game)
- [Quick Start](#-quick-start)
- [Core Features](#-core-features)
- [Technical Highlights](#-technical-highlights)
- [Project Structure](#-project-structure)
- [Database Schema](#-database-schema)
- [API Endpoints](#-api-endpoints)
- [Development](#-development)
- [Related Projects](#-related-projects)
- [License](#-license)

---

## 🎯 About the Game

**Digital Harvest** is an interactive business simulation where you manage a retail operation with real accounting accuracy. Unlike typical idle games, this simulator maintains a complete **double-entry accounting system** and **FIFO inventory costing** - the same principles used by real businesses.

### Why I Built This

This project started as a data analysis tool - I wanted to generate realistic business data for Power BI dashboards. But to make the data meaningful, the underlying simulation had to be accurate: proper inventory tracking, cost accounting, and double-entry bookkeeping.

The result is a game that teaches business principles through hands-on experience while generating data realistic enough for actual analysis.

### What You'll Learn

- 📊 **Inventory Management** - Balance stock levels against carrying costs
- 🚚 **Supply Chain Logistics** - Manage lead times and vendor relationships
- 💰 **Cash Flow Management** - Pay bills on time while maintaining liquidity
- 📈 **Financial Analysis** - Read P&L statements and balance sheets

---

## 🚀 Quick Start

### Windows
Double-click `START_WINDOWS.bat`

### Mac/Linux
```bash
chmod +x START_MAC.command
./START_MAC.command
```

That's it! The game opens automatically in your browser at `http://localhost:5002`

### Requirements

- **Python 3.8+** ([Download](https://www.python.org/downloads/))
- A modern web browser

Python packages are installed automatically on first run, or manually with:
```bash
pip install -r requirements.txt
```

---

## ✨ Core Features

### 🏢 Three Business Types

| Business | Volatility | Starting Cash | Theme |
|----------|------------|---------------|-------|
| **Keyp Collected** | Medium | $15,000 | Mechanical keyboard switches - ride enthusiast trends |
| **Silicon Orchard** | High | $25,000 | Tech parts - crypto booms create wild swings |
| **Heritage Seeds** | Low | $10,000 | Vertical farm - steady, reliable growth |

### 🎮 Core Gameplay Loop

1. **Purchase Inventory** - Order products from vendors with different prices, minimums, and lead times
2. **Watch Sales Happen** - Customers buy based on demand patterns, seasonality, and your pricing
3. **Manage Cash Flow** - Pay bills on time, track expenses, and grow your business
4. **Advance Time** - Each day brings new sales, deliveries, and challenges
5. **Restart Anytime** - Made a mistake? Restart any business from scratch without affecting others

### 📦 Realistic Business Mechanics

- **FIFO Inventory Costing** - Oldest inventory sells first, just like real businesses
- **Lead Time Management** - Orders take time to arrive based on vendor distance
- **Minimum Order Requirements** - Meet vendor minimums or pay more per unit
- **Bill Payment** - Pay vendors on time or face cash flow challenges
- **Business Maturity** - New businesses start slow and build customer base over 90 days

### 📊 Analytics Dashboard

Track your business performance with real-time analytics:
- **Revenue & Profit Trends** - Interactive charts showing daily performance
- **Units Sold** - Bar charts tracking sales volume over time
- **Days Supply** - Know exactly how long your inventory will last
- **Product Performance** - See which products are selling and which need attention

### 📈 Three-Statement Financial Reporting

Full professional accounting statements just like real businesses:
- **Income Statement** - Revenue, COGS, Gross Profit, Operating Expenses, Net Income
- **Balance Sheet** - Assets, Liabilities, Equity with A=L+E verification
- **Cash Flow Statement** - Track where your cash comes from and goes
- **Accounts Payable Aging** - See what bills are due and when

### 🔄 Multiple Businesses

Run up to 3 businesses simultaneously - one of each type. Switch between them anytime to manage your empire.

### 💾 Automatic Backups

Your data is automatically backed up to `Documents/DigitalHarvest_Data`:
- ✅ Latest backup always available
- ✅ Daily backups kept for 3 days
- ✅ Weekly backups kept for 4 weeks

---

## 🔧 Technical Highlights

### Double-Entry Accounting
Every transaction creates balanced debit/credit entries in the `financial_ledger` table, maintaining accounting integrity throughout the simulation.

### FIFO Cost Layers
Inventory is tracked in layers via `inventory_layers` table. When sales occur, the oldest layers are consumed first, ensuring accurate Cost of Goods Sold calculations.

### Portable SQLite Database
No database server required - your entire game is in a single file that moves with the project.

### Modern Web Interface
React + Tailwind CSS interface with:
- Real-time financial dashboard
- Toast notifications (no ugly browser alerts)
- Dark/light theme support
- Live minimum order warnings

---

## 📂 Project Structure

```
digital-harvest/
├── start.py                 # Main launcher (handles setup, backups, migrations)
├── START_WINDOWS.bat        # Windows double-click launcher
├── START_MAC.command        # Mac double-click launcher
│
├── src/
│   ├── api.py              # Flask REST API (port 5002)
│   ├── game_engine.py      # Core simulation engine
│   ├── setup_sqlite.py     # Database initialization
│   ├── seed_data.py        # Products, vendors, and initial data
│   └── migration_runner.py # Schema migration system
│
├── game.html               # Main game interface (React)
├── login.html              # User authentication
├── register.html           # New user registration
├── select-business.html    # Business type selection
└── themes.js               # Dark/light theme support
```

---

## 🗄️ Database Schema

The game uses a normalized SQLite database:

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

---

## 🔌 API Endpoints

All endpoints use `/api/` prefix and require authentication (except register/login):

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/register` | POST | Create account |
| `/api/login` | POST | Authenticate |
| `/api/game/businesses` | GET | List available businesses |
| `/api/game/state` | GET | Current game state |
| `/api/game/start` | POST | Start new game for business |
| `/api/game/advance_time` | POST | Progress simulation |
| `/api/game/restart` | POST | Reset business to fresh start |
| `/api/game/purchase_order` | POST | Create vendor order |
| `/api/game/financials` | GET | P&L and balance sheet |

---

## 🛠️ Development

### Running in Debug Mode

```bash
cd src
python api.py
```

The API runs with Flask debug mode on port 5002.

### Database Reset

Delete `src/data/digitalharvest.db` and restart. A fresh database will be created with seed data.

### Migrations

Schema changes are handled automatically via `migration_runner.py`. Migration files are applied in order on startup.

---

## 🔗 Related Projects

### Perfect Books - Personal Finance Management

Digital Harvest shares its **double-entry accounting foundation** with [Perfect Books](https://github.com/matthew-s-jenkins/perfect-books), a personal finance application.

**Shared Architecture:**
- ✅ Double-entry accounting (Assets = Liabilities + Equity)
- ✅ Immutable financial ledger
- ✅ SQLite database with full portability
- ✅ Flask REST API
- ✅ React + Tailwind CSS frontend

---

## 📜 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 📧 Contact

**Matthew Jenkins**
- GitHub: [@matthew-s-jenkins](https://github.com/matthew-s-jenkins)

---

**Built with Python, Flask, React, and SQLite** 🌱
