from django.urls import path, reverse

from . import views, FortiPoCSDWAN, sdwan1, sdwan2
import fpoc

# The 'name' of the paths are used in templates (html) and must be unique across whole apps of the project
# By registering a name for this app with variable 'app_name' it creates a context
# In the templates, the name must be referenced with {% url '<app_name>:<path.name>' %}
app_name = 'sdwan'

urlpatterns = [
    path('', views.HomePageView.as_view(), name='home'),
    path('about/', views.AboutPageView.as_view(), name='about'),
    # path('test/', views.display_request_parameters, name='display_request_parameters'),

    # Class instance (FortiPoCSDWAN()) must not be created here because it is created as a default argument of the function
    # Python evaluates default arguments when the function is defined and is NOT re-evaluated when the function is called
    # Which means that the exact same class instance is passed to the function each time
    # I must therefore create the class instance inside the function itself by passing the class name here
    # Creating the instance in this file (before the urlpatterns) does not work either
    path('poweron/', fpoc.pocs.poweron, {'Class_PoC': FortiPoCSDWAN}, name='poweron'),
    path('upgrade/', fpoc.pocs.upgrade, {'Class_PoC': FortiPoCSDWAN}, name='upgrade'),
    path('bootstrap/', fpoc.pocs.bootstrap, {'Class_PoC': FortiPoCSDWAN}, name='bootstrap'),

    path('dualdc_dualregion/', sdwan1.dualdc, name='dualdc_dualregion'),  # poc_id 9 and 10
    path('dualdc_dualregion2/', sdwan2.dualdc, name='dualdc_dualregion2'),  # poc_id 11

    # path('singlehub/bgp_per_overlay/fos62/', sdwan0.singlehub, {'poc_id': 5}, name='singlehub_fos62'),
    # poc6 = SDWAN+ADVPN Dual-DC with bgp-per-overlay for FOS 6.4
    # path('singlehub/bgp_per_overlay/fos70/', sdwan0.singlehub, {'poc_id': 8}, name='singlehub_fos70'),
]

