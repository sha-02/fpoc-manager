from django.urls import path

from . import views, pocs, FortiPoCFoundation1
import fpoc

# The 'name' of the paths are used in templates (html) and must be unique across whole apps of the project
# By registering a name for this app with variable 'app_name' it creates a context
# In the templates, the name must be referenced with {% url '<app_name>:<path.name>' %}
app_name = 'fpoc'

urlpatterns = [
    path('', views.HomePageView.as_view(), name='home'),
    path('about/', views.AboutPageView.as_view(), name='about'),
    path('test/', views.display_request_parameters, name='display_request_parameters'),

    # Class instance (FortiPoCFoundation1()) must not be created here because it is created as a default argument of the function
    # Python evaluates default arguments when the function is defined and is NOT re-evaluated when the function is called
    # Which means that the exact same class instance is passed to the function each time
    # I must therefore create the class instance inside the function itself by passing the class name here
    # Creating the instance in this file (before the urlpatterns) does not work either
    path('poweron/', fpoc.views.poweron, {'Class_PoC': FortiPoCFoundation1}, name='poweron'),
    path('upgrade/', fpoc.views.upgrade, {'Class_PoC': FortiPoCFoundation1}, name='upgrade'),
    path('bootstrap/', fpoc.views.bootstrap, {'Class_PoC': FortiPoCFoundation1}, name='bootstrap'),

    path('vpn/dialup/', pocs.vpn_dialup, {'poc_id': 2}, name='vpn_dialup'),
    path('vpn/site2site/', pocs.vpn_site2site, {'poc_id': 3}, name='vpn_site2site'),
    path('l2vpn/', pocs.l2vpn, {'poc_id': 1}, name='l2vpn'),
]
