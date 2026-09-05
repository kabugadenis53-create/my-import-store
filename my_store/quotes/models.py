from django.db import models
from django.contrib.auth.models import User

class Product(models.Model):
    """
    Items available for importing/pre-ordering.
    """
    name = models.CharField(max_length=255)
    description = models.TextField()
    base_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Starting price per unit")
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    # Added null=True to allow migration of existing rows
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return self.name

class QuoteRequest(models.Model):
    """
    The core business logic: A customer uploads a design for a specific product.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('quoted', 'Quote Sent'),
        ('approved', 'Approved / Paid'),
        ('rejected', 'Rejected'),
        ('shipped', 'Shipped'),
    ]

    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quotes')
    # Added null=True, blank=True to allow migration of existing rows
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    
    # This file goes to Supabase Storage as per settings.py
    design_file = models.FileField(
        upload_to='design_uploads/%Y/%m/', 
        help_text="Upload your blueprint or design file"
    )
    
    quantity = models.PositiveIntegerField(default=1)
    customer_notes = models.TextField(blank=True, help_text="Specific requirements or customization details")
    
    # Admin-controlled fields
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_quote_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    admin_response_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Quote #{self.id} for {self.customer.username} - {self.product.name}"