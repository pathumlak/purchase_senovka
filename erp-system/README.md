# SENOVKA ERP System

Comprehensive Django ERP solution for inventory, customer pricing, billing, cheque settlements, booking orders, analytics dashboard, system logs, and report exports.

This document is written in project-proposal style so it can be used directly for academic or business submission.

## 1. Project Summary

SENOVKA ERP is a modular web-based enterprise resource planning system developed with Django. It centralizes operations across:

1. Production and inventory management
2. Customer management and customer-specific pricing
3. Billing lifecycle (cash, credit, cheque)
4. Booking order workflow (pending to completed bill conversion)
5. Cheque settlement tracking via sold-goods records
6. Dashboard alerts, notifications, and unified activity logs
7. Excel/PDF reporting and printable documents

## 2. Business Problem Solved

The system addresses common SME operational problems:

1. Manual stock and product tracking errors
2. No centralized customer and pricing control
3. Slow billing operations and poor visibility of payment types
4. Lack of cheque maturity and booking send-date monitoring
5. Scattered operational events with no unified log view
6. Difficulty in generating structured reports for management

## 3. Objectives

1. Digitize end-to-end inventory and sales operations
2. Reduce billing and settlement mistakes with validations
3. Improve operational visibility with dashboards and alerts
4. Provide downloadable, filterable management reports
5. Keep implementation simple, maintainable, and extensible

## 4. Technology Stack

1. Backend: Django
2. Database: SQLite (default, configurable)
3. Frontend: Django Templates + Tailwind CSS
4. Reporting:
   1. PDF generation: xhtml2pdf
   2. Excel generation: openpyxl
5. Language: Python

## 5. Current Project Structure

High-level structure (functional view):

1. Core project
   1. manage.py
   2. erp/
      1. settings.py
      2. urls.py
      3. views.py (Home dashboard + Logs)
      4. asgi.py
      5. wsgi.py
2. Domain apps
   1. apps/production/
      1. models.py
      2. views.py
      3. forms.py
      4. urls.py
      5. migrations/
   2. apps/customers/
      1. models.py
      2. views.py
      3. forms.py
      4. urls.py
      5. migrations/
   3. apps/billing/
      1. models.py
      2. views.py
      3. forms.py
      4. urls.py
      5. migrations/
3. UI and assets
   1. templates/
      1. base.html
      2. home.html
      3. billing/ (bills, sold goods, booking orders, report templates)
      4. production/ (categories and products)
      5. customers/ (customer list and pricing list)
      6. logs/ (all logs page and PDF template)
   2. static/
      1. css/
      2. js/
      3. audio/
4. Configuration and dependencies
   1. requirements.txt
   2. tailwind.config.js
   3. db.sqlite3

## 6. Module-Wise Functionalities

### 6.1 Home Dashboard and Notifications

Route: /

Functionalities:

1. KPI cards:
   1. Total products
   2. Total customers
   3. Bills created today
   4. Monthly revenue
2. Inventory health:
   1. Low stock count
   2. Critical stock count
   3. Out-of-stock count
3. Recent tasks stream:
   1. Recent bills
   2. Recent cheque settlements
   3. Newly created customers
4. Smart alerts:
   1. Low stock alerts
   2. Upcoming cheque maturity alerts
   3. Pending booking send-date alerts
5. In-browser notification interaction with clear-for-today behavior

### 6.2 Production Module

Routes: /production/ and /production/products/

Category management:

1. Create, update, delete product categories
2. Filter by category name and product availability
3. Export filtered category report:
   1. PDF
   2. Excel
4. Protected delete handling for categories used in billing

Product management:

1. Create, update, delete products
2. Product attributes:
   1. Name
   2. Category
   3. Size
   4. Quantity
   5. Description
3. Attach customer-specific prices directly from product forms
4. Table filtering by category and stock in frontend
5. Protected delete handling for products used in billing records

### 6.3 Customers Module

Routes: /customers/ and /customers/pricing/

Customer management:

1. Create, update, delete customers
2. Customer balance tracking
3. Protected delete handling when linked with bills

Customer pricing management:

1. Create/update/delete customer-product price mappings
2. Enforce one price per customer-product pair
3. API endpoint to fetch customer-specific product price

### 6.4 Billing Module

Route group: /billing/

All Bills:

1. List all bills with pagination (10 per page)
2. Filters:
   1. Period (all/daily/weekly/monthly)
   2. Customer
   3. Payment method
   4. Status
   5. Search by order/customer
3. Export filtered list:
   1. PDF
   2. Excel
