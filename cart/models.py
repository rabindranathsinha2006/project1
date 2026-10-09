from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from products.models import Product
from decimal import Decimal

class Coupon(models.Model):
    DISCOUNT_TYPES = (
        ('percentage', 'Percentage Discount (%)'),
        ('fixed', 'Fixed Amount Discount (₹)'),
    )

    code = models.CharField(max_length=30, unique=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES, default='percentage')
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    min_purchase = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    max_discount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    valid_from = models.DateTimeField(default=timezone.now)
    valid_to = models.DateTimeField()
    usage_limit = models.PositiveIntegerField(default=100)
    times_used = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.code} ({self.discount_value}{'%' if self.discount_type == 'percentage' else '₹'} off)"

    def is_valid(self, subtotal=Decimal('0.00')):
        now = timezone.now()
        if not self.is_active:
            return False, "This coupon is not active."
        if now < self.valid_from or now > self.valid_to:
            return False, "This coupon has expired or is not yet valid."
        if self.times_used >= self.usage_limit:
            return False, "This coupon usage limit has been reached."
        if subtotal < self.min_purchase:
            return False, f"Minimum purchase amount of ₹{self.min_purchase} required to use this coupon."
        return True, "Coupon is valid."

    def calculate_discount(self, subtotal):
        if subtotal <= 0:
            return Decimal('0.00')
        if self.discount_type == 'percentage':
            discount = (subtotal * self.discount_value) / Decimal('100.00')
            if self.max_discount and discount > self.max_discount:
                discount = self.max_discount
        else:
            discount = min(self.discount_value, subtotal)
        return round(discount, 2)


class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name='cart')
    session_key = models.CharField(max_length=60, null=True, blank=True)
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.user:
            return f"Cart of {self.user.username}"
        return f"Guest Cart ({self.session_key})"

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def subtotal(self):
        return sum(item.line_total for item in self.items.all())

    @property
    def discount_amount(self):
        if self.coupon:
            valid, _ = self.coupon.is_valid(self.subtotal)
            if valid:
                return self.coupon.calculate_discount(self.subtotal)
        return Decimal('0.00')

    @property
    def shipping_cost(self):
        sub = self.subtotal
        if sub == 0:
            return Decimal('0.00')
        # Free shipping over ₹999, else flat ₹99
        return Decimal('0.00') if sub >= Decimal('999.00') else Decimal('99.00')

    @property
    def final_total(self):
        total = self.subtotal - self.discount_amount + self.shipping_cost
        return max(Decimal('0.00'), round(total, 2))


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('cart', 'product')
        ordering = ['added_at']

    def __str__(self):
        return f"{self.quantity}x {self.product.name}"

    @property
    def line_total(self):
        return self.product.effective_price * self.quantity
