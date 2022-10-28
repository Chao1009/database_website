from django import template
import urllib

register = template.Library()


@register.simple_tag(takes_context=True)
def url_replace(context, **kwargs):
    query = context['request'].GET.copy()
    for k in kwargs.keys():
        if query.get(k):
            query.pop(k)
    query.update(kwargs)
    return query.urlencode()


@register.simple_tag(takes_context=True)
def url_update(context, **kwargs):
    query = context['request'].GET.copy()
    query.update(kwargs)
    return query.urlencode()


@register.filter(name='inlist')
def inlist(value, encodedlist):
    lst = [urllib.parse.unquote(x) for x in encodedlist.split(',')]
    return value in lst
