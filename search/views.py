import requests
import random

from isodate import parse_duration

from django.conf import settings
from django.shortcuts import render, redirect
from django.db.models import Q
from django.views.generic import ListView, DetailView, View

from .models import Product, ProductItem


def index(request):
    items = []
    if request.method == 'POST':
        if request.POST['submit'] == 'lucky':
            allprod = list(Product.objects.all())
            items = random.sample(allprod, min(6, len(allprod)))
        else:
            search_str = request.POST['search']
            if search_str:
                items = Product.objects.filter(Q(sku__contains=search_str) | Q(name__contains=search_str))

    context = {
        'items': items
    }
    return render(request, 'search/index.html', context)


class ProductDetailView(DetailView):
    model = Product
    template_name = 'search/product.html'


class ProductListView(ListView):
    model = Product
    template_name = 'search/products.html'
