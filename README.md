# Trio Snacks — Snacks Shop Website & Cloud POS System

A modern, responsive Snacks Shop Website with an integrated Point-of-Sale (POS) Billing & Invoice System built with Python Flask, SQLAlchemy (SQLite locally + PostgreSQL on Vercel), ReportLab PDF generation, and vanilla JavaScript.

## Key Features

- **Public Storefront (`/` & `/menu`)**:
  - Branded Hero section with store highlights and active promotional offers.
  - Interactive Menu catalog with category filters (`Bread Omelette`, `Sixty Five (65)`, `Sandwich`, `Bakery`, `Drinks`, `Snacks`) and instant search.
- **Cloud POS Billing Terminal (`/billing`)**:
  - Split-pane POS interface optimized for desktop, tablet, and mobile.
  - Real-time session cart with quantity controls, optional Customer Name & Phone capture, configurable discount, and synchronized Tax/GST calculations.
  - Keyboard-wedge USB barcode scanner integration (`barcode.js`).
  - Bilingual POS toggle (**English** + **தமிழ் / Tamil**) and global **Dark Mode**.
  - Post-order completion modal with 1-click **PDF Invoice Download** and receipt view.
- **Orders & Invoice History (`/orders` & `/orders/<id>`)**:
  - Filter transactions by `Today`, `Last 7 Days`, `Last 30 Days`, or `All Time`.
  - Print-ready A4 PDF invoices generated dynamically via ReportLab.
- **Admin Portal (`/admin/dashboard`, `/admin/products`, `/admin/offers`, `/admin/settings`)**:
  - Today's revenue, all-time revenue, top-selling snacks breakdown, and recent invoices.
  - Full CRUD management for menu products (with safe soft-archiving for previously billed items) and promotional offers.
  - Store branding, logo, address, phone, tax rate, GST rate, and invoice footer configuration.

## Quick Local Setup

1. **Create and activate a virtual environment**:
   ```bash
   python3 -m venv venv
   # Linux / macOS:
   source venv/bin/activate
   # Windows (PowerShell / CMD):
   venv\Scripts\activate
   ```
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Run the application**:
   ```bash
   python app.py
   ```
4. **Open in browser**:
   - URL: `http://localhost:5000`
   - Default Admin login: `admin` / `admin123`
   - Default Cashier login: `cashier` / `cashier123`

## Vercel Deployment

See `VERCEL_DEPLOY.md` and `.env.example` for step-by-step instructions to deploy on Vercel with PostgreSQL (Neon, Supabase, or Vercel Postgres).
