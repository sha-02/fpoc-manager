from django.urls import path

from . import views
import fpoc
from config.urls import sites

# The 'name' of the paths are used in templates (html) and must be unique across whole apps of the project
# By registering a name for this app with variable 'app_name' it creates a context
# In the templates, the name must be referenced with {% url '<app_name>:<path.name>' %}
app_name = 'poc'

urlpatterns = [
    path('', views.HomePageView.as_view(), {'sites': sites}, name='home'),

    path('about/', views.AboutPageView.as_view(), name='about'),
    # path('test/', views.display_request_parameters, name='display_request_parameters'),

    # Class instance (PoC_Once()) must not be created here because it is created as a default argument of the function
    # Python evaluates default arguments when the function is defined and is NOT re-evaluated when the function is called
    # Which means that the exact same class instance is passed to the function each time
    # I must therefore create the class instance inside the function itself by passing the class name here
    # Creating the instance in this file (before the urlpatterns) does not work either
    # path('poweron/', fpoc.views.poweron, {'Class_PoC': PoC_Once}, name='poweron'),
    # path('upgrade/', fpoc.views.upgrade, {'Class_PoC': PoC_Once}, name='upgrade'),
    # path('bootstrap/', fpoc.views.bootstrap, {'Class_PoC': PoC_Once}, name='bootstrap'),

    # New strategy for common views: the class required for the view is passed via the form
    path('poweron/', fpoc.views.poweron, name='poweron'),
    path('upgrade/', fpoc.views.upgrade, name='upgrade'),
    path('bootstrap/', fpoc.views.bootstrap, name='bootstrap'),
    path('dashboard/', fpoc.views.dashboard, name='dashboard'),

    # path('01/', fpoc.PoC_Once.poc01, {'poc_id': 1}, name='poc'),
    # 'name' is not used, the submit URL is built using the POC_ID defined in views.py
    path('01/', fpoc.PoC_Once.poc01, {'poc_id': 1}),
]
