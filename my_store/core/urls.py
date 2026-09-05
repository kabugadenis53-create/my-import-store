from django.contrib import admin
from django.urls import path, include
from django.conf import settings 
from django.conf.urls.static import static 

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('storefront.urls')),
    # ADDED: This connects the custom quote logic to your site
    path('quotes/', include('quotes.urls', namespace='quotes')),
] 

# This line allows Django to serve uploaded images while we are developing
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)