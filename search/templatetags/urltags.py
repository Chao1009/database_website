from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def url_replace(context, **kwargs):
    query = context['request'].GET.copy()
    for k in kwargs.keys():
        if query.get(k):
            query.pop(k)
    query.update(kwargs)
    return query.urlencode()
