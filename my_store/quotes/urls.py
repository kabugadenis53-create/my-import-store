from django.urls import path
from . import views

app_name = 'quotes'

urlpatterns = [
    # ADDED: Routes for the Quote Request system
    path('request/', views.request_quote, name='request_quote'),
    path('request/<int:product_id>/', views.request_quote, name='request_quote_with_product'),
]