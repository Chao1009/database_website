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


cat_size = json.load(open(staticfiles_storage.path('cat_size.json')))


def index(request):
    cats = [{'name': c, 'selected': False} for c in cat_size.keys()]
    items = []

    if request.method == 'POST':
        if 'categories' not in request.POST.keys():
            products = Product.objects.all()

        else:
            cat = request.POST['categories']
            products = Product.objects.filter(category=cat)
            cats = [{'name': c, 'selected': False if c != cat else True} for c in cat_size.keys()]
        if request.POST['submit'] == 'top':
            items = list(products.filter(top_seller=True).order_by('top_seller_priority'))
            if len(items) > 10:
                items = items[:10]
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
