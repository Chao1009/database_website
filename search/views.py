import re
import requests
import random
import json
import numpy as np
from isodate import parse_duration

from django.db.utils import OperationalError
from django.conf import settings
from django.shortcuts import render, redirect
from django.db.models import Q
from django.views.generic import ListView, DetailView, View

from .models import *
from django.contrib.staticfiles.storage import staticfiles_storage

N_TOP_SELLER = 6
CAT_SIZE = json.load(open(staticfiles_storage.path('cat_size.json')))


def humanized_sort(lt):
    def convert(text):
        return float(text) if text.isdigit() else text

    def alphanum(key):
        return [convert(c) for c in re.split(r'([-+]?[0-9]*\.?[0-9]+)', key)]

    lt.sort(key=alphanum)
    return lt


class HomeView(ListView):
    model = Product
    template_name = 'search/home.html'
    paginate_by = 9

    def get_queryset(self):
        brand = self.request.GET.get('brand', 'All')
        order = self.request.GET.get('orderby', 'sku')
        if brand == 'All':
            qs = Product.objects.all()
        else:
            qs = Product.objects.filter(brand=brand).order_by(order)
        print(qs.count())
        return qs

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        # filters
        brand = self.request.GET.get('brand', 'All')
        context['current_brand'] = brand
        context['filters'] = {}
        # brand list
        brands = []
        try:
            brands_data = np.array(Product.objects.all().values_list('brand', 'sub_brand').distinct())
            allsubs = []
            for b in np.unique(brands_data.T[0]):
                subs = humanized_sort(list(brands_data[brands_data.T[0] == b].T[1]))
                brands.append({'name': b, 'models': subs})
                allsubs += subs
            brands.append({'name': 'All', 'models': allsubs})
            brands.sort(key=lambda x: len(x['models']), reverse=True)
        except OperationalError:
            print('Warning: no product data entries')
        context['brands'] = brands
        print(brands)
        return context


def search(request):
    cats = [{'name': 'All', 'selected': True}]\
         + [{'name': c, 'selected': False} for c in CAT_SIZE.keys()]
    items = []

    if request.method == 'POST':
        print(request.POST)
        if 'categories' not in request.POST.keys() or request.POST['categories'] == 'All':
            products = Product.objects.all()

        else:
            cat = request.POST['categories']
            products = Product.objects.filter(category=cat)
            cats = [{'name': 'All', 'selected': False}]\
                 + [{'name': c, 'selected': False if c != cat else True} for c in CAT_SIZE.keys()]
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
