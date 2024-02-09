from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from config.settings import BASE_DIR

# List of FortiPoC/FortiLab projects

sites = {
    'FortiPoC_Foundation1/': 'fpoc.FortiPoCFoundation1.urls',
    'FortiPoC_SDWAN/': 'fpoc.FortiPoCSDWAN.urls',
}

# Which FortiPoC/FortiLab project is being managed ? (default is 'FortiPoCFoundation1')

try:    # Check if there is a config file indicating which site is desired in the first line of the file
    with open(f"{BASE_DIR}/config/site.txt") as f:
        site_to_manage = f.readline().strip('\n')
except: # something went wrong when attempting to read the config file, use 'FortiPoCFoundation1' as a default site
    site_to_manage = "FortiPoC_Foundation1/"

if sites.get(site_to_manage) is None:   # The site retrieved from the config file is unknown, default to 'FortiPoCFoundation1'
    site_to_manage = "FortiPoC_Foundation1/"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    # path('', include('fpoc.urls')),
    # path('', RedirectView.as_view(url='FortiPoCFoundation1/')),
    # path('FortiPoCFoundation1/', include('fpoc.FortiPoCFoundation1.urls')),
    path('', RedirectView.as_view(url=site_to_manage)),
] + [path(site_name, include(site_urls)) for site_name, site_urls in sites.items()]  # URL patterns for my sites


if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
                      path('__debug__/', include(debug_toolbar.urls)),
                  ] + urlpatterns
