from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from config.settings import BASE_DIR

# dict of sites, the key must be consistent with the content of file 'site.txt'

sites = {
    'SDWAN/7.6_8.0/fabric/': 'fpoc.PoC_SDWAN.urls',
    'SDWAN/7.6_8.0/agora/': 'fpoc.PoC_SDWAN.urls',
    'SDWAN/7.4_7.6/fabric/': 'fpoc.PoC_SDWAN.urls',
    'SDWAN/7.4_7.6/agora/': 'fpoc.PoC_SDWAN.urls',
    'SDWAN/7.0_7.2/fabric/': 'fpoc.PoC_SDWAN.urls',
    'SDWAN/7.0_7.2/agora/': 'fpoc.PoC_SDWAN.urls',
    'VPN/': 'fpoc.PoC_VPN.urls',
    'One-Off/': 'fpoc.PoC_Once.urls'
}
default_site = 'SDWAN/7.6_8.0/fabric/'

# The first line of file 'site.txt' contains the URL of the site to start (kind of equivalent to index.html)
try:    # Check if there is a config file indicating which site is desired (first line in the file)
    with open(f"{BASE_DIR}/config/site.txt") as f:
        startup_site = f.readline().strip('\n')
except:  # something went wrong when attempting to read the config file
    startup_site = default_site

if sites.get(startup_site) is None:  # the site retrieved from config file is undefined
    startup_site = default_site

#
# Register the default URLs
#

urlpatterns = [
    path(route='admin/', view=admin.site.urls),
    path(route='accounts/', view=include('allauth.urls')),
    path(route='', view=RedirectView.as_view(url=startup_site)),     # Default site to start when URL is empty
]

#
# Register the URLs for each site defined in the 'sites' dict
#
# urlpatterns += [path(route=site_name, view=include(site['urls'])) for site_name, site in sites.items()]
urlpatterns += [path(route=path_, view=include(url_file), kwargs={'sites': sites})
                for path_, url_file in sites.items()]

# path('', include('fpoc.urls')),
# path('', RedirectView.as_view(url='PoC_VPN/')),
# path('PoC_VPN/', include('fpoc.PoC_VPN.urls')),


#
# Add URL for debug if needed
#
if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
                      path('__debug__/', include(debug_toolbar.urls)),
                  ] + urlpatterns
