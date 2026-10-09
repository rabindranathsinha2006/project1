# THE ULTIMATE SHOPPING — Full-Stack E-Commerce Web Application

**THE ULTIMATE SHOPPING** is a commercial-grade, full-stack e-commerce web platform built with **Python Django**, **HTML5/CSS3/JavaScript**, and **SQLite / PostgreSQL**. It delivers a modern, high-performance shopping experience with a deep navy and vibrant orange visual theme, dark mode support, transactional inventory protection, and 14 innovative features.

---

## 🚀 Key Highlights & Innovative Features

1. **AI Shopping Assistant**: Interactive natural language shopping chatbot that parses price ceilings (e.g., *"Find the best smartphone under ₹15,000"*), category keywords, and preferences against real database records. Available as a full-page tool (`/ai-assistant/`) and an omnipresent floating widget on every page.
2. **Atomic Inventory Control**: Uses `django.db.transaction.atomic()` and `select_for_update()` to prevent race conditions and overselling during simultaneous checkout attempts.
3. **Smart Product Recommendations**: Content-aware and bestseller recommendation engines on Home, Product Details, and Cart pages.
4. **Product Comparison Matrix**: Side-by-side comparison of up to 4 items across dynamic technical specifications, ratings, and price points (`/compare/`).
5. **Real-time Price Drop Alerts**: Customers set target price alerts; the system tracks actual database prices and notifies users upon price drops.
6. **Flash Deals & Special Offers**: Deals engine with real discount calculations, % sold progress, and live countdown timers (`/deals/`).
7. **Coupons & Rewards Ledger**: Multi-type coupon validation (percentage / flat off, min cart value, usage caps) and a full loyalty points ledger (1 point earned per ₹10 spent, instant redemption up to 20% order limit).
8. **Visual Order Tracking**: Step-by-step progress timeline: *Order Placed → Confirmed → Packed → Shipped → Out for Delivery → Delivered*, with order cancellation and inventory restoration for eligible orders.
9. **Verified Customer Reviews**: 5-star rating breakdown, verified purchase verification, and average rating aggregation.
10. **Recently Viewed Products**: Preserved per authenticated user and guest session.
11. **Restock Subscriptions**: Out-of-stock notification opt-in when product inventory reaches zero.
12. **Serviceable PIN Code Delivery Estimator**: Instant transit days calculation and COD eligibility check for Indian PIN codes.
13. **Smart Low-Stock Admin Alerts**: Automated notifications when products dip below configurable thresholds.
14. **Custom Admin Analytics Portal**: Executive dashboard at `/admin-portal/` with revenue trends, AOV, order processing, and full CRUD over products, inventory, coupons, and reviews.

---

## 🛠 Technology Stack

* **Backend**: Python 3.14+, Django 6.1
* **Database**: SQLite (default for development), PostgreSQL-compatible via `DATABASE_URL`
* **Frontend**: HTML5, CSS3 Custom Properties (CSS variables), Vanilla JavaScript
* **CSS Framework**: Bootstrap 5.3 + Bootstrap Icons
* **Authentication**: Django PBKDF2 secure password hashing, session management, CSRF protection
* **WSGI Server**: Gunicorn

---

## 📂 Project Structure

```
project 1 new/
├── accounts/               # User profiles, addresses, loyalty rewards, auth views
├── assistant/              # AI Shopping Assistant rule-based NLP query engine
├── cart/                   # Cart, CartItem, guest cart merging, coupons
├── core/                   # Home, deals, static pages, PIN checker API, seed command
│   └── management/
│       └── commands/
│           └── seed_data.py # Automated catalog and demo user seeder
├── orders/                 # Atomic order checkout, tracking, and cancellation
├── portal/                 # Custom administrative analytics and management dashboard
├── products/               # Products, categories, reviews, wishlist, price alerts
├── static/
│   ├── css/main.css        # Navy & orange design system with dark mode
│   └── js/
│       ├── main.js         # Theme toggle, AJAX cart/wishlist, PIN estimator
│       └── assistant.js    # AI assistant chat interface & card rendering
├── templates/              # 28+ clean Jinja/Django HTML templates
│   ├── base.html           # Unified navigation, floating AI widget, footer
│   ├── accounts/           # Login, register, dashboard, addresses, alerts
│   ├── assistant/          # Dedicated AI assistant page
│   ├── cart/               # Cart detail and promo input
│   ├── core/               # Home, deals, about, contact, privacy, terms
│   ├── orders/             # Checkout, confirmation, visual tracking
│   ├── portal/             # Admin dashboard, products, inventory, analytics
│   └── products/           # Catalog list, details, reviews, compare, wishlist
├── manage.py
├── requirements.txt
├── .env.example
└── README.md
```

