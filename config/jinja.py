import os
import jinja2
import ipaddress

from django.urls import reverse
from django.contrib.staticfiles.storage import staticfiles_storage
# for more later django installations use:
# from django.templatetags.static import static

# ATTENTION: package 'netaddr' MUST BE INSTALLED otherwise calls to ipaddr() filter simply return "False"
# Both the below import are Ok
# from ansible_collections.ansible.utils.plugins.plugin_utils.base.ipaddr_utils import ipaddr
from ansible_collections.ansible.utils.plugins.filter.ipaddr import ipaddr
from ansible_collections.ansible.utils.plugins.filter.ipmath import ipmath


# Using Jinja2 with Django:
# https://samuh.medium.com/using-jinja2-with-django-1-8-onwards-9c58fe1204dc


class JinjaEnvironment(jinja2.Environment):
    def __init__(self, **kwargs):
        super(JinjaEnvironment, self).__init__(**kwargs)

    # Goal is to be able to use relative paths in templates: for e.g. {% include ./FGT.conf %}
    # Instead of having to indicate the full template path (default behavior): e.g. {% include fpoc/fpoc05/FGT.conf %}
    # https://stackoverflow.com/questions/2180247/does-the-jinja2-templating-language-have-the-concept-of-here-current-director
    # https://jinja.palletsprojects.com/en/3.0.x/api/#jinja2.Environment.join_path
    # https://stackoverflow.com/questions/30701631/how-to-use-jinja2-as-a-templating-engine-in-django-1-8
    """Override join_path() to enable relative template paths."""

    def join_path(self, template, parent):
        return os.path.join(os.path.dirname(parent), template)


def environment(**options):
    # Create an environment out of the JinJaEnvironment class defined above
    env = JinjaEnvironment(**options)

    # Allows to use Django template tags like {% url “index” %} or {% static “path/to/static/file.js” %}
    # in Jinja2 templates
    env.globals.update({
        "static": staticfiles_storage.url,
        "url": reverse
        })

    # Allow to use Python built-in function isinstance() in Jinja templates for Checking the type of variable in Jinja2
    # Another alternative is to test like this:  var.__class__.__name__ == 'list'  to check if 'var' is a list
    env.globals.update({"isinstance": isinstance})

    # Adds Ansible filters to Jinja2
    env.filters['ipaddr'] = ipaddr
    env.filters['ipmath'] = ipmath

    # Add my own Jinja2 filters
    env.filters['ipv4_to_ipv6'] = ipv4_to_ipv6


    return env


# def ipv4_to_ipv6(ipv4addr):
#     """
#     Converts an IPv4 address (for eg, 10.1.2.3) into an IPv6 address (2000:10:1:2::3)
#     The resulting IPv6 address always starts with 2000
#     """
#     a, b, c, d = ipv4addr.split('.')
#     return f"2000:{a}:{b}:{c}::{d}"

def ipv4_to_ipv6(ipv4:str)-> str:
    """
    Convert an ipv4 address into an ipv6 address
        10.1.2.3                       -> 2000:10:1:2::3
        10.1.2.3/32                    -> 2000:10:1:2::3/128
        10.1.2.3/31                    -> 2000:10:1:2::3/127
        10.1.2.3/30                    -> 2000:10:1:2::3/126
        10.1.2.3/24                    -> 2000:10:1:2::3/64
        10.1.2.3/16                    -> 2000:10:1:2::3/48
        10.1.2.3/8                     -> 2000:10:1:2::3/32
        10.1.2.3 255.255.255.255       -> 2000:10:1:2::3/128
        10.1.2.3 255.255.255.254       -> 2000:10:1:2::3/127
        10.1.2.3 255.255.255.252       -> 2000:10:1:2::3/126
        10.1.2.3 255.255.255.0         -> 2000:10:1:2::3/64
        10.1.2.3 255.255.0.0           -> 2000:10:1:2::3/48
        10.1.2.3 255.0.0.0             -> 2000:10:1:2::3/32

        Mask or prefix-length which are not listed in the PREFIX_MAP are converted to /128
        10.1.2.3/20                    -> 2000:10:1:2::3/128
        10.1.2.3 255.255.240.0         -> 2000:10:1:2::3/128
    """
    # IPv4 prefix -> IPv6 prefix mapping
    PREFIX_MAP = {
        32: 128,
        31: 127,
        30: 126,
        24: 64,
        16: 48,
        8: 32,
    }

    ipv4 = ipv4.strip()

    ip_part = None
    prefix = None

    # Format: a.b.c.d/prefix
    if "/" in ipv4:
        iface = ipaddress.IPv4Interface(ipv4)
        ip_part = str(iface.ip)
        prefix = iface.network.prefixlen

    # Format: a.b.c.d mask
    elif " " in ipv4:
        ip_part, mask = ipv4.split(None, 1)
        prefix = ipaddress.IPv4Network(f"0.0.0.0/{mask}").prefixlen

    # Format: a.b.c.d
    else:
        ip_part = ipv4

    # Validate IPv4 address and extract octets
    a, b, c, d = map(int, ip_part.split("."))
    ipaddress.IPv4Address(ip_part)  # validation

    ipv6 = f"2000:{a}:{b}:{c}::{d}"

    if prefix is None:
        return ipv6

    ipv6_prefix = PREFIX_MAP.get(prefix, 128)
    return f"{ipv6}/{ipv6_prefix}"