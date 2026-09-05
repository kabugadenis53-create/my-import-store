from django.contrib import admin
from .models import Product, QuoteRequest

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'base_price', 'is_active', 'created_at')
    search_fields = ('name',)

@admin.register(QuoteRequest)
class QuoteRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'product', 'status', 'admin_quote_amount', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('customer__username', 'product__name')
    readonly_fields = ('created_at', 'updated_at')
    
    # Organizes the admin interface
    fieldsets = (
        ('Customer Info', {
            'fields': ('customer', 'product', 'design_file', 'quantity', 'customer_notes')
        }),
        ('Management', {
            'fields': ('status', 'admin_quote_amount', 'admin_response_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )