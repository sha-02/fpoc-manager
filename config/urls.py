from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    # path('', include('pages.urls')),
    # path('', include('fpoc.urls')),
    path('', RedirectView.as_view(url='FortiPoCFoundation1/')),
    path('FortiPoCFoundation1/', include('fpoc.FortiPoCFoundation1.urls')),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
                      path('__debug__/', include(debug_toolbar.urls)),
                  ] + urlpatterns
