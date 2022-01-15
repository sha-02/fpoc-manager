import os
import jinja2


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