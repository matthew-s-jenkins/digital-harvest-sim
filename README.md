# Digital Harvest - Accounting-Based Business Simulator

[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white)](https://www.mysql.com/)
[![React](https://img.shields.io/badge/React-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://reactjs.org/)
[![Power BI](https://img.shields.io/badge/Power%20BI-F2C811?style=for-the-badge&logo=powerbi&logoColor=black)](https://powerbi.microsoft.com/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)

> A sophisticated business simulation engine built on real-world accounting principles, providing an interactive platform for strategic decision-making and financial analysis.

---

## 📋 Table of Contents

- [About the Project](#about-the-project)
- [Demo](#demo)
- [Core Features](#core-features)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Running the Application](#running-the-application)
- [Dashboard & Analytics](#dashboard--analytics)
- [Database Architecture](#database-architecture)
- [Project Structure](#project-structure)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

---

## 🎯 About the Project

**Digital Harvest** is an interactive business simulation engine that models a retail business with **real-world accounting accuracy**. Unlike typical business games, this simulator maintains a complete **double-entry accounting system**, tracking every transaction through a financial ledger that follows GAAP principles.

### Why I Built This

During my time as a Data Analyst at High Life Enterprises, I had access to rich sales data that revealed fascinating patterns - seasonal trends, weekly fluctuations, the impact of inventory decisions on profitability. I could build SQL queries and Power BI dashboards to analyze this data, but I wanted to take it further: what if I could generate that same kind of data on demand?

The challenge was to create a simulation that produced realistic sales data I could analyze in Power BI, just like I did with real retail data. But to make the data meaningful, the underlying business model had to be accurate - proper inventory tracking, cost accounting, and double-entry bookkeeping. I couldn't fake the numbers; the simulation needed to work like a real business.

Digital Harvest solves this by modeling every aspect of a retail operation:
- **Demand simulation** with seasonal trends, weekly patterns, and random market events
- **Inventory management** using perpetual inventory accounting
- **Procurement decisions** with multiple vendors, lead times, and shipping costs
- **Financial tracking** through a complete double-entry ledger system

The result is a platform that generates authentic business data for analysis while teaching supply chain and financial management principles.

### What It Does

The project creates a "digital twin" of a retail business, allowing users to:
- Make strategic decisions about inventory purchasing, pricing, and marketing
- See the immediate financial impact through real-time P&L and balance sheet updates
- Analyze trends using Power BI dashboards connected to the live MySQL database
- Understand the connection between operations (sales, inventory, procurement) and profitability
- Learn business principles through hands-on experimentation

### Technical Highlights

- **Double-Entry Accounting**: Every transaction creates balanced DR/CR entries following GAAP principles
- **Perpetual Inventory System**: Real-time quantity tracking with FIFO cost accounting
- **Demand Modeling**: Sales engine with configurable trends, seasonality, and market events
- **Power BI Integration**: Normalized database schema designed for direct BI connectivity
- **Stateless API Architecture**: Flask REST API enables both web and terminal interfaces

**Explore the Stories:** I've documented interesting scenarios and discoveries from the simulation [here](https://matthew-s-jenkins.github.io/digital-harvest-sim/stories/index.html).

---

## 🎬 Demo

### Interactive Web Interface

![Business UI Demo](screenshots/Business_UI.gif)

*Real-time inventory management, supplier negotiations, marketing campaigns, and financial tracking—all in one intuitive dashboard.*

---

## Technical Challenges Solved

### 1. Realistic Demand Modeling

Creating authentic sales patterns required modeling multiple layers of variability:

- **Long-term growth trends**: Gradual business expansion over time
- **Seasonal patterns**: Products sell differently in summer vs. winter
- **Weekly fluctuations**: Weekend vs. weekday shopping behaviors
- **Random market events**: Temporary boosts to specific product categories

The demand engine combines these factors using weighted algorithms that mirror real retail patterns I observed while working with actual sales data. This produces data realistic enough for meaningful Power BI analysis.

### 2. Perpetual Inventory with FIFO Costing

Tracking inventory value requires knowing not just quantity, but the cost of each unit sold. I implemented:

- **FIFO (First-In, First-Out) accounting**: Oldest inventory sells first
- **Layered cost tracking**: Each purchase creates a new cost layer
- **Automated COGS calculation**: Cost of Goods Sold updates automatically as sales occur
- **Inventory valuation**: Real-time inventory value based on remaining cost layers

This matches how real businesses track inventory and ensures accurate profitability calculations.

### 3. Supply Chain Lead Time Management

Orders don't arrive instantly in the real world. The simulation includes:

- **Distance-based lead times**: Further suppliers take longer to ship
- **In-transit order tracking**: Visibility into pending inventory
- **Stockout risk**: Running out of inventory impacts sales
- **Order optimization**: Balancing inventory carrying costs vs. stockout risk

This creates realistic procurement challenges similar to those in actual supply chain management.

### 4. Power BI Database Integration

Designed the MySQL schema specifically for BI connectivity:

- **Star schema patterns**: Fact tables (transactions, sales) with dimension tables (products, vendors)
- **Normalized design**: Minimizes data redundancy while maintaining query performance
- **Date dimensions**: Enables time-based analysis and trends
- **Calculated metrics**: Pre-computed aggregations for dashboard performance

The schema supports complex analytics like vendor ROI analysis, product profitability trends, and inventory turnover rates.

---

## ✨ Core Features

### 💰 Accounting Engine

- **Double-Entry Ledger**: Every transaction creates balanced debit/credit entries
- **Perpetual Inventory System**: Real-time quantity and value tracking
- **Multi-Account Structure**: Cash, Inventory, AP, Revenue, COGS, Operating Expenses
- **Financial Statements**: Auto-generated Balance Sheet and P&L capability

### 📈 Sales & Demand Modeling

- **Realistic Demand Curves**: Long-term trends, seasonality, and weekly patterns
- **Price Sensitivity**: Customer response to pricing changes
- **Market Events**: Random boosts to specific product categories
- **Progressive Unlocks**: New products become available as revenue milestones are reached

### 🚚 Supply Chain Management

- **Multi-Vendor System**: Choose from suppliers with different terms
- **Lead Time Simulation**: Orders arrive after realistic delays
- **Shipping Calculations**: Distance-based and value-based shipping costs
- **Vendor Relationships**: Build rapport to unlock better suppliers

### 💼 Business Operations

- **Marketing Campaigns**: Launch targeted promotions to boost demand
- **Loan System**: Access business financing with realistic APR and terms
- **Recurring Expenses**: Rent, utilities, and operational costs
- **Pricing Control**: Set product prices and see immediate impact on sales

### 🖥️ User Interfaces

- **Web Dashboard**: Multi-page React interface with real-time data
- **Terminal CLI**: Classic command-line interface for purists
- **Power BI Integration**: Connect for advanced analytics and reporting

---

## 🛠️ Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Backend** | Python 3 | Business logic and simulation engine |
| **Database** | MySQL 8.0+ | Persistent data storage with referential integrity |
| **API** | Flask + Flask-CORS | RESTful API for frontend communication |
| **Frontend** | React 17 | Interactive single-page application |
| **Styling** | Tailwind CSS | Modern, responsive UI design |
| **Analytics** | Power BI | Business intelligence dashboards |
| **Libraries** | `mysql-connector-python` | Database connectivity |

---

## 🚀 Getting Started

### Prerequisites

Before running Digital Harvest, ensure you have:

- **Python 3.8+** installed ([Download](https://www.python.org/downloads/))
- **MySQL Server 8.0+** running locally or remotely ([Download](https://dev.mysql.com/downloads/))
- A modern web browser (Chrome, Firefox, or Edge recommended)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/digital-harvest.git
   cd digital-harvest
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure database connection**

   Edit the `DB_CONFIG` dictionary in the following files with your MySQL credentials:
   - `src/setup.py`
   - `src/engine.py`
   - `src/api.py`

   ```python
   DB_CONFIG = {
       'user': 'your_username',
       'password': 'your_password',
       'host': 'localhost',
       'port': 3306
   }
   ```

4. **Initialize the database**

   ⚠️ **Warning**: This will drop and recreate the `digital_harvest` database!

   ```bash
   python src/setup.py
   ```

   You should see output confirming table creation and initial data population.

### Running the Application

#### Option 1: Web Interface (Recommended)

1. **Start the API server**
   ```bash
   python src/api.py
   ```
   You should see: `* Running on http://127.0.0.1:5000`

2. **Open the interface**
   - **Simple**: Double-click `index.html` to open directly in your browser
   - **Server**: For better compatibility, run a local web server:
     ```bash
     python -m http.server 8080
     ```
     Then navigate to: `http://localhost:8080/index.html`

#### Option 2: Terminal Interface

For a classic command-line experience:
```bash
python src/cli.py
```

Follow the on-screen prompts to manage your business day-by-day.

---

## 📊 Dashboard & Analytics

### Web Interface Features

The web dashboard provides six core sections:

1. **📈 Dashboard** - KPIs, sales trends, and inventory breakdown
2. **📦 Inventory** - Stock levels, pricing controls, and product filtering
3. **🚚 Suppliers** - Vendor catalog, ordering interface, and relationship tracking
4. **📢 Marketing** - Campaign launches and performance monitoring
5. **🧾 Expenses** - Recurring cost tracking and analysis
6. **🏦 Bank** - Loan offers and financing options

### Power BI Analytics

The simulation generates data ready for advanced analysis. Connect Power BI to the MySQL database for:

#### 1. Executive Summary Dashboard

![Executive Summary](screenshots/ExecutiveSummary10.02.25.jpg)

**Purpose**: High-level financial health and profitability overview

**Key Visualizations**:
- **KPI Cards**: Cash, AP Due, Gross Profit, Net Profit
- **Monthly P&L**: Revenue vs. Expenses with Net Profit trend
- **Expense Breakdown**: Interactive donut chart of cost structure
- **Working Capital Trend**: Cash balance vs. liabilities over time
- **Date Slicer**: Filter the entire report by time period

#### 2. Supply Chain & Operations Dashboard

![Supply Chain Dashboard](screenshots/SupplyChain&Operations10.02.25.jpg)

**Purpose**: Operational insights connecting physical activities to financial impact

**Key Visualizations**:
- **Accounting Validation**: Real-time verification of double-entry integrity (Total Debits - Total Credits = $0.00)
- **Vendor Scorecard**: Performance metrics (lead time, on-time delivery %)
- **Live Stock Levels**: Current quantity and value for each product
- **Assets & Equity Chart**: Visualization of the accounting equation over time
- **Interactive Slicers**: Filter by vendor or product category

---

## 🗄️ Database Architecture

The database is designed with **normalization** and **referential integrity** in mind:

### Core Tables

| Table | Purpose |
|-------|---------|
| `products` | Product catalog with pricing and demand metadata |
| `product_categories` | Hierarchical categorization (Linear, Tactile, Clicky switches) |
| `vendors` | Supplier information (terms, location, minimums, relationships) |
| `inventory_ledger` | **Perpetual inventory system** - every stock movement with running balances |
| `financial_ledger` | **Double-entry accounting** - debits and credits for all transactions |
| `purchase_orders` | Orders placed to vendors with tracking and status |
| `purchase_order_items` | Line items for each PO |
| `accounts_payable` | Outstanding bills to suppliers |
| `expenses` | Recurring operational costs |
| `loans` | Active financing with repayment schedules |
| `marketing_campaigns` | Active promotions with duration and target |
| `market_events` | Random demand-boosting events |
| `business_state` | Current simulation state (date, cash on hand) |

### Key Design Decisions

- **Immutable Ledgers**: Financial and inventory ledgers are append-only for audit trails
- **Running Balances**: Ledgers include calculated running balances for performance
- **Foreign Keys**: Enforce referential integrity between all related entities
- **Decimal Precision**: All monetary values use `DECIMAL(15,2)` for accuracy
- **Date Tracking**: Every transaction includes timestamps for time-series analysis

---

## 📂 Project Structure

```
digital-harvest/
├── src/                      # Main application code
│   ├── engine.py            # Core simulation engine
│   ├── api.py               # Flask REST API endpoints
│   ├── cli.py               # Terminal interface
│   └── setup.py             # Database initialization and seeding
│
├── index.html               # React-based web interface
├── screenshots/             # Demo images and GIFs
├── oldVersions/             # Archived legacy code
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

---

## 🗺️ Roadmap

### Current Status
- ✅ Full double-entry accounting system
- ✅ Multi-vendor supply chain
- ✅ Marketing campaigns
- ✅ Loan system
- ✅ Market events
- ✅ Web UI with 6 pages
- ✅ Power BI integration

### Planned Enhancements
- [ ] Employee hiring and payroll
- [ ] Customer loyalty system
- [ ] Seasonal inventory planning AI
- [ ] Multi-location expansion
- [ ] Tax accounting and reporting
- [ ] Competitive market simulation
- [ ] Export financial statements (PDF)

---

## 🤝 Contributing

Contributions are welcome! This project is ideal for:
- **Students** learning about databases, accounting, or web development
- **Developers** interested in simulation engines or business logic
- **Educators** looking for teaching tools

### How to Contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📜 License

This project is open source and available under the [MIT License](LICENSE).

---

## 🔗 Related Projects

### Perfect Books - Personal Finance Management

Digital Harvest shares its **double-entry accounting foundation** with [Perfect Books](https://github.com/matthew-s-jenkins/perfect-books), a personal finance application.

**Shared Principles:**
- ✅ Double-entry accounting (Assets = Liabilities + Equity)
- ✅ Immutable financial ledger with transaction UUIDs
- ✅ BI-ready normalized database schema
- ✅ Flask REST API architecture
- ✅ React + Tailwind CSS frontend
- ✅ MySQL database with referential integrity

**Key Differences:**
| Digital Harvest | Perfect Books |
|-----------------|--------------|
| Business simulation | Personal finance tracking |
| Single-user simulation | Multi-user with authentication |
| Simulated sales & purchasing | Real-world transactions |
| Profitability & inventory focus | Budget & expense focus |
| Progressive unlocks & market events | Recurring expenses & loan tracking |

**Why This Matters:**
Both projects prove that **accurate accounting** and **great user experience** can coexist. The shared architecture demonstrates these patterns work for both business and personal finance.

---

## 📧 Contact

**Matthew Jenkins**
- GitHub: [@matthew-s-jenkins](https://github.com/matthew-s-jenkins)
- Project Link: [https://github.com/matthew-s-jenkins/digital-harvest-sim](https://github.com/matthew-s-jenkins/digital-harvest-sim)

---

## 🙏 Acknowledgments

- MySQL for providing a robust relational database
- Flask for making API development straightforward
- React and Tailwind CSS for enabling rapid UI development
- Power BI for powerful data visualization capabilities

---

**Built with Python**
