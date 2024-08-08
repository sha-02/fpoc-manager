from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from config.settings import BASE_DIR

# dict of FortiPoC/FortiLab projects, the key must be consistent with the content of file 'site.txt'

sites = {
    'SDWAN/ADVPNv2/': 'fpoc.FortiPoCSDWAN.urls',
    'SDWAN/': 'fpoc.FortiPoCSDWAN.urls',
    'Foundation1/': 'fpoc.FortiPoCFoundation1.urls',
    'Airbus/': 'fpoc.FortiPoCAirbus.urls',
}

# Which FortiPoC/FortiLab project is being managed ? (default is 'FortiPoCFoundation1')

try:    # Check if there is a config file indicating which site is desired in the first line of the file
    with open(f"{BASE_DIR}/config/site.txt") as f:
        site_to_manage = f.readline().strip('\n')
except:  # something went wrong when attempting to read the config file
    site_to_manage = "SDWAN/ADVPNv2/"

if sites.get(site_to_manage) is None:  # site retrieved from config file is undefined
    site_to_manage = "SDWAN/ADVPNv2/"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    # path('', include('fpoc.urls')),
    # path('', RedirectView.as_view(url='FortiPoCFoundation1/')),
    # path('FortiPoCFoundation1/', include('fpoc.FortiPoCFoundation1.urls')),
    path('', RedirectView.as_view(url=site_to_manage)),
] + [path(site_name, include(site_urls)) for site_name, site_urls in sites.items()]  # add URL path() for each 'sites' entry


if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
                      path('__debug__/', include(debug_toolbar.urls)),
                  ] + urlpatterns
