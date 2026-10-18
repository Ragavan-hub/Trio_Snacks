# Vercel Deployment Guide — Trio Snacks

## 1. Prerequisites
- A GitHub account with this project pushed to a repository.
- A Vercel account connected to your GitHub.
- A PostgreSQL database (Vercel Postgres / Neon / Supabase) for persistent production storage.

## 2. Environment Variables Required on Vercel
In your Vercel Project Dashboard, navigate to **Settings → Environment Variables** and add:

| Variable | Description | Example Value |
| :--- | :--- | :--- |
| `SECRET_KEY` | Strong random secret used to sign Flask session cookies | `f8a9c2d1e4b7...` (64-char hex string) |
| `DATABASE_URL` | PostgreSQL connection string (`postgresql://...`) | `postgresql://user:pass@ep-xyz.aws.neon.tech/neondb?sslmode=require` |

> **Note**: Both `postgres://` and `postgresql://` connection strings are automatically normalized in `config.py`. On first boot, `app.py` automatically creates all database tables and seeds the default `admin` (`admin123`) and `cashier` (`cashier123`) accounts, default store settings, promotional offers, and initial menu items if the database is empty.

## 3. Step-by-Step Deployment via GitHub & Vercel
1. Initialize Git and push to GitHub:
   ```bash
   git init
   git add .
   git commit -m "Production-ready Trio Snacks POS & Storefront"
   git branch -M main
   git remote add origin https://github.com/<your-username>/<your-repo>.git
   git push -u origin main
   ```
2. Log in to [Vercel](https://vercel.com/new) and click **Add New... → Project**.
3. Import your GitHub repository.
4. Leave the Build & Output Settings as default (Vercel automatically detects `vercel.json` with `@vercel/python` for `api/index.py` and `@vercel/static` for `static/**`).
5. Expand **Environment Variables** and add `SECRET_KEY` and `DATABASE_URL`.
6. Click **Deploy**.

## 4. Serverless File Upload Considerations
Vercel serverless functions have an ephemeral `/tmp` filesystem. Bundled product images in `static/images/` are served permanently via Vercel's CDN. If you upload new product images through the Admin panel at runtime on Vercel, they are stored in `/tmp` for the lifetime of the warm lambda instance; for permanent runtime uploads on serverless, commit new product images to `static/images/products/` or connect an object storage bucket (e.g., Vercel Blob, Cloudinary, or AWS S3).
