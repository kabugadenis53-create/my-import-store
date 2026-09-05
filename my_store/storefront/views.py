from django.shortcuts import render
from .models import Product

def product_list(request):
    # This gets all products from your Supabase database
    products = Product.objects.all()
    
    # This sends those products to an HTML file (we will create it next)
    return render(request, 'storefront/index.html', {'products': products})