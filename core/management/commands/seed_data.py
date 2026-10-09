from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
import datetime

from accounts.models import UserProfile, Address, LoyaltyTransaction
from products.models import Category, Product, ProductImage, Review
from cart.models import Coupon
from orders.models import Order, OrderItem, OrderTracking
from core.models import DeliveryPincode

class Command(BaseCommand):
    help = 'Populates the database with rich seed data for THE ULTIMATE SHOPPING'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding THE ULTIMATE SHOPPING database..."))

        # 1. Create Admin Account
        admin_user, created = User.objects.get_or_create(username='admin', defaults={
            'email': 'admin@ultimateshopping.com',
            'first_name': 'Super',
            'last_name': 'Administrator',
            'is_staff': True,
            'is_superuser': True
        })
        if created:
            admin_user.set_password('Admin@12345')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("Created admin user: admin / Admin@12345"))
        else:
            admin_user.is_staff = True
            admin_user.is_superuser = True
            admin_user.set_password('Admin@12345')
            admin_user.save()

        # 2. Create Demo Customer Account
        customer_user, created = User.objects.get_or_create(username='customer', defaults={
            'email': 'customer@example.com',
            'first_name': 'Rahul',
            'last_name': 'Sharma',
            'is_staff': False
        })
        if created:
            customer_user.set_password('Customer@12345')
            customer_user.save()
            profile = customer_user.profile
            profile.phone = '+91 98765 43210'
            profile.loyalty_points = 250
            profile.save()
            LoyaltyTransaction.objects.create(
                user=customer_user,
                points=100,
                description="Welcome sign-up reward bonus"
            )
            LoyaltyTransaction.objects.create(
                user=customer_user,
                points=150,
                description="Bonus reward from previous purchase"
            )
            self.stdout.write(self.style.SUCCESS("Created demo customer: customer / Customer@12345"))
        else:
            customer_user.set_password('Customer@12345')
            customer_user.save()

        # Demo Address for Customer
        demo_address, _ = Address.objects.get_or_create(
            user=customer_user,
            full_name="Rahul Sharma",
            phone="+91 98765 43210",
            street_address="Flat 402, Lotus Residency, MG Road",
            apartment_suite="Near City Mall",
            city="Bengaluru",
            state="Karnataka",
            postal_code="560001",
            country="India",
            address_type="Home",
            is_default=True
        )

        # 3. Create Categories
        categories_data = [
            {
                'name': 'Electronics & Gadgets',
                'slug': 'electronics',
                'description': 'Smartphones, laptops, audio gear, and cutting-edge tech gadgets.',
                'icon': 'bi-laptop',
                'image_url': 'https://images.unsplash.com/photo-1498049794561-7780e7231661?w=600&auto=format&fit=crop&q=80',
                'is_featured': True
            },
            {
                'name': 'Fashion & Apparel',
                'slug': 'fashion',
                'description': 'Trendsetting men and women clothing, sneakers, watches and accessories.',
                'icon': 'bi-bag-heart',
                'image_url': 'https://images.unsplash.com/photo-1445205170230-053b83016050?w=600&auto=format&fit=crop&q=80',
                'is_featured': True
            },
            {
                'name': 'Home & Kitchen',
                'slug': 'home-kitchen',
                'description': 'Smart kitchen appliances, elegant decor, and home essentials.',
                'icon': 'bi-house-door',
                'image_url': 'https://images.unsplash.com/photo-1556911220-e15b29be8c8f?w=600&auto=format&fit=crop&q=80',
                'is_featured': True
            },
            {
                'name': 'Beauty & Wellness',
                'slug': 'beauty-wellness',
                'description': 'Premium skincare, fragrances, grooming essentials, and wellness products.',
                'icon': 'bi-stars',
                'image_url': 'https://images.unsplash.com/photo-1596462502278-27bfdc403348?w=600&auto=format&fit=crop&q=80',
                'is_featured': True
            },
            {
                'name': 'Sports & Fitness',
                'slug': 'sports-fitness',
                'description': 'Gym gear, running shoes, smart fitness trackers, and outdoor equipment.',
                'icon': 'bi-bicycle',
                'image_url': 'https://images.unsplash.com/photo-1517838277536-f5f99be501cd?w=600&auto=format&fit=crop&q=80',
                'is_featured': True
            },
            {
                'name': 'Books & Audio',
                'slug': 'books-media',
                'description': 'Bestselling books, e-readers, educational literature, and audiobooks.',
                'icon': 'bi-book',
                'image_url': 'https://images.unsplash.com/photo-1495446815901-a7297e633e8d?w=600&auto=format&fit=crop&q=80',
                'is_featured': True
            }
        ]

        cat_map = {}
        for cdata in categories_data:
            cat, _ = Category.objects.update_or_create(
                slug=cdata['slug'],
                defaults=cdata
            )
            cat_map[cdata['slug']] = cat

        # 4. Products Data
        now = timezone.now()
        deals_end = now + datetime.timedelta(days=7)

        products_data = [
            # Smartphone under 15,000 (Required in AI assistant test prompt!)
            {
                'category': cat_map['electronics'],
                'name': 'Redmi Note 13 5G (Prism Gold, 128GB)',
                'slug': 'redmi-note-13-5g',
                'brand': 'Xiaomi',
                'sku': 'RDM-N13-GLD',
                'short_description': 'Super-slim 120Hz AMOLED display, 108MP camera, 33W fast turbo charging.',
                'description': 'Experience blazing speed with the MediaTek Dimensity 6080 5G processor. Features a vivid 6.67-inch FHD+ AMOLED screen with ultra-narrow bezels, Corning Gorilla Glass 5 protection, and an all-day 5000mAh battery.',
                'price': Decimal('17999.00'),
                'discount_price': Decimal('13999.00'),
                'stock': 24,
                'stock_threshold': 5,
                'is_active': True,
                'is_featured': True,
                'is_bestseller': True,
                'is_flash_deal': True,
                'flash_deal_end': deals_end,
                'primary_image': 'https://images.unsplash.com/photo-1598327105666-5b89351aff97?w=600&auto=format&fit=crop&q=80',
                'specifications': {
                    'Display': '6.67-inch FHD+ 120Hz AMOLED',
                    'Processor': 'MediaTek Dimensity 6080 5G',
                    'RAM / Storage': '6GB RAM + 128GB Storage',
                    'Rear Camera': '108MP + 8MP Ultra-wide + 2MP Macro',
                    'Battery': '5000 mAh with 33W Fast Charger',
                    'Warranty': '1 Year Manufacturer Warranty'
                },
                'secondary_images': [
                    'https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=600&auto=format&fit=crop&q=80',
                    'https://images.unsplash.com/photo-1592899677977-9c10ca588bbd?w=600&auto=format&fit=crop&q=80'
                ]
            },
            {
                'category': cat_map['electronics'],
                'name': 'Samsung Galaxy M14 5G (Smoky Teal, 128GB)',
                'slug': 'samsung-galaxy-m14-5g',
                'brand': 'Samsung',
                'sku': 'SMG-M14-TEA',
                'short_description': 'Massive 6000mAh monster battery, 50MP triple camera, 5nm Exynos processor.',
                'description': 'Unleash power with the Samsung Galaxy M14 5G. Engineered with segment-leading 6000mAh battery for 2-day endurance, 13 5G bands, and smooth 90Hz FHD+ display for immersive streaming.',
                'price': Decimal('14999.00'),
                'discount_price': Decimal('12499.00'),
                'stock': 18,
                'stock_threshold': 4,
                'is_active': True,
                'is_featured': True,
                'is_bestseller': True,
                'is_flash_deal': False,
                'primary_image': 'https://images.unsplash.com/photo-1610945415295-d9bbf067e59c?w=600&auto=format&fit=crop&q=80',
                'specifications': {
                    'Display': '6.6-inch 90Hz FHD+ PLS LCD',
                    'Processor': 'Exynos 1330 5nm Octa-core',
                    'RAM / Storage': '6GB RAM + 128GB ROM',
                    'Rear Camera': '50MP (F1.8) + 2MP + 2MP',
                    'Battery': '6000 mAh with 25W Support',
                    'Warranty': '1 Year Brand Warranty'
                },
                'secondary_images': [
                    'https://images.unsplash.com/photo-1580910051074-3eb694886505?w=600&auto=format&fit=crop&q=80'
                ]
            },
            {
                'category': cat_map['electronics'],
                'name': 'Apple iPhone 15 Pro Max (Titanium Blue, 256GB)',
                'slug': 'apple-iphone-15-pro-max',
                'brand': 'Apple',
                'sku': 'APL-IP15PM-BLU',
                'short_description': 'Aerospace-grade titanium design, A17 Pro chip, 5x telephoto optical zoom.',
                'description': 'Forged in titanium and featuring the groundbreaking A17 Pro chip, customizable Action button, and the most versatile camera system ever in an iPhone. USB-C with USB 3 speeds.',
                'price': Decimal('159900.00'),
                'discount_price': Decimal('148900.00'),
                'stock': 12,
                'stock_threshold': 3,
                'is_active': True,
                'is_featured': True,
                'is_bestseller': True,
                'is_flash_deal': False,
                'primary_image': 'https://images.unsplash.com/photo-1695048133142-1a20484d2569?w=600&auto=format&fit=crop&q=80',
                'specifications': {
                    'Display': '6.7-inch Super Retina XDR OLED ProMotion 120Hz',
                    'Processor': 'A17 Pro Chip with 6-core GPU',
                    'Storage': '256GB NVMe',
                    'Camera': '48MP Main + 12MP Ultra Wide + 12MP 5x Telephoto',
                    'Build': 'Titanium Frame with Textured Matte Glass Back',
                    'Connector': 'USB-C (up to 10Gb/s)'
                },
                'secondary_images': [
                    'https://images.unsplash.com/photo-1510557880182-3d4d3cba35a5?w=600&auto=format&fit=crop&q=80'
                ]
            },
            {
                'category': cat_map['electronics'],
                'name': 'Sony WH-1000XM5 Wireless Noise Cancelling Headphones',
                'slug': 'sony-wh1000xm5-headphones',
                'brand': 'Sony',
                'sku': 'SNY-XM5-BLK',
                'short_description': 'Industry-leading noise cancellation, 30-hour battery, crystal-clear hands-free calls.',
                'description': 'Two processors and eight microphones deliver magnificent noise cancelling and exceptional call quality. Newly developed carbon-fiber driver units ensure magnificent high-resolution sound playback.',
                'price': Decimal('34990.00'),
                'discount_price': Decimal('26990.00'),
                'stock': 15,
                'stock_threshold': 4,
                'is_active': True,
                'is_featured': True,
                'is_bestseller': True,
                'is_flash_deal': True,
                'flash_deal_end': deals_end,
                'primary_image': 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600&auto=format&fit=crop&q=80',
                'specifications': {
                    'Noise Cancellation': 'Dual Processor V1 + HD QN1',
                    'Battery Life': 'Up to 30 hours (ANC on)',
                    'Microphones': '8 Mics with Precise Voice Pickup',
                    'Connectivity': 'Bluetooth 5.2, Multipoint, 3.5mm Aux',
                    'Weight': '250 grams',
                    'Warranty': '1 Year Sony India'
                },
                'secondary_images': [
                    'https://images.unsplash.com/photo-1484704849700-f032a568e944?w=600&auto=format&fit=crop&q=80'
                ]
            },
            {
                'category': cat_map['electronics'],
                'name': 'Apple MacBook Air 15-inch M3 (Midnight, 16GB, 512GB)',
                'slug': 'macbook-air-15-m3',
                'brand': 'Apple',
                'sku': 'APL-MBA15-M3',
                'short_description': 'Stunning Liquid Retina display, 18 hours battery life, impossibly thin silent design.',
                'description': 'Lean, mean, M3 machine. Built for Apple Intelligence with incredible performance and up to 18 hours of battery life. 15.3-inch Liquid Retina display brings 1 billion colors to life.',
                'price': Decimal('154900.00'),
                'discount_price': Decimal('139900.00'),
                'stock': 8,
                'stock_threshold': 3,
                'is_active': True,
                'is_featured': True,
                'is_bestseller': False,
                'primary_image': 'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=600&auto=format&fit=crop&q=80',
                'specifications': {
                    'Display': '15.3-inch Liquid Retina Display (500 nits)',
                    'Chip': 'Apple M3 chip (8-core CPU, 10-core GPU)',
                    'Memory': '16GB Unified Memory',
                    'Storage': '512GB SSD',
                    'Battery': 'Up to 18 hours wireless web',
                    'Audio': 'Six-speaker sound system with Spatial Audio'
                },
                'secondary_images': []
            },
            # Fashion
            {
                'category': cat_map['fashion'],
                'name': 'UrbanCraft Italian Leather Aviator Bomber Jacket',
                'slug': 'italian-leather-bomber-jacket',
                'brand': 'UrbanCraft',
                'sku': 'UC-JKT-BOM-01',
                'short_description': 'Genuine full-grain lambskin leather with cozy sherpa collar and brass zippers.',
                'description': 'Handcrafted from premium Italian full-grain lambskin leather that develops a magnificent patina over time. Features a detachable plush sherpa wool collar, ribbed cuffs, and quilted thermal satin lining.',
                'price': Decimal('12999.00'),
                'discount_price': Decimal('7999.00'),
                'stock': 14,
                'stock_threshold': 5,
                'is_active': True,
                'is_featured': True,
                'is_bestseller': True,
                'is_flash_deal': True,
                'flash_deal_end': deals_end,
                'primary_image': 'https://images.unsplash.com/photo-1551028719-00167b16eac5?w=600&auto=format&fit=crop&q=80',
                'specifications': {
                    'Material': '100% Genuine Full-grain Lambskin Leather',
                    'Lining': 'Quilted Thermal Satin',
                    'Collar': 'Detachable Natural Sherpa Collar',
                    'Pockets': '4 Exterior, 2 Concealed Interior',
                    'Care': 'Specialist Leather Clean Only'
                },
                'secondary_images': [
                    'https://images.unsplash.com/photo-1520975954732-35dd22299614?w=600&auto=format&fit=crop&q=80'
                ]
            },
            {
                'category': cat_map['fashion'],
                'name': 'Nike Air Max 270 React Sneakers (White/Crimson)',
                'slug': 'nike-air-max-270-react',
                'brand': 'Nike',
                'sku': 'NK-AM270-WHT',
                'short_description': 'Max Air 270 unit delivers 270 degrees of unrivaled all-day comfort cushioning.',
                'description': 'Nike Air Max 270 combines exaggerated tongue from Air Max 180 and classic elements from Air Max 93. Features Nike React foam midsole for an exceptionally soft and bouncy stride.',
                'price': Decimal('13995.00'),
                'discount_price': Decimal('9799.00'),
                'stock': 22,
                'stock_threshold': 5,
                'is_active': True,
                'is_featured': True,
                'is_bestseller': True,
                'primary_image': 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=600&auto=format&fit=crop&q=80',
                'specifications': {
                    'Sole': 'Rubber with React Cushioning Technology',
                    'Upper': 'Breathable Engineered Knit & Synthetic Overlays',
                    'Closure': 'Lace-Up with Speed Lacing System',
                    'Fit': 'True to Size',
                    'Weight': '340 grams'
                },
                'secondary_images': [
                    'https://images.unsplash.com/photo-1608231387042-66d1773070a5?w=600&auto=format&fit=crop&q=80'
                ]
            },
            {
                'category': cat_map['fashion'],
                'name': 'Titan Regalia Automatic Chronograph Sapphire Watch',
                'slug': 'titan-regalia-automatic-watch',
                'brand': 'Titan',
                'sku': 'TTN-RGL-CHR',
                'short_description': 'Open heart skeleton automatic dial, anti-reflective sapphire crystal glass.',
                'description': 'A masterpiece of horological engineering. Hand-assembled with 24 jewels self-winding mechanical movement, 42-hour power reserve, surgical stainless steel case, and genuine alligator grain leather strap.',
                'price': Decimal('22995.00'),
                'discount_price': Decimal('16495.00'),
                'stock': 7,
                'stock_threshold': 3,
                'is_active': True,
                'is_featured': True,
                'is_bestseller': False,
                'primary_image': 'https://images.unsplash.com/photo-1524805444758-089113d48a6d?w=600&auto=format&fit=crop&q=80',
                'specifications': {
                    'Movement': 'Automatic Self-Winding (24 Jewels)',
                    'Glass': 'Scratch-Proof Sapphire Crystal',
                    'Water Resistance': '50 Meters (5 ATM)',
                    'Case Diameter': '42 mm',
                    'Strap': 'Genuine Leather with Butterfly Clasp'
                },
                'secondary_images': []
            },
            # Home & Kitchen
            {
                'category': cat_map['home-kitchen'],
                'name': 'DeLonghi Magnifica S Smart Espresso Machine',
                'slug': 'delonghi-magnifica-s-espresso',
                'brand': 'DeLonghi',
                'sku': 'DLG-MAG-ESP',
                'short_description': 'Bean-to-cup barista espresso machine with 15-bar pump and manual milk frother.',
                'description': 'Grind fresh beans for every cup with integrated conical burr grinder featuring 13 grind settings. Prepare rich aromatic espresso, cappuccino, and latte macchiato at the touch of a button.',
                'price': Decimal('54990.00'),
                'discount_price': Decimal('42990.00'),
                'stock': 6,
                'stock_threshold': 2,
                'is_active': True,
                'is_featured': True,
                'is_bestseller': True,
                'primary_image': 'https://images.unsplash.com/photo-1517668808822-9ebb02f2a0e6?w=600&auto=format&fit=crop&q=80',
                'specifications': {
                    'Pump Pressure': '15 Bar Italian High Pressure',
                    'Water Tank': '1.8 Litres Removable',
                    'Bean Container': '250 grams with Aroma Preserving Lid',
                    'Milk Frother': 'Advanced Cappuccino System',
                    'Power': '1450 Watts'
                },
                'secondary_images': []
            },
            {
                'category': cat_map['home-kitchen'],
                'name': 'Dyson Pure Cool HEPA Air Purifier & Bladeless Fan',
                'slug': 'dyson-pure-cool-air-purifier',
                'brand': 'Dyson',
                'sku': 'DYS-PC-TP07',
                'short_description': 'Captures 99.95% of ultrafine particles including PM2.5, allergen gases, and dust.',
                'description': 'Intelligently purifies and cools the whole room. Fully sealed to HEPA H13 standard, preventing pollutants from leaking back into the air. Controlled via remote and smart home app.',
                'price': Decimal('44900.00'),
                'discount_price': Decimal('36900.00'),
                'stock': 10,
                'stock_threshold': 3,
                'is_active': True,
                'is_featured': True,
                'is_bestseller': False,
                'is_flash_deal': True,
                'flash_deal_end': deals_end,
                'primary_image': 'https://images.unsplash.com/photo-1585771724684-38269d6639fd?w=600&auto=format&fit=crop&q=80',
                'specifications': {
                    'Filtration': 'HEPA H13 + Activated Carbon Filtration',
                    'Airflow': '390 Litres per second with Air Multiplier',
                    'Noise Level': 'Ultra-quiet Sleep Mode (38 dB)',
                    'Smart Features': 'LCD Real-time Air Quality Report',
                    'Coverage': 'Rooms up to 450 sq. ft.'
                },
                'secondary_images': []
            },
            # Beauty & Wellness
            {
                'category': cat_map['beauty-wellness'],
                'name': 'Estee Lauder Advanced Night Repair Synchronized Multi-Recovery Serum',
                'slug': 'estee-lauder-advanced-night-repair',
                'brand': 'Estee Lauder',
                'sku': 'EL-ANR-50ML',
                'short_description': 'Revolutionary face serum that rapidly reduces fine lines and maximizes firmness.',
                'description': 'Patented Chronolux Power Signal Technology supports skins natural repair process. Infused with Hyaluronic Acid for 72-hour continuous hydration, leaving skin radiant and rested.',
                'price': Decimal('9200.00'),
                'discount_price': Decimal('7499.00'),
                'stock': 30,
                'stock_threshold': 6,
                'is_active': True,
                'is_featured': True,
                'is_bestseller': True,
                'primary_image': 'https://images.unsplash.com/photo-1620916566398-39f1143ab7be?w=600&auto=format&fit=crop&q=80',
                'specifications': {
                    'Volume': '50 ml / 1.7 oz',
                    'Skin Type': 'All Skin Types (Oil-free, Non-acnegenic)',
                    'Key Ingredients': 'Hyaluronic Acid, Tripeptide-32, Antioxidants',
                    'Formula': 'Fragrance-Free, Paraben-Free',
                    'Origin': 'Made in USA'
                },
                'secondary_images': []
            },
            # Sports & Fitness
            {
                'category': cat_map['sports-fitness'],
                'name': 'Garmin Forerunner 265 AMOLED GPS Running Smartwatch',
                'slug': 'garmin-forerunner-265-watch',
                'brand': 'Garmin',
                'sku': 'GRM-FR265-BLK',
                'short_description': 'Brilliant AMOLED touchscreen, training readiness score, up to 13 days battery life.',
                'description': 'Plan your race day strategy with daily suggested workouts, heart rate variability (HRV) status, training readiness metrics, and multi-band GPS tracking with SatIQ technology.',
                'price': Decimal('49990.00'),
                'discount_price': Decimal('42490.00'),
                'stock': 12,
                'stock_threshold': 4,
                'is_active': True,
                'is_featured': True,
                'is_bestseller': True,
                'primary_image': 'https://images.unsplash.com/photo-1508685096489-7aacd43bd3b1?w=600&auto=format&fit=crop&q=80',
                'specifications': {
                    'Display': '1.3-inch Colorful AMOLED (416 x 416)',
                    'Battery Life': 'Up to 13 days in Smartwatch Mode, 20 hours GPS',
                    'Sensors': 'Wrist HR, Pulse Ox, Multi-band GNSS, Barometer',
                    'Water Rating': '5 ATM (Swimming / Showering)',
                    'Weight': '47 grams'
                },
                'secondary_images': []
            },
            # Out of Stock product (To test restock notifications!)
            {
                'category': cat_map['sports-fitness'],
                'name': 'Bowflex SelectTech 552 Adjustable Dumbbells (Pair)',
                'slug': 'bowflex-selecttech-552-dumbbells',
                'brand': 'Bowflex',
                'sku': 'BWF-ST552-SET',
                'short_description': 'Replaces 15 sets of weights. Adjusts from 5 to 52.5 lbs with turn of a dial.',
                'description': 'Combines 15 sets of weights into one compact system using a unique dial system. Rapidly switch from one exercise to the next with weights from 2.5 kg up to 24 kg per dumbbell.',
                'price': Decimal('38999.00'),
                'discount_price': Decimal('32999.00'),
                'stock': 0, # OUT OF STOCK for restock testing
                'stock_threshold': 2,
                'is_active': True,
                'is_featured': False,
                'is_bestseller': False,
                'primary_image': 'https://images.unsplash.com/photo-1584735935682-2f2b69dff9d2?w=600&auto=format&fit=crop&q=80',
                'specifications': {
                    'Weight Range': '2.5 to 24 kg (5 to 52.5 lbs) each',
                    'Settings': '15 Weight Increments',
                    'Plates': 'Molding around metal plates for quiet lifting',
                    'Dimensions': '43 x 21 x 23 cm'
                },
                'secondary_images': []
            },
            # Low Stock product (To test low stock admin inventory alerts!)
            {
                'category': cat_map['books-media'],
                'name': 'Kindle Paperwhite Signature Edition (32GB, Wireless Charging)',
                'slug': 'kindle-paperwhite-signature-32gb',
                'brand': 'Amazon',
                'sku': 'AMZ-KNDL-SIG32',
                'short_description': '6.8-inch 300 ppi glare-free display, auto-adjusting light, waterproof IPX8.',
                'description': 'Everything in the Kindle Paperwhite, plus wireless charging, auto-adjusting front light, and 32 GB storage. Up to 10 weeks of battery life and 20% faster page turns.',
                'price': Decimal('17999.00'),
                'discount_price': Decimal('15499.00'),
                'stock': 2, # LOW STOCK (threshold is 5)
                'stock_threshold': 5,
                'is_active': True,
                'is_featured': True,
                'is_bestseller': True,
                'primary_image': 'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=600&auto=format&fit=crop&q=80',
                'specifications': {
                    'Screen': '6.8-inch Glare-free 300 ppi Paperwhite',
                    'Storage': '32 GB holds thousands of books',
                    'Charging': 'Qi Wireless + USB-C Quick Charge',
                    'Water Resistance': 'IPX8 (Submersion in fresh water)',
                    'Battery Life': 'Up to 10 weeks'
                },
                'secondary_images': []
            }
        ]

        for pdata in products_data:
            sec_images = pdata.pop('secondary_images', [])
            prod, _ = Product.objects.update_or_create(
                slug=pdata['slug'],
                defaults=pdata
            )
            # Add secondary images
            for idx, img_url in enumerate(sec_images):
                ProductImage.objects.get_or_create(
                    product=prod,
                    image_url=img_url,
                    defaults={'order': idx + 1, 'alt_text': f"{prod.name} view {idx + 1}"}
                )

        self.stdout.write(self.style.SUCCESS(f"Seeded {len(products_data)} rich products."))

        # 5. Seed Reviews for products
        reviews_data = [
            (
                'redmi-note-13-5g', 5,
                "Best phone under ₹15,000 bar none!",
                "The AMOLED screen is stunningly bright and smooth at 120Hz. Battery easily lasts 1.5 days. Unbelievable value for under ₹15k!"
            ),
            (
                'redmi-note-13-5g', 4,
                "Very smooth daily performance",
                "Great camera in daylight and very fast charging. Decent build quality. Highly recommended for students and professionals."
            ),
            (
                'samsung-galaxy-m14-5g', 5,
                "Unstoppable 6000mAh battery life",
                "I bought this for my commute. Heavy GPS and hotspot usage and it still has 40% battery at night. Samsung OneUI is clean."
            ),
            (
                'sony-wh1000xm5-headphones', 5,
                "Supreme sound and silence",
                "The noise cancellation in flights and noisy cafes is black magic. Comfort is 10/10. Definitely worth every rupee."
            ),
            (
                'italian-leather-bomber-jacket', 5,
                "Incredible craftsmanship & genuine leather",
                "The leather aroma is authentic, fits like a glove, and the sherpa collar is super warm. Looks like a ₹30,000 designer jacket."
            ),
            (
                'nike-air-max-270-react', 4,
                "Extremely comfortable for running & casual wear",
                "React foam cushioning is top notch. Got compliments from friends on the design."
            ),
            (
                'estee-lauder-advanced-night-repair', 5,
                "Holy grail night serum",
                "Skin texture improved within 7 days. Glow and hydration are noticeable every morning."
            )
        ]

        for slug, rating, headline, comment in reviews_data:
            try:
                p = Product.objects.get(slug=slug)
                Review.objects.update_or_create(
                    product=p,
                    user=customer_user,
                    defaults={
                        'rating': rating,
                        'headline': headline,
                        'comment': comment,
                        'is_verified_purchase': True,
                        'is_approved': True,
                    }
                )
                p.update_rating_stats()
            except Product.DoesNotExist:
                pass

        # 6. Seed Coupons
        coupons = [
            {
                'code': 'WELCOME100',
                'discount_type': 'fixed',
                'discount_value': Decimal('100.00'),
                'min_purchase': Decimal('500.00'),
                'usage_limit': 500,
                'valid_to': now + datetime.timedelta(days=180),
                'is_active': True
            },
            {
                'code': 'SUPER20',
                'discount_type': 'percentage',
                'discount_value': Decimal('20.00'),
                'min_purchase': Decimal('1000.00'),
                'max_discount': Decimal('1500.00'),
                'usage_limit': 200,
                'valid_to': now + datetime.timedelta(days=90),
                'is_active': True
            },
            {
                'code': 'FESTIVE15',
                'discount_type': 'percentage',
                'discount_value': Decimal('15.00'),
                'min_purchase': Decimal('2000.00'),
                'max_discount': Decimal('3000.00'),
                'usage_limit': 150,
                'valid_to': now + datetime.timedelta(days=60),
                'is_active': True
            },
            {
                'code': 'MEGA500',
                'discount_type': 'fixed',
                'discount_value': Decimal('500.00'),
                'min_purchase': Decimal('3000.00'),
                'usage_limit': 100,
                'valid_to': now + datetime.timedelta(days=45),
                'is_active': True
            }
        ]

        for cdata in coupons:
            Coupon.objects.update_or_create(
                code=cdata['code'],
                defaults=cdata
            )
        self.stdout.write(self.style.SUCCESS("Seeded coupons: WELCOME100, SUPER20, FESTIVE15, MEGA500"))

        # 7. Seed Serviceable Pincodes
        pincodes = [
            {'pincode': '110001', 'city': 'New Delhi', 'state': 'Delhi', 'estimated_days': 2},
            {'pincode': '400001', 'city': 'Mumbai', 'state': 'Maharashtra', 'estimated_days': 2},
            {'pincode': '560001', 'city': 'Bengaluru', 'state': 'Karnataka', 'estimated_days': 1},
            {'pincode': '600001', 'city': 'Chennai', 'state': 'Tamil Nadu', 'estimated_days': 2},
            {'pincode': '700001', 'city': 'Kolkata', 'state': 'West Bengal', 'estimated_days': 3},
            {'pincode': '500001', 'city': 'Hyderabad', 'state': 'Telangana', 'estimated_days': 2},
            {'pincode': '411001', 'city': 'Pune', 'state': 'Maharashtra', 'estimated_days': 2},
            {'pincode': '380001', 'city': 'Ahmedabad', 'state': 'Gujarat', 'estimated_days': 2},
            {'pincode': '201301', 'city': 'Noida', 'state': 'Uttar Pradesh', 'estimated_days': 2},
            {'pincode': '682001', 'city': 'Kochi', 'state': 'Kerala', 'estimated_days': 3},
        ]
        for pdata in pincodes:
            DeliveryPincode.objects.update_or_create(
                pincode=pdata['pincode'],
                defaults=pdata
            )

        # 8. Seed Sample Order for Demo Customer
        sample_prod = Product.objects.get(slug='redmi-note-13-5g')
        demo_order, ord_created = Order.objects.get_or_create(
            order_number='ORD-DEMO1001',
            defaults={
                'user': customer_user,
                'status': 'shipped',
                'shipping_full_name': demo_address.full_name,
                'shipping_phone': demo_address.phone,
                'shipping_address': f"{demo_address.street_address}, {demo_address.apartment_suite}",
                'shipping_city': demo_address.city,
                'shipping_state': demo_address.state,
                'shipping_postal_code': demo_address.postal_code,
                'shipping_country': demo_address.country,
                'payment_method': 'online',
                'payment_status': 'completed',
                'transaction_id': 'SIM-PAY-DEMO998811',
                'subtotal': Decimal('13999.00'),
                'coupon_discount': Decimal('100.00'),
                'coupon_code': 'WELCOME100',
                'loyalty_discount': Decimal('0.00'),
                'shipping_cost': Decimal('0.00'),
                'total_amount': Decimal('13899.00'),
                'points_earned': 1389,
                'points_redeemed': 0,
                'tracking_number': 'TRK-BLUEDART-882199',
                'estimated_delivery_date': (now + datetime.timedelta(days=2)).date()
            }
        )

        if ord_created:
            OrderItem.objects.create(
                order=demo_order,
                product=sample_prod,
                product_name=sample_prod.name,
                product_image=sample_prod.primary_image,
                price=sample_prod.effective_price,
                quantity=1,
                total_price=sample_prod.effective_price
            )
            # Tracking history
            OrderTracking.objects.create(
                order=demo_order,
                status='placed',
                title="Order Placed",
                description="Your order was confirmed and verified.",
                location="Bengaluru Fulfillment Center"
            )
            OrderTracking.objects.create(
                order=demo_order,
                status='confirmed',
                title="Payment Verified",
                description="Simulated Online Payment completed successfully.",
                location="Billing Gateway"
            )
            OrderTracking.objects.create(
                order=demo_order,
                status='packed',
                title="Package Sealed",
                description="Package inspected and handed over to logistics partner.",
                location="Warehouse Zone B"
            )
            OrderTracking.objects.create(
                order=demo_order,
                status='shipped',
                title="Dispatched with BlueDart",
                description="Package is in transit with courier tracking TRK-BLUEDART-882199.",
                location="Regional Sorting Facility"
            )

        self.stdout.write(self.style.SUCCESS("[SUCCESS] THE ULTIMATE SHOPPING database seeded completely and successfully!"))
