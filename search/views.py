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
ORDER_BY_DROPDOWN = [
    {'value': 'best', 'name': 'Best Sellers'},
    {'value': 'name', 'name': 'Name'},
    {'value': 'price', 'name':  'Price: Low to High'},
    {'value': '-price', 'name':  'Price: Low to High'},
]


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
    curr_brand = ''
    curr_order = ''

    def get_queryset(self):
        self.curr_brand = self.request.GET.get('brand', 'All')
        self.curr_order = self.request.GET.get('order_by', 'best')

        # brand filter
        if self.curr_brand == 'All':
            qs = Product.objects.all()
        else:
            qs = Product.objects.filter(brand=self.curr_brand)

        # order by
        if self.curr_order == 'best':
            qs = qs.order_by('-top_seller', 'top_seller_priority')
        elif 'price' in self.curr_order:
            qs = qs.annotate(price=Min('productitem__price')).order_by(self.curr_order)
        else:
            qs = qs.order_by(self.curr_order)

        return qs

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        # filters
        context['current_brand'] = self.curr_brand
        context['current_order'] = self.curr_order
        context['filters'] = {}
        if context['is_paginated']:
            page = context['page_obj']
            pages = [i for i in page.paginator.page_range if abs(i - page.number) < 5]
            context['pages'] = pages
            context['to_first_page'] = (pages[0] > 1)
            context['to_last_page'] = (pages[-1] < page.paginator.num_pages)
        # brand list
        brands = []
        try:
            brands_data = np.array(Product.objects.all().values_list('brand', 'sub_brand').distinct())
            if len(brands_data):
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
        context['order_by_menu'] = ORDER_BY_DROPDOWN
        # print(brands)
        return context


class ProductDetailView(DetailView):
    model = Product
    template_name = 'search/product.html'


class ProductListView(ListView):
    model = Product
    template_name = 'search/products.html'
