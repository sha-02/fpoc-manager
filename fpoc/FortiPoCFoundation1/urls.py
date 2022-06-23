from django.urls import path

from . import views, pocs

# The 'name' of the paths are used in templates (html) and must be unique across whole apps of the project
# By registering a name for this app with variable 'app_name' it creates a context
# In the templates, the name must be referenced with {% url '<app_name>:<path.name>' %}
app_name = 'fpoc'

urlpatterns = [
    path('', views.HomePageView.as_view(), name='home'),
    path('about/', views.AboutPageView.as_view(), name='about'),
    path('test/', views.display_request_parameters, name='display_request_parameters'),

    path('poweron/', pocs.poweron, name='poweron'),
    path('upgrade/', pocs.upgrade, name='upgrade'),
    path('bootstrap/', pocs.bootstrap, {'poc_id': 0}, name='bootstrap'),

    path('sdwan/simple/', pocs.sdwan_simple, {'poc_id': 1}, name='sdwan_simple'),

    # Single Hub ADVPN+SDWAN
    path('sdwan_advpn/singlehub/bgp_per_overlay/fos62/', pocs.sdwan_advpn_singlehub, {'poc_id': 5}, name='sdwan_advpn_singlehub_fos62'),
    path('sdwan_advpn/singlehub/bgp_per_overlay/fos70/', pocs.sdwan_advpn_singlehub, {'poc_id': 8}, name='sdwan_advpn_singlehub_fos70'),

    # Dual-DC, Dual-Region with different designs:
    # - "one BGP peering per overlay" design
    # - "BGP without route reflection" design
    path('sdwan_advpn/dualdc/bgp_per_overlay/fos64/', pocs.sdwan_advpn_dualdc, {'poc_id': 6}, name='sdwan_advpn_dualdc_fos64'),
    path('sdwan_advpn/dualdc/bgp_per_overlay/fos70/', pocs.sdwan_advpn_dualdc, {'poc_id': 9}, name='sdwan_advpn_dualdc_fos70'),
    path('sdwan_advpn/dualdc/bgp_per_overlay/bgp_no_rr/', pocs.sdwan_advpn_dualdc, {'poc_id': 7}, name='sdwan_advpn_nobgprr'),

    path('vpn/dialup/', pocs.vpn_dialup, {'poc_id': 2}, name='vpn_dialup'),
    path('vpn/site2site/', pocs.vpn_site2site, {'poc_id': 3}, name='vpn_site2site'),
    path('vpn/dualhub/singletunnel/', pocs.vpn_dualhub_singletunnel, {'poc_id': 4}, name='vpn_dualhub_singletunnel'),
]

# TODO list
"""
- suspend devices which are not used for a poc
  if a device is used for a poc and it is currently suspended, resume it

Usability:
----------
- once a config has been pushed to a device, store this new config in its revision history using poc_id
  would need to find a way to store info about 'context' as well
  --> tried in deploy_config() but the comment field is very limited in size so cannot write the whole 'context' there
  
- Use class Form to store the context elements of a scenario and generate the HTML code with template where the 
  accordion are all created automatically  

- Enrich the print() statement with the Rich class
    RED color when device is skipped
    ORANGE color when retries
    GREEN color when device is finished processing
    Add the name of the device to the beginning of each line, similar to a debug => needed for threading
"""