---

## ⚡ Quick Start & Local Setup

### 1. Prerequisites
Ensure Python 3.10+ is installed on your system.

### 2. Clone / Open Directory
```bash
cd "c:\Users\rabin\OneDrive\Documents\project 1 new"
```

### 3. Install Dependencies
```bash
python -m pip install -r requirements.txt
```

### 4. Run Migrations
```bash
python manage.py migrate
```

### 5. Seed Catalog & Demo Accounts
Run the built-in seed command to populate 14 rich products, categories, reviews, coupons, and demo accounts:
```bash
python manage.py seed_data
```

### 6. Run the Development Server
```bash
python manage.py runserver
```
Visit **http://127.0.0.1:8000/** in your browser.

---

## 🔑 Demo Login Credentials

| Role | Username / Email | Password | Description |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin` / `admin@ultimateshopping.com` | `Admin@12345` | Access to `/admin-portal/` and Django `/admin/` |
| **Customer** | `customer` / `customer@example.com` | `Customer@12345` | Preloaded with addresses, orders, and 250 loyalty points |

*(Note: The login page includes convenient one-click "Auto-Fill" buttons for both demo roles.)*

---

## 🧪 Running Automated Tests

To run the complete automated test suite verifying all 14 core workflows, checkout atomicity, security boundaries, and AI query resolution:
```bash
python manage.py test core
```

---

## 🌐 Complete List of 28 Built Pages

1. **Home Page**: `/`
2. **All Products Catalog**: `/products/`
3. **Category Products**: `/products/category/<slug>/`
4. **Product Details**: `/products/product/<slug>/`
5. **Search Results**: `/search/?q=<query>`
6. **Shopping Cart**: `/cart/`
7. **Wishlist**: `/products/wishlist/`
8. **Product Comparison**: `/products/compare/`
9. **Checkout**: `/orders/checkout/`
10. **Order Confirmation**: `/orders/confirmation/<order_number>/`
11. **Visual Order Tracking**: `/orders/track/<order_number>/`
12. **Sign In**: `/login/`
13. **Sign Up (Registration)**: `/register/`
14. **My Account Dashboard**: `/dashboard/`
15. **My Orders**: `/orders/my-orders/`
16. **Saved Addresses**: `/addresses/`
17. **Product Reviews Full Page**: `/products/product/<slug>/reviews/`
18. **Deals & Offers**: `/deals/`
19. **AI Shopping Assistant Page**: `/assistant/`
20. **Admin Dashboard**: `/admin-portal/`
21. **Admin Product Management**: `/admin-portal/products/`
22. **Admin Inventory & Stock Alerts**: `/admin-portal/inventory/`
23. **Admin Order Fulfillment**: `/admin-portal/orders/`
24. **Admin Sales Analytics**: `/admin-portal/analytics/`
25. **About Us**: `/about/`
26. **Contact & Help Center**: `/contact/`
27. **Privacy Policy**: `/privacy/`
28. **Terms & Conditions**: `/terms/`

---

## ☁️ Deployment Guide (e.g. Render / Production)

1. **Create a Web Service on Render** connected to your repository.
2. **Build Command**:
   ```bash
   pip install -r requirements.txt && python manage.py migrate && python manage.py seed_data && python manage.py collectstatic --no-input
   ```
3. **Start Command**:
   ```bash
   gunicorn ultimate_shop.wsgi:application
   ```
4. **Environment Variables**:
   * `DJANGO_SECRET_KEY`: Set to a strong production secret key.
   * `DJANGO_DEBUG`: `False`
   * `ALLOWED_HOSTS`: `your-app.onrender.com`
   * `DATABASE_URL`: Your Render PostgreSQL database connection string.
