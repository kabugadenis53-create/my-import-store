from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"

class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    # This line handles your file uploads
    image = models.ImageField(upload_to='product_images/', blank=True, null=True) 
    # This new line links each product to a category
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
class SiteConfiguration(models.Model):
    business_name = models.CharField(max_length=100, default="MEKLAS")
    contact_phone = models.CharField(max_length=20, default="(+254) 747900900")
    top_bar_message = models.CharField(max_length=200, default="Track My Order")

    class Meta:
        verbose_name = "Site Configuration"
        verbose_name_plural = "Site Configuration"

    def __str__(self):
        return self.business_name