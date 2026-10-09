from django.db import models

class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.name} - {self.subject}"


class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email


class DeliveryPincode(models.Model):
    pincode = models.CharField(max_length=10, unique=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    estimated_days = models.PositiveIntegerField(default=3)
    is_serviceable = models.BooleanField(default=True)
    cod_available = models.BooleanField(default=True)

    class Meta:
        ordering = ['pincode']

    def __str__(self):
        return f"{self.pincode} - {self.city}, {self.state} ({self.estimated_days} days)"
