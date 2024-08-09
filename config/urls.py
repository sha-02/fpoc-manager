from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from config.settings import BASE_DIR

# dict of sites, the key must be consistent with the content of file 'site.txt'

sites = {
    'SDWAN/ADVPNv2/fortipoc/': {'urls': 'fpoc.FortiPoCSDWAN.urls', 'selected': False},
    'SDWAN/fortipoc/': {'urls': 'fpoc.FortiPoCSDWAN.urls', 'selected': False},
    'SDWAN/ADVPNv2/hardware/': {'urls': 'fpoc.FortiPoCSDWAN.urls', 'selected': False},
    'SDWAN/hardware/': {'urls': 'fpoc.FortiPoCSDWAN.urls', 'selected': False},
    'Foundation1/': {'urls': 'fpoc.FortiPoCFoundation1.urls', 'selected': False},
    'Airbus/': {'urls': 'fpoc.FortiPoCAirbus.urls', 'selected': False}
}

# The first line of file 'site.txt' contains the URL of the site to start (kind of equivalent to index.html principle) ?

try:    # Check if there is a config file indicating which site is desired in the first line of the file
    with open(f"{BASE_DIR}/config/site.txt") as f:
        startup_site = f.readline().strip('\n')
except:  # something went wrong when attempting to read the config file
    startup_site = "Foundation1/"

if sites.get(startup_site) is None:  # the site retrieved from config file is undefined
    startup_site = "Foundation1/"

#
# Register the default URLs
#

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('', RedirectView.as_view(url=startup_site)),     # Default site to start when URL is empty
]

#
# Register the URLs for each site defined in the 'sites' dict
#

urlpatterns += [path(site_name, include(site['urls'])) for site_name, site in sites.items()]

# path('', include('fpoc.urls')),
# path('', RedirectView.as_view(url='FortiPoCFoundation1/')),
# path('FortiPoCFoundation1/', include('fpoc.FortiPoCFoundation1.urls')),


#
# Add URL for debug if needed
#
if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
                      path('__debug__/', include(debug_toolbar.urls)),
                  ] + urlpatterns
