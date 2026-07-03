import random
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.customers.models import Customer, CustomerProductPrice
from apps.pettycash.models import CashSale
from apps.production.models import Product, ProductCategory


def d(value):
    return Decimal(str(value)).quantize(Decimal('0.01'))


class Command(BaseCommand):
    help = 'Seed dummy data for all core models: production, customers, and pettycash.'

    def add_arguments(self, parser):
        parser.add_argument('--cashsales', type=int, default=35, help='Number of seed petty cash entries to ensure')

    def handle(self, *args, **options):
        random.seed(42)
        self.stdout.write(self.style.WARNING('Seeding full ERP demo data...'))

        categories, products, customers, product_base_prices = self._seed_master_data()
        cash_sale_created = self._seed_cash_sales(options['cashsales'])

        self.stdout.write(self.style.SUCCESS(
            f"\nDone. Created/ensured data -> "
            f"Categories: {len(categories)}, Products: {len(products)}, Customers: {len(customers)}, "
            f"Cash Sales added: {cash_sale_created}."
        ))

    def _seed_master_data(self):
        categories_data = [
            {'name': 'Cement', 'description': 'All types of cement products'},
            {'name': 'Steel', 'description': 'TMT bars, rods, and steel products'},
            {'name': 'Bricks', 'description': 'Clay bricks, fly ash bricks, AAC blocks'},
            {'name': 'Sand & Aggregates', 'description': 'River sand, M-sand, gravel, crushed stone'},
            {'name': 'Plumbing', 'description': 'Pipes, fittings, valves, and plumbing accessories'},
            {'name': 'Electrical', 'description': 'Wires, cables, switches, and electrical fittings'},
            {'name': 'Paint', 'description': 'Interior, exterior paints and primers'},
            {'name': 'Hardware', 'description': 'Nails, screws, bolts, hinges, locks'},
            {'name': 'Tiles', 'description': 'Floor tiles, wall tiles, ceramic and vitrified'},
            {'name': 'Wood & Plywood', 'description': 'Timber, plywood sheets, MDF boards'},
        ]

        products_data = [
            {'name': 'OPC 53 Grade', 'category': 'Cement', 'size': '50 kg', 'qty': 500, 'description': 'Ordinary Portland Cement 53 Grade'},
            {'name': 'PPC Cement', 'category': 'Cement', 'size': '50 kg', 'qty': 400, 'description': 'Portland Pozzolana Cement'},
            {'name': 'White Cement', 'category': 'Cement', 'size': '5 kg', 'qty': 200, 'description': 'White cement for finishing'},
            {'name': 'TMT Bar 8mm', 'category': 'Steel', 'size': '8 mm', 'qty': 1000, 'description': 'Fe-500 TMT reinforcement bar'},
            {'name': 'TMT Bar 12mm', 'category': 'Steel', 'size': '12 mm', 'qty': 800, 'description': 'Fe-500 TMT reinforcement bar'},
            {'name': 'Binding Wire', 'category': 'Steel', 'size': '20 gauge', 'qty': 300, 'description': 'GI binding wire for rebar tying'},
            {'name': 'Red Clay Brick', 'category': 'Bricks', 'size': '9x4x3 in', 'qty': 10000, 'description': 'Standard red clay brick'},
            {'name': 'Fly Ash Brick', 'category': 'Bricks', 'size': '9x4x3 in', 'qty': 8000, 'description': 'Eco-friendly fly ash brick'},
            {'name': 'AAC Block', 'category': 'Bricks', 'size': '600x200x150 mm', 'qty': 3000, 'description': 'Autoclaved Aerated Concrete block'},
            {'name': 'M-Sand', 'category': 'Sand & Aggregates', 'size': '1 unit', 'qty': 150, 'description': 'Manufactured sand for construction'},
            {'name': 'River Sand', 'category': 'Sand & Aggregates', 'size': '1 unit', 'qty': 100, 'description': 'Natural river sand'},
            {'name': '20mm Aggregate', 'category': 'Sand & Aggregates', 'size': '1 unit', 'qty': 200, 'description': 'Crushed stone 20 mm jelly'},
            {'name': 'PVC Pipe 1 inch', 'category': 'Plumbing', 'size': '1 inch', 'qty': 500, 'description': 'PVC pressure pipe'},
            {'name': 'CPVC Pipe 0.5 inch', 'category': 'Plumbing', 'size': '0.5 inch', 'qty': 400, 'description': 'CPVC hot-water pipe'},
            {'name': 'Ball Valve 1 inch', 'category': 'Plumbing', 'size': '1 inch', 'qty': 150, 'description': 'Brass ball valve'},
            {'name': 'Copper Wire 1.5mm', 'category': 'Electrical', 'size': '90 m coil', 'qty': 120, 'description': 'FR PVC insulated copper wire'},
            {'name': 'MCB 32A', 'category': 'Electrical', 'size': 'Single Pole', 'qty': 250, 'description': 'Miniature Circuit Breaker 32 Amp'},
            {'name': 'Interior Emulsion', 'category': 'Paint', 'size': '20 L', 'qty': 60, 'description': 'Premium interior wall paint'},
            {'name': 'Exterior Emulsion', 'category': 'Paint', 'size': '20 L', 'qty': 50, 'description': 'Weather-proof exterior paint'},
            {'name': 'Primer', 'category': 'Paint', 'size': '10 L', 'qty': 80, 'description': 'White cement primer'},
            {'name': 'GI Nails 3 inch', 'category': 'Hardware', 'size': '1 kg pack', 'qty': 300, 'description': 'Galvanized iron nails'},
            {'name': 'Wood Screws 2 inch', 'category': 'Hardware', 'size': '100 pcs', 'qty': 400, 'description': 'Self-tapping wood screws'},
            {'name': 'Door Hinge SS', 'category': 'Hardware', 'size': '4 inch', 'qty': 200, 'description': 'Stainless steel butt hinge'},
            {'name': 'Floor Tile 2x2', 'category': 'Tiles', 'size': '600x600 mm', 'qty': 1500, 'description': 'Vitrified glossy floor tile'},
            {'name': 'Wall Tile 12x18', 'category': 'Tiles', 'size': '300x450 mm', 'qty': 2000, 'description': 'Ceramic wall tile for kitchen/bath'},
            {'name': 'BWR Plywood 18mm', 'category': 'Wood & Plywood', 'size': '8x4 ft', 'qty': 100, 'description': 'Boiling Water Resistant plywood'},
            {'name': 'Teak Wood Plank', 'category': 'Wood & Plywood', 'size': '6 ft', 'qty': 80, 'description': 'Natural teak wood plank'},
            {'name': 'MDF Board 12mm', 'category': 'Wood & Plywood', 'size': '8x4 ft', 'qty': 120, 'description': 'Medium Density Fibreboard'},
        ]

        customers_data = [
            {'name': 'Raj Construction', 'address': '12/A, MG Road, Coimbatore - 641001', 'balance': Decimal('15000.00')},
            {'name': 'Kumar Builders', 'address': '45, Gandhi Nagar, Tirupur - 641602', 'balance': Decimal('8500.00')},
            {'name': 'Sri Lakshmi Enterprises', 'address': '78, Nehru Street, Erode - 638001', 'balance': Decimal('22000.00')},
            {'name': 'Deepak & Sons', 'address': '9, Anna Salai, Salem - 636001', 'balance': Decimal('0.00')},
            {'name': 'Senthil Homes', 'address': '33, Kamaraj Road, Madurai - 625001', 'balance': Decimal('4500.00')},
            {'name': 'Balaji Infra Projects', 'address': '101, Industrial Estate, Chennai - 600032', 'balance': Decimal('55000.00')},
            {'name': 'VK Constructions', 'address': '56, Avinashi Road, Coimbatore - 641018', 'balance': Decimal('12000.00')},
            {'name': 'Mahalakshmi Traders', 'address': '22, Bazaar Street, Trichy - 620001', 'balance': Decimal('0.00')},
            {'name': 'Naveen Developers', 'address': '7/B, Lake View Road, Ooty - 643001', 'balance': Decimal('30000.00')},
            {'name': 'SS Civil Works', 'address': '88, Peelamedu, Coimbatore - 641004', 'balance': Decimal('9800.00')},
            {'name': 'Anbu Hardware Store', 'address': '14, Market Road, Pollachi - 642001', 'balance': Decimal('1200.00')},
            {'name': 'Murugan Contractors', 'address': '60, EB Colony, Dindigul - 624001', 'balance': Decimal('17500.00')},
            {'name': 'Priya Foundations', 'address': '3, Temple Street, Thanjavur - 613001', 'balance': Decimal('0.00')},
            {'name': 'Karthik Associates', 'address': '25, Ring Road, Karur - 639001', 'balance': Decimal('6700.00')},
            {'name': 'JM Builders & Co', 'address': '110, Bypass Road, Namakkal - 637001', 'balance': Decimal('42000.00')},
        ]

        product_base_prices = {
            'OPC 53 Grade': d(390), 'PPC Cement': d(370), 'White Cement': d(480),
            'TMT Bar 8mm': d(54), 'TMT Bar 12mm': d(59), 'Binding Wire': d(92),
            'Red Clay Brick': d(8), 'Fly Ash Brick': d(6.5), 'AAC Block': d(50),
            'M-Sand': d(4300), 'River Sand': d(4700), '20mm Aggregate': d(3800),
            'PVC Pipe 1 inch': d(125), 'CPVC Pipe 0.5 inch': d(138), 'Ball Valve 1 inch': d(240),
            'Copper Wire 1.5mm': d(3300), 'MCB 32A': d(210),
            'Interior Emulsion': d(2950), 'Exterior Emulsion': d(3200), 'Primer': d(900),
            'GI Nails 3 inch': d(115), 'Wood Screws 2 inch': d(90), 'Door Hinge SS': d(150),
            'Floor Tile 2x2': d(45), 'Wall Tile 12x18': d(38),
            'BWR Plywood 18mm': d(1450), 'Teak Wood Plank': d(980), 'MDF Board 12mm': d(820),
        }

        categories = {}
        for item in categories_data:
            obj, _ = ProductCategory.objects.get_or_create(
                name=item['name'],
                defaults={'description': item['description']},
            )
            categories[item['name']] = obj

        products = {}
        for item in products_data:
            cat = categories[item['category']]
            obj, _ = Product.objects.get_or_create(
                name=item['name'],
                category=cat,
                defaults={
                    'size': item['size'],
                    'qty': d(item['qty']),
                    'description': item['description'],
                },
            )
            products[item['name']] = obj

        customers = {}
        for item in customers_data:
            obj, _ = Customer.objects.get_or_create(
                name=item['name'],
                defaults={
                    'address': item['address'],
                    'balance': item['balance'],
                },
            )
            customers[item['name']] = obj

        discount_factors = [d(0.94), d(0.96), d(0.98), d(1.00), d(1.02)]
        for index, customer in enumerate(customers.values()):
            factor = discount_factors[index % len(discount_factors)]
            for product_name, product in products.items():
                base = product_base_prices.get(product_name)
                if base is None:
                    continue
                unit_price = (base * factor).quantize(Decimal('0.01'))
                CustomerProductPrice.objects.get_or_create(
                    customer=customer,
                    product=product,
                    defaults={'unit_price': unit_price},
                )

        return categories, products, customers, product_base_prices

    def _seed_cash_sales(self, target_count):
        created_count = 0
        purpose_options = [
            'Office petty expenses', 'Transport and delivery charge', 'Tea and refreshments',
            'Cash collection from counter', 'Stationery purchase', 'Utility bill payment',
            'Local purchase reimbursement', 'Maintenance expense', 'Courier expense',
        ]

        for i in range(1, target_count + 1):
            reference = f'SEED-CS-{i:05d}'
            if CashSale.objects.filter(reference_number=reference).exists():
                continue

            sale_type = random.choices([CashSale.CASH_IN, CashSale.CASH_OUT], weights=[45, 55], k=1)[0]
            amount = d(random.uniform(250, 15000))
            sale_date = timezone.localdate() - timedelta(days=random.randint(0, 180))

            CashSale.objects.create(
                date=sale_date,
                reference_number=reference,
                sale_type=sale_type,
                amount=amount,
                purpose=random.choice(purpose_options),
                notes='Seed petty cash entry',
            )
            created_count += 1

        return created_count