4. Bill detail and invoice PDF/print support

Cash Sales and Cheque Sales:

1. Dedicated views by payment method
2. Advanced filters (period/customer/category/product/customer-pricing)
3. Export filtered results to PDF and Excel

Bill creation:

1. Validates customer and product selection
2. Uses customer-specific product availability/pricing
3. Computes totals, discount, net value, paid amounts
4. Supports payment methods:
   1. Cash
   2. Credit
   3. Cheque
5. Updates stock on bill completion
6. Updates customer balance based on payment method rules

Sold Goods (Cheque Settlement):

1. List with pagination (10 per page)
2. Filters:
   1. Customer
   2. Status
   3. Maturity date range
   4. Search (customer, bill, bank, branch, account)
3. Export filtered results:
   1. PDF
   2. Excel
4. Settlement logic updates customer balance deduction and extra amount

Booking Orders:

1. Pending/completed order workflow
2. List with pagination (10 per page)
3. Filters:
   1. Status
   2. Customer
   3. Payment method
   4. Send-date range
   5. Search (order/customer)
4. Export filtered list:
   1. PDF
   2. Excel
5. Complete action converts booking order into finalized bill
6. Stock and balance adjustments executed atomically
7. Per-row bill print action for completed booking orders

### 6.5 Unified Logs Module

Route: /logs/

Functionalities:

1. Consolidates events from:
   1. Bills
   2. Settlements
   3. Customers
   4. Booking orders
   5. Alert events
2. Category filtering
3. Pagination (15 per page)
4. Export filtered logs:
   1. PDF
   2. Excel
5. Newest activity first ordering

## 7. Data Model Overview

Core entities and relationships:

1. ProductCategory -> Product (1 to many)
2. Customer -> Bill (1 to many, protected on delete)
3. Bill -> BillItem (1 to many)
4. Product -> BillItem (1 to many, protected on delete)
5. Customer + Product -> CustomerProductPrice (unique pair)
6. SoldGoods links Customer and Bill (both protected)
7. BookingOrder -> BookingOrderItem (1 to many)
8. BookingOrder optionally links completed Bill

## 8. Business Rules and Validations

1. Auto-generated sequential IDs:
   1. Bill IDs (BILL-xxxx)
   2. Booking IDs (BOOK-xxxx)
2. Stock cannot go negative during billing completion
3. Product line quantities must be positive
4. Discount and payment numeric validation
5. Product access constrained by customer-price mapping in billing flows
6. Protected deletes return user-friendly error messages for referenced entities

## 9. Reporting and Export Capabilities

Implemented export surfaces:

1. All Bills (PDF/Excel)
2. Cash Sales (PDF/Excel)
3. Cheque Sales (PDF/Excel)
4. Sold Goods (PDF/Excel)
5. Booking Orders (PDF/Excel)
6. Production Categories (PDF/Excel)
7. Unified Logs (PDF/Excel)

## 10. Security and Operational Notes

1. CSRF protection enabled via Django middleware
2. Protected foreign keys prevent accidental data loss
3. SQLite is used by default for local development
4. DEBUG is currently enabled and should be disabled in production
5. SECRET_KEY should be externalized for production deployment

## 11. Setup Instructions

1. Clone project and move into folder
2. Create virtual environment
3. Install dependencies
4. Apply migrations
5. Run server

Windows example:

1. python -m venv .venv
2. .venv\Scripts\activate
3. pip install -r requirements.txt
4. python manage.py migrate
5. python manage.py runserver

Application URL:

1. http://127.0.0.1:8000/

## 12. Dependencies

Core packages in requirements.txt include:

1. Django
2. djangorestframework
3. django-tailwind
4. psycopg2-binary
5. xhtml2pdf
6. openpyxl

## 13. Suggested Proposal Section Mapping

You can map this README directly into proposal chapters:

1. Introduction: Sections 1 and 2
2. Objectives: Section 3
3. System Design and Architecture: Sections 4, 5, and 7
4. Functional Requirements: Section 6
5. Business Rules and Validation: Section 8
6. Reporting and Outputs: Section 9
7. Deployment and Environment: Sections 10 and 11
8. Tools and Libraries: Section 12

## 14. Future Enhancements

1. Authentication and role-based access control
2. Audit history model for immutable event tracking
3. REST API layer for external integrations
4. Advanced analytics charts and forecasting
5. Scheduled report emails
6. PostgreSQL production configuration and backups

(Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned) ; (& c:\Users\Laksh\Desktop\senovak\erp-system\.venv\Scripts\Activate.ps1)