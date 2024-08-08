import os
import jinja2

from django.urls import reverse
from django.contrib.staticfiles.storage import staticfiles_storage
# for more later django installations use:
# from django.templatetags.static import static

# ATTENTION: package 'netaddr' MUST BE INSTALLED otherwise calls to ipaddr() filter simply return "False"
# Both the below import are Ok
# from ansible_collections.ansible.utils.plugins.plugin_utils.base.ipaddr_utils import ipaddr
from ansible_collections.ansible.utils.plugins.filter.ipaddr import ipaddr


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

    # Adds Ansible 'ipaddr' filter to Jinja2
    env.filters['ipaddr'] = ipaddr

    return env
