from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from decimal import Decimal
from django.utils import timezone
import datetime

from products.models import Product, Category, Wishlist, Review, PriceAlert
from cart.models import Cart, CartItem, Coupon
from orders.models import Order, OrderItem, OrderTracking
from accounts.models import Address, UserProfile

class UltimateShoppingWorkflowTests(TestCase):
    def setUp(self):
        self.client = Client()
        
        # 1. Setup Category
        self.category = Category.objects.create(
            name="Electronics",
            slug="electronics",
            description="Tech and gadgets"
        )

        # 2. Setup Products (one in stock, one low stock, one out of stock)
        self.product1 = Product.objects.create(
            category=self.category,
            name="Redmi Note 13 5G",
            slug="redmi-note-13-5g",
            brand="Xiaomi",
            sku="RDM-001",
            short_description="5G smartphone with powerful processor",
            price=Decimal('15000.00'),
            discount_price=Decimal('13999.00'),
            stock=10,
            stock_threshold=5,
            is_active=True,
            primary_image="https://images.unsplash.com/photo-1598327105666-5b89351aff97?w=600"
        )

        self.out_of_stock_product = Product.objects.create(
            category=self.category,
            name="Rare Vintage Smartwatch",
            slug="rare-vintage-smartwatch",
            brand="Retro",
            sku="RTR-002",
            price=Decimal('5000.00'),
            stock=0, # out of stock
            stock_threshold=2,
            is_active=True,
            primary_image="https://images.unsplash.com/photo-1524805444758-089113d48a6d?w=600"
        )

        # 3. Setup Coupon
        self.coupon = Coupon.objects.create(
            code="TEST20",
            discount_type="percentage",
            discount_value=Decimal('20.00'),
            min_purchase=Decimal('500.00'),
            valid_from=timezone.now() - datetime.timedelta(days=1),
            valid_to=timezone.now() + datetime.timedelta(days=30),
            usage_limit=10,
            is_active=True
        )

        # 4. Setup Users (Regular User A, Regular User B, and Admin User)
        self.user_a = User.objects.create_user(username='usera', email='usera@example.com', password='Password@123')
        self.user_b = User.objects.create_user(username='userb', email='userb@example.com', password='Password@123')
        self.admin_user = User.objects.create_user(username='adminuser', email='admin@example.com', password='Password@123', is_staff=True)

        # Address for User A
        self.address_a = Address.objects.create(
            user=self.user_a,
            full_name="User A",
            phone="9876543210",
            street_address="123 Test Street",
            city="Bengaluru",
            state="Karnataka",
            postal_code="560001",
            is_default=True
        )

    # 1. Test Registration and Login
    def test_01_registration_and_login(self):
        # Register new user
        response = self.client.post(reverse('accounts:register'), {
            'username': 'newuser',
            'full_name': 'New Tester',
            'email': 'tester@example.com',
            'phone': '9123456789',
            'password': 'Password@123',
            'confirm_password': 'Password@123',
        })
        self.assertEqual(response.status_code, 302)
        new_user = User.objects.get(username='newuser')
        self.assertEqual(new_user.email, 'tester@example.com')
        # Check welcome loyalty bonus
        self.assertEqual(new_user.profile.loyalty_points, 100)

        # Test login
        self.client.logout()
        login_res = self.client.post(reverse('accounts:login'), {
            'username_or_email': 'newuser',
            'password': 'Password@123'
        })
        self.assertEqual(login_res.status_code, 302)

    # 2. Test Search and Filter Products
    def test_02_search_and_filters(self):
        # Search query
        response = self.client.get(reverse('products:list'), {'q': 'Redmi'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Redmi Note 13 5G')

        # Filter by category
        res_cat = self.client.get(reverse('products:list'), {'category': 'electronics'})
        self.assertEqual(res_cat.status_code, 200)
        self.assertContains(res_cat, 'Redmi Note 13 5G')

        # Filter in-stock only
        res_stock = self.client.get(reverse('products:list'), {'in_stock': '1'})
        self.assertContains(res_stock, 'Redmi Note 13 5G')
        self.assertNotContains(res_stock, 'Rare Vintage Smartwatch')

    # 3. Test Product Details View
    def test_03_product_detail_view(self):
        response = self.client.get(reverse('products:detail', kwargs={'slug': self.product1.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product1.name)
        self.assertContains(response, '13999.00')

    # 4. Test Add and Remove Cart Items
    def test_04_cart_operations(self):
        self.client.login(username='usera', password='Password@123')
        
        # Add to cart
        add_res = self.client.get(reverse('cart:add', kwargs={'product_id': self.product1.id}))
        self.assertEqual(add_res.status_code, 302)
        cart = Cart.objects.get(user=self.user_a)
        self.assertEqual(cart.total_items, 1)

        # Remove from cart
        item = cart.items.first()
        rem_res = self.client.post(reverse('cart:remove', kwargs={'item_id': item.id}))
        self.assertEqual(rem_res.status_code, 302)
        self.assertEqual(cart.items.count(), 0)

    # 5. Test Update Product Quantities
    def test_05_update_cart_quantity(self):
        self.client.login(username='usera', password='Password@123')
        self.client.get(reverse('cart:add', kwargs={'product_id': self.product1.id}))
        cart = Cart.objects.get(user=self.user_a)
        item = cart.items.first()

        # Increase quantity
        self.client.post(reverse('cart:update', kwargs={'item_id': item.id}), {'action': 'increase'})
        item.refresh_from_db()
        self.assertEqual(item.quantity, 2)

        # Decrease quantity
        self.client.post(reverse('cart:update', kwargs={'item_id': item.id}), {'action': 'decrease'})
        item.refresh_from_db()
        self.assertEqual(item.quantity, 1)

    # 6. Test Wishlist operations
    def test_06_wishlist(self):
        self.client.login(username='usera', password='Password@123')
        # Add to wishlist
        res = self.client.get(reverse('products:toggle_wishlist', kwargs={'product_id': self.product1.id}))
        self.assertTrue(Wishlist.objects.filter(user=self.user_a, product=self.product1).exists())

        # Toggle off
        res_off = self.client.get(reverse('products:toggle_wishlist', kwargs={'product_id': self.product1.id}))
        self.assertFalse(Wishlist.objects.filter(user=self.user_a, product=self.product1).exists())

    # 7. Test Product Comparison
    def test_07_compare_products(self):
        # Add to comparison
        res = self.client.get(reverse('products:toggle_compare', kwargs={'product_id': self.product1.id}))
        self.assertEqual(res.status_code, 302)
        compare_list = self.client.session.get('compare_list', [])
        self.assertIn(self.product1.id, compare_list)

        # View compare page
        comp_page = self.client.get(reverse('products:compare'))
        self.assertEqual(comp_page.status_code, 200)
        self.assertContains(comp_page, self.product1.name)

    # 8. Test Apply Coupon
    def test_08_apply_coupon(self):
        self.client.login(username='usera', password='Password@123')
        self.client.get(reverse('cart:add', kwargs={'product_id': self.product1.id}))
        
        # Apply valid coupon
        res = self.client.post(reverse('cart:apply_coupon'), {'coupon_code': 'TEST20'})
        cart = Cart.objects.get(user=self.user_a)
        self.assertEqual(cart.coupon, self.coupon)
        self.assertTrue(cart.discount_amount > 0)

    # 9 & 10. Complete Cash on Delivery order and verify stock updates
    def test_09_10_order_placement_and_stock_persistence(self):
        self.client.login(username='usera', password='Password@123')
        initial_stock = self.product1.stock
        
        # Add to cart (2 units)
        self.client.post(reverse('cart:add', kwargs={'product_id': self.product1.id}), {'quantity': 2})
        
        # Place order
        response = self.client.post(reverse('orders:place_order'), {
            'address_id': str(self.address_a.id),
            'payment_method': 'cod',
        })
        self.assertEqual(response.status_code, 302)
        
        # Verify order exists
        order = Order.objects.filter(user=self.user_a).first()
        self.assertIsNotNone(order)
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.items.first().quantity, 2)
        
        # Verify stock decreased atomically
        self.product1.refresh_from_db()
        self.assertEqual(self.product1.stock, initial_stock - 2)

    # 11. Test Order Tracking & History
    def test_11_order_tracking(self):
        self.client.login(username='usera', password='Password@123')
        self.client.get(reverse('cart:add', kwargs={'product_id': self.product1.id}))
        self.client.post(reverse('orders:place_order'), {
            'address_id': str(self.address_a.id),
            'payment_method': 'cod',
        })
        order = Order.objects.filter(user=self.user_a).first()
        
        # View tracking page
        track_res = self.client.get(reverse('orders:tracking', kwargs={'order_number': order.order_number}))
        self.assertEqual(track_res.status_code, 200)
        self.assertContains(track_res, order.order_number)

    # 12. Security Test: User B cannot access User A's order tracking
    def test_12_cross_user_order_isolation(self):
        # Create order for User A
        self.client.login(username='usera', password='Password@123')
        self.client.get(reverse('cart:add', kwargs={'product_id': self.product1.id}))
        self.client.post(reverse('orders:place_order'), {
            'address_id': str(self.address_a.id),
            'payment_method': 'cod',
        })
        order_a = Order.objects.filter(user=self.user_a).first()

        # Login as User B and try accessing User A's order tracking
        self.client.logout()
        self.client.login(username='userb', password='Password@123')
        res = self.client.get(reverse('orders:tracking', kwargs={'order_number': order_a.order_number}))
        # User B should receive 404 Not Found!
        self.assertEqual(res.status_code, 404)

    # 13. Security Test: Regular users cannot access Admin Dashboard
    def test_13_admin_access_control(self):
        # Regular user A tries accessing admin portal
        self.client.login(username='usera', password='Password@123')
        res_user = self.client.get(reverse('portal:dashboard'))
        # Should redirect to login or be rejected
        self.assertEqual(res_user.status_code, 302)

        # Admin user accesses admin portal
        self.client.logout()
        self.client.login(username='adminuser', password='Password@123')
        res_admin = self.client.get(reverse('portal:dashboard'))
        self.assertEqual(res_admin.status_code, 200)
        self.assertContains(res_admin, "Management Portal")

    # 14. Test AI Shopping Assistant endpoint
    def test_14_ai_assistant_engine(self):
        response = self.client.post(
            reverse('assistant:chat_api'),
            data={'query': 'Find smartphone under 15000'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertTrue(len(data['products']) > 0)
        self.assertEqual(data['products'][0]['name'], 'Redmi Note 13 5G')

    # 15. Test Out of stock error prevention
    def test_15_out_of_stock_prevention(self):
        self.client.login(username='usera', password='Password@123')
        # Try adding out of stock item
        res = self.client.get(reverse('cart:add', kwargs={'product_id': self.out_of_stock_product.id}))
        # Should redirect with error, cart should remain empty
        cart = Cart.objects.get(user=self.user_a)
        self.assertEqual(cart.total_items, 0)
