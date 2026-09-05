from .models import SiteConfiguration

def site_settings(request):
    # This looks for the settings in your database
    config = SiteConfiguration.objects.first()
    return {
        'site_config': config
    }