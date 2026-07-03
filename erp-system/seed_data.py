"""
Seed script — creates sample categories, products, customers, and customer prices.
Run with:  python seed_data.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp.settings')
django.setup()

from decimal import Decimal
from apps.production.models import ProductCategory, Product
from apps.customers.models import Customer, CustomerProductPrice

# ─── counters ─────────────────────────────────────────────────────────────────

created_count = 0
skipped_count = 0


def make_category(name, description=''):
    global created_count, skipped_count
    obj, created = ProductCategory.objects.get_or_create(
        name=name,
        defaults={'description': description},
    )
    if created:
        created_count += 1
        print(f'  [+] Category: {name}')
    else:
        skipped_count += 1
        print(f'  [=] Category exists: {name}')
    return obj


def make_product(name, category, size='', qty=0, description=''):
    global created_count, skipped_count
    obj, created = Product.objects.get_or_create(
        name=name,
        category=category,
        defaults={
            'size':        size,
            'qty':         Decimal(str(qty)),
            'description': description,
        },
    )
    if created:
        created_count += 1
        print(f'  [+] Product: {name} ({category.name})')
    else:
        skipped_count += 1
        print(f'  [=] Product exists: {name} ({category.name})')
    return obj


def make_customer(name, address='', balance=0):
    global created_count, skipped_count
    obj, created = Customer.objects.get_or_create(
        name=name,
        defaults={
            'address': address,
            'balance': Decimal(str(balance)),
        },
    )
    if created:
        created_count += 1
        print(f'  [+] Customer: {name}')
    else:
        skipped_count += 1
        print(f'  [=] Customer exists: {name}')
    return obj


def make_price(customer, product, unit_price):
    global created_count, skipped_count
    obj, created = CustomerProductPrice.objects.get_or_create(
        customer=customer,
        product=product,
        defaults={'unit_price': Decimal(str(unit_price))},
    )
    if created:
        created_count += 1
        print(f'  [+] Price: {customer.name} → {product.name} @ Rs. {unit_price}')
    else:
        skipped_count += 1
        print(f'  [=] Price exists: {customer.name} → {product.name}')
    return obj


# ─── Categories ───────────────────────────────────────────────────────────────

print('\n── Categories ──────────────────────────────────────')

cat_fiber    = make_category('Fiber Products',   'Glass fibre and composite items')
cat_foam     = make_category('Foam Products',    'Foam-based insulation and packaging')
cat_tile     = make_category('Roof Tiles',       'Fibre cement and clay roof tiles')
cat_pipe     = make_category('Pipes & Fittings', 'PVC and HDPE pipes')
cat_hardware = make_category('Hardware',         'General construction hardware')


# ─── Products ─────────────────────────────────────────────────────────────────

print('\n── Products ─────────────────────────────────────────')

# Fiber Products
p_sheet_84  = make_product('Fibre Sheet 8×4',        cat_fiber,    size='8ft × 4ft',    qty=120)
p_sheet_63  = make_product('Fibre Sheet 6×3',        cat_fiber,    size='6ft × 3ft',    qty=85)
p_corr      = make_product('Corrugated Fibre Panel', cat_fiber,    size='10ft × 3ft',   qty=200)
p_flat_fp   = make_product('Flat Fibre Panel',       cat_fiber,    size='8ft × 4ft',    qty=60)
p_cement_bd = make_product('Fibre Cement Board',     cat_fiber,    size='12mm thick',   qty=45)

# Foam Products
p_foam_50   = make_product('Foam Roll 50mm',         cat_foam,     size='50mm × 1m',    qty=300)
p_foam_25   = make_product('Foam Roll 25mm',         cat_foam,     size='25mm × 1m',    qty=180)
p_foam_blg  = make_product('Foam Block Large',       cat_foam,     size='2m × 1m × 1m', qty=30)
p_foam_bls  = make_product('Foam Block Small',       cat_foam,     size='1m × 0.5m',    qty=75)

# Roof Tiles
p_roman     = make_product('Roman Roof Tile',        cat_tile,     size='420mm × 330mm', qty=1500)
p_ridge     = make_product('Ridge Tile',             cat_tile,     size='450mm',          qty=400)
p_hip       = make_product('Hip Tile',               cat_tile,     size='450mm',          qty=220)
p_flat_ct   = make_product('Flat Concrete Tile',     cat_tile,     size='400mm × 250mm',  qty=800)
p_interlock = make_product('Interlocking Tile',      cat_tile,     size='380mm × 230mm',  qty=600)

# Pipes & Fittings
p_pvc4      = make_product('PVC Pipe 4 inch',        cat_pipe,     size='4" × 6m',      qty=90)
p_pvc3      = make_product('PVC Pipe 3 inch',        cat_pipe,     size='3" × 6m',      qty=120)
p_hdpe2     = make_product('HDPE Pipe 2 inch',       cat_pipe,     size='2" × 6m',      qty=55)
p_elbow4    = make_product('PVC Elbow 4 inch',       cat_pipe,     size='4"',            qty=200)
p_tee3      = make_product('PVC Tee 3 inch',         cat_pipe,     size='3"',            qty=150)

# Hardware
p_screw     = make_product('Roofing Screw M6',       cat_hardware, size='M6 × 75mm',    qty=5000)
p_bolt      = make_product('Roofing Bolt M8',        cat_hardware, size='M8 × 100mm',   qty=2000)
p_washer    = make_product('Galvanised Washer M6',   cat_hardware, size='M6',            qty=8000)
p_clip      = make_product('Purlin Clip',            cat_hardware, size='Standard',      qty=600)
p_nail      = make_product('J-Hook Nail',            cat_hardware, size='75mm',          qty=10000)


# ─── Customers ────────────────────────────────────────────────────────────────

print('\n── Customers ────────────────────────────────────────')

c_amal      = make_customer('Amal Perera',         address='45, Kandy Road, Kurunegala',       balance=0)
c_nimal     = make_customer('Nimal Constructions', address='12, Industrial Zone, Gampaha',     balance=5000)
c_suresh    = make_customer('Suresh Hardware',     address='78, Main Street, Matara',          balance=0)
c_lanka     = make_customer('Lanka Roofing Co.',   address='23, Negombo Road, Wattala',        balance=12500)
c_jayasing  = make_customer('W.D.K. Jayasinghe',  address='6/1, Temple Road, Panadura',       balance=0)
c_prasad    = make_customer('Prasad Builders',     address='99, Colombo Road, Kalutara',       balance=3000)
c_silva     = make_customer('Silva & Sons',        address='34, Galle Road, Hikkaduwa',        balance=0)
c_chatura   = make_customer('Chatura Enterprises', address='17, Station Road, Anuradhapura',  balance=8750)
c_rathna    = make_customer('D.M.S. Rathnayake',  address='2, New Town, Ratnapura',           balance=0)
c_stores    = make_customer('Ratnayake Stores',    address='88, Market Road, Badulla',         balance=1500)
c_sampath   = make_customer('Sampath Roofing',     address='55, Rajapaksha Mawatha, Matale',  balance=0)
c_green     = make_customer('Green Build Ltd.',    address='10, Nawala Road, Nugegoda',        balance=22000)
c_bandara   = make_customer('H.M. Bandara',        address='3, Lake View, Tissamaharama',      balance=0)
c_upeka     = make_customer('Upeka Trading',       address='66, Kandy Road, Kadawatha',        balance=4250)
c_city      = make_customer('City Hardware Hub',   address='1, Main Street, Colombo 10',       balance=0)


# ─── Customer Prices ──────────────────────────────────────────────────────────
# Only assign prices where a customer gets a rate different from the standard.
# Customers without entries here use the default product price on bills.

print('\n── Customer Prices ──────────────────────────────────')

# Lanka Roofing Co. — bulk roofing buyer, discounted tile & fibre prices
make_price(c_lanka, p_roman,     1_800)
make_price(c_lanka, p_ridge,     2_200)
make_price(c_lanka, p_hip,       2_100)
make_price(c_lanka, p_flat_ct,   1_650)
make_price(c_lanka, p_interlock, 1_750)
make_price(c_lanka, p_sheet_84,  3_400)
make_price(c_lanka, p_corr,      2_900)

# Nimal Constructions — regular builder, gets a small discount on fibre & foam
make_price(c_nimal, p_sheet_84,  3_500)
make_price(c_nimal, p_sheet_63,  2_800)
make_price(c_nimal, p_foam_50,     620)
make_price(c_nimal, p_foam_25,     380)
make_price(c_nimal, p_pvc4,      1_850)
make_price(c_nimal, p_pvc3,      1_400)

# Sampath Roofing — specialist roofer, custom tile rates
make_price(c_sampath, p_roman,     1_850)
make_price(c_sampath, p_ridge,     2_250)
make_price(c_sampath, p_hip,       2_150)
make_price(c_sampath, p_interlock, 1_800)
make_price(c_sampath, p_screw,        18)
make_price(c_sampath, p_bolt,         28)

# Green Build Ltd. — large account, preferential rates across categories
make_price(c_green, p_sheet_84,   3_300)
make_price(c_green, p_sheet_63,   2_700)
make_price(c_green, p_corr,       2_800)
make_price(c_green, p_flat_fp,    2_950)
make_price(c_green, p_cement_bd,  4_200)
make_price(c_green, p_roman,      1_780)
make_price(c_green, p_ridge,      2_180)
make_price(c_green, p_flat_ct,    1_620)
make_price(c_green, p_pvc4,       1_820)
make_price(c_green, p_pvc3,       1_380)
make_price(c_green, p_hdpe2,      2_100)
make_price(c_green, p_foam_50,       600)
make_price(c_green, p_foam_25,       370)

# Chatura Enterprises — hardware focus, discounted fittings
make_price(c_chatura, p_screw,       17)
make_price(c_chatura, p_bolt,        26)
make_price(c_chatura, p_washer,       5)
make_price(c_chatura, p_clip,       145)
make_price(c_chatura, p_nail,          4)
make_price(c_chatura, p_elbow4,     320)
make_price(c_chatura, p_tee3,       260)

# City Hardware Hub — hardware dealer, negotiated rates
make_price(c_city, p_screw,          16)
make_price(c_city, p_bolt,           25)
make_price(c_city, p_washer,          5)
make_price(c_city, p_clip,          140)
make_price(c_city, p_nail,            4)
make_price(c_city, p_pvc4,        1_800)
make_price(c_city, p_pvc3,        1_350)
make_price(c_city, p_elbow4,        310)
make_price(c_city, p_tee3,          250)

# Prasad Builders — occasional bulk foam orders
make_price(c_prasad, p_foam_50,     630)
make_price(c_prasad, p_foam_25,     390)
make_price(c_prasad, p_foam_blg,  4_800)
make_price(c_prasad, p_foam_bls,  2_600)

# Upeka Trading — mixed products, modest discount
make_price(c_upeka, p_sheet_84,   3_550)
make_price(c_upeka, p_roman,      1_900)
make_price(c_upeka, p_ridge,      2_300)
make_price(c_upeka, p_screw,         19)

# Ratnayake Stores — local hardware shop
make_price(c_stores, p_screw,        18)
make_price(c_stores, p_bolt,         27)
make_price(c_stores, p_washer,        6)
make_price(c_stores, p_nail,           4)


# ─── Summary ──────────────────────────────────────────────────────────────────

print(f'\n── Done ─────────────────────────────────────────────')
print(f'   Created : {created_count}')
print(f'   Skipped : {skipped_count} (already existed)')
print(f'   Total   : {created_count + skipped_count}')
