from django.contrib import admin
from .models import Product, Category # Updated to include Category
from .models import SiteConfiguration # Add this to your imports at the top

# Added registration for the Category model
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)} # This auto-fills the slug as you type

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    # Added 'category' to the display list below
    list_display = ('name', 'category', 'price', 'stock', 'created_at')
    # Added a filter sidebar to help you sort by category
    list_filter = ('category',)
  

@admin.register(SiteConfiguration)
class SiteConfigurationAdmin(admin.ModelAdmin):
    # This prevents you from creating multiple settings; you just edit one
    def has_add_permission(self, request):
        return not SiteConfiguration.objects.exists()