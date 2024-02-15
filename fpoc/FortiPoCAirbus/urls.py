from django.urls import path

from . import views, pocs, FortiPoCAirbus
import fpoc

# The 'name' of the paths are used in templates (html) and must be unique across whole apps of the project
# By registering a name for this app with variable 'app_name' it creates a context
# In the templates, the name must be referenced with {% url '<app_name>:<path.name>' %}
app_name = 'airbus'

urlpatterns = [
    path('', views.HomePageView.as_view(), name='home'),
    path('about/', views.AboutPageView.as_view(), name='about'),
    # path('test/', views.display_request_parameters, name='display_request_parameters'),

    # Class instance (FortiPoCSDWAN()) must not be created here because it is created as a default argument of the function
    # Python evaluates default arguments when the function is defined and is NOT re-evaluated when the function is called
    # Which means that the exact same class instance is passed to the function each time
    # I must therefore create the class instance inside the function itself by passing the class name here
    # Creating the instance in this file (before the urlpatterns) does not work either
    path('poweron/', fpoc.pocs.poweron, {'Class_PoC': FortiPoCAirbus}, name='poweron'),
    path('upgrade/', fpoc.pocs.upgrade, {'Class_PoC': FortiPoCAirbus}, name='upgrade'),
    path('bootstrap/', fpoc.pocs.bootstrap, {'Class_PoC': FortiPoCAirbus}, name='bootstrap'),

    path('bgp_loopback/', pocs.airbus, name='airbus'),
]
