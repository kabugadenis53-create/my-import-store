from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .forms import QuoteRequestForm
from .models import Product

@login_required
def request_quote(request, product_id=None):
    product = None
    if product_id:
        product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        form = QuoteRequestForm(request.POST, request.FILES)
        if form.is_valid():
            quote = form.save(commit=False)
            quote.customer = request.user
            
            # Ensure the product is linked if it was passed via the URL
            if product:
                quote.product = product
                
            quote.save()
            
            # HTMX Logic: If the request comes from HTMX, return the professional success partial
            if request.htmx:
                return render(request, 'quotes/partials/success.html')
            
            # Standard fallback for non-HTMX requests
            return render(request, 'quotes/success.html')
    else:
        # Pre-fill the form with the product if coming from a specific product page
        form = QuoteRequestForm(initial={'product': product})

    return render(request, 'quotes/quote_form.html', {'form': form, 'product': product})