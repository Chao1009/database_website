import re
import requests
import random
import json
from isodate import parse_duration

from django.conf import settings
from django.shortcuts import render, redirect
from django.db.models import Q
from django.views.generic import ListView, DetailView, View

from .models import *
from django.contrib.staticfiles.storage import staticfiles_storage


N_TOP_SELLER = 6
cat_size = json.load(open(staticfiles_storage.path('cat_size.json')))


def humanized_sort(lt):
    def convert(text):
        return float(text) if text.isdigit() else text

    def alphanum(key):
        return [convert(c) for c in re.split(r'([-+]?[0-9]*\.?[0-9]+)', key)]

    lt.sort(key=alphanum)
    return lt


def index(request):
    brands = Product.objects.all().values_list('brand', 'sub_brand').distinct()
    d = {}
    for x, y in list(brands):
        d.setdefault(x, []).append(y)
    for key, values in d.items():
        d[key] = humanized_sort(values)
    context = {
        'brands': list(d.keys())
    }
    print(context)
    return render(request, 'search/index_new.html', context)


def search(request):
    cats = [{'name': 'All', 'selected': True}]\
         + [{'name': c, 'selected': False} for c in cat_size.keys()]
    items = []

    if request.method == 'POST':
        print(request.POST)
        if 'categories' not in request.POST.keys() or request.POST['categories'] == 'All':
            products = Product.objects.all()

        else:
            cat = request.POST['categories']
            products = Product.objects.filter(category=cat)
            cats = [{'name': 'All', 'selected': False}]\
                 + [{'name': c, 'selected': False if c != cat else True} for c in cat_size.keys()]
        if request.POST['submit'] == 'top':
            items = list(products.filter(top_seller=True).order_by('top_seller_priority'))
            if len(items) > N_TOP_SELLER:
                items = items[:N_TOP_SELLER]
        else:
            search_str = request.POST['search']
            items = products.filter(Q(sku__contains=search_str) | Q(name__contains=search_str))

    context = {
        'categories': cats,
        'items': items
    }
    return render(request, 'search/index.html', context)


class ProductDetailView(DetailView):
    model = Product
    template_name = 'search/product.html'


class ProductListView(ListView):
    model = Product
    template_name = 'search/products.html'
