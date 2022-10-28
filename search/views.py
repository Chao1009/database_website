import re
import requests
import random
import json
import numpy as np
from natsort import natsorted
from isodate import parse_duration

from django.db.utils import OperationalError
from django.conf import settings
from django.shortcuts import render, redirect
from django.db.models import Q
from django.views.generic import ListView, DetailView, View
from django.core.paginator import InvalidPage
from django.http import Http404

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


# assuming size code is always number or number + 1 character
def sort_size(size_list):
    def size_key(size_str):
        try:
            if size_str[-1].isdigit():
                return ' ', float(size_str)
            else:
                return size_str[-1], float(size_str[:-1])
        except ValueError:
            # a large number to be at the bottom
            return '~', 999.
    return sorted(size_list, key=size_key)


class HomeView(ListView):
    model = Product
    template_name = 'search/home.html'
    paginate_by = 9

    curr_brand = ''
    curr_order = ''
    curr_filters = {}
    price_range = (0, 2500)

    size_groups = []
    sub_brands = []
    brands = []
    try:
        brands_data = Product.objects.all().values_list('brand', 'sub_brand').distinct()
        if len(brands_data):
            brands_data = np.array(brands_data)
            allsubs = []
            for b in np.unique(brands_data.T[0]):
                subs = natsorted(list(brands_data[brands_data.T[0] == b].T[1]))
                brands.append({'name': b, 'models': subs})
                allsubs += subs
            # brands.append({'name': 'All', 'models': allsubs})
            brands.sort(key=lambda x: len(x['models']), reverse=True)
    except OperationalError:
        print('Warning: no product data entries')

    def paginate_queryset(self, queryset, page_size):
        """Paginate the queryset, if needed."""
        paginator = self.get_paginator(
                queryset, page_size, orphans=self.get_paginate_orphans(),
                allow_empty_first_page=self.get_allow_empty())
        page_kwarg = self.page_kwarg
        page = self.kwargs.get(page_kwarg) or self.request.GET.get(page_kwarg) or 1
        try:
            page_number = int(page)
        except ValueError:
            if page == 'last':
                page_number = paginator.num_pages
            else:
                raise Http404("Page is not 'last', nor can it be converted to an int.")
        try:
            page = paginator.page(page_number)
            return paginator, page, page.object_list, page.has_other_pages()
        except InvalidPage as e:
            # <-first page
            page_number = 1
            page = paginator.page(page_number)
            # <-return first page
            return paginator, page, page.object_list, page.has_other_pages()

    def get_queryset(self):
        print(self.request.GET)
        self.curr_brand = self.request.GET.get('brand', 'All')
        self.curr_order = self.request.GET.get('order_by', 'best')

        # brands
        if self.curr_brand == 'All':
            qs = Product.objects.all()
        else:
            qs = Product.objects.filter(brand=self.curr_brand)

        # annotation
        qs = qs.annotate(price=Min('productitem__price'))

        # get all models and sizes before applying additional filters (only major brand filter)
        self.sub_brands = natsorted(list(np.unique(qs.values_list('sub_brand', flat=True))))
        size_grp = {}
        sizes = [s for s in qs.values_list('productitem__size', flat=True) if s]
        for size in np.unique(sizes):
            if size[-1].isdigit():
                size_grp['digit'] = size_grp.get('digit', []) + [size]
            else:
                size_grp[size[-1]] = size_grp.get(size[-1], []) + [size]
        self.size_groups = [sort_size(values) for _, values in size_grp.items()]
        # print(self.size_groups)

        # additional filters
        self.curr_filters = {}
        list_filters = [
            ('sub_brand', 'sub_brand'),
            ('size', 'productitem__size'),
        ]
        for flt, keyval in list_filters:
            flt_val = self.request.GET.get(flt, '')
            flt_val = flt_val.split(',') if flt_val else []
            self.curr_filters.update({flt: flt_val})
            if len(flt_val):
                qs = qs.filter(**{'{}__in'.format(keyval): flt_val})
        # price range
        try:
            self.price_range = (
                float(self.request.GET.get('min_price', '0')), float(self.request.GET.get('max_price', '2500'))
            )
            qs = qs.filter(Q(price__gte=self.price_range[0]) & Q(price__lte=self.price_range[1]))
        except ValueError:
            self.price_range = (0, 2500)

        # order by
        if self.curr_order == 'best':
            qs = qs.order_by('-top_seller', 'top_seller_priority')
        else:
            qs = qs.order_by(self.curr_order)

        return qs

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        # brand list
        context['brands'] = self.brands
        context['models'] = self.sub_brands
        # special treatment for sizes, group for columns
        n_size_col = 3
        lst = []
        for ll in self.size_groups:
            nn = len(ll) % n_size_col
            if nn > 0:
                nn = n_size_col - nn
            lst += ll + ['']*nn
        context['size_groups'] = list(zip(*[iter(lst)]*n_size_col))
        context['current_brand'] = self.curr_brand
        context['current_order'] = self.curr_order
        context['current_filters'] = self.curr_filters
        context['min_price'] = self.price_range[0]
        context['max_price'] = self.price_range[0]
        if context['is_paginated']:
            page = context['page_obj']
            pages = [i for i in page.paginator.page_range if abs(i - page.number) < 5]
            context['pages'] = pages
            context['to_first_page'] = (pages[0] > 1)
            context['to_last_page'] = (pages[-1] < page.paginator.num_pages)
        context['order_by_menu'] = ORDER_BY_DROPDOWN
        # print(brands)
        return context


class ProductDetailView(DetailView):
    model = Product
    template_name = 'search/product.html'


class ProductListView(ListView):
    model = Product
    template_name = 'search/products.html'
