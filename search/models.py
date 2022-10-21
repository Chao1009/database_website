# from django.conf import settings
from django.db import models
from django.urls import reverse
from django.db.models import Count, Min, Max
import datetime as dt
from django.core.validators import MaxValueValidator, MinValueValidator
# from django.utils import timezone
# from django.db.models.signals import post_save
# from django.db.models import Sum
# from django.shortcuts import reverse
# from django_countries.fields import CountryField


def extract_size_digits(size_str):
    istop = len(size_str)
    for i in range(len(size_str)):
        if not size_str[i].isdigit() and size_str[i] not in '.-+':
            istop = i
            break
    return 0 if not istop else float(size_str[:istop])


# Product (unique SKU)
class Product(models.Model):
    sku = models.CharField(max_length=50, default='0', primary_key=True)
    name = models.CharField(max_length=100)
    brand = models.CharField(max_length=30, blank=True)
    category = models.CharField(max_length=20, blank=True)
    image_src = models.CharField(max_length=255, blank=True)
    first_created_on = models.DateTimeField(null=True, blank=True)
    top_seller = models.BooleanField(
        default=False,
        help_text='Check it and this product will be shown as topsellers',
    )
    top_seller_priority = models.IntegerField(
        default=1,
        validators=[MaxValueValidator(10), MinValueValidator(1)],
        help_text='With 1 the top priority and 10 the lowest',
    )

    def __str__(self):
        return self.name

    def absolute_url(self):
        return reverse('product_detail', args=[str(self.sku)])

    def price_range(self, size='all'):
        items = ProductItem.objects.filter(product=self)
        if size != 'all':
            items = items.filter(size=size)
        prices = [item.price for item in items]
        min_price, max_price = min(prices), max(prices)
        if min_price != max_price:
            return '${:.2f} - ${:.2f}'.format(min_price, max_price)
        return '${:.2f}'.format(min_price)

    def summary(self):
        results = ProductItem.objects.filter(product=self)\
                  .values('size')\
                  .annotate(count=Count('size'), price=Min('price'))
        return sorted(results, key=lambda x: extract_size_digits(x['size']))

    def total_count(self):
        return len(ProductItem.objects.filter(product=self))

    def is_new(self, max_days=30):
        if not self.first_created_on.null():
            start_date = dt.datetime.strptime(self.first_created_on, '%Y-%m-%d %H:%M:%S')
            end_date = dt.datetime.today()
            return (end_date - start_date).days < max_days
        return False


# Product Item (individual item for each product)
class ProductItem(models.Model):
    id = models.CharField(max_length=50, primary_key=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.FloatField()
    stockx_price = models.CharField(max_length=50)
    discount_price = models.FloatField(blank=True, null=True)
    size = models.CharField(max_length=10)
    added_on = models.DateTimeField(null=False, blank=False, auto_now_add=True)

    storage_loc = models.CharField(max_length=50)
    storage_addr = models.CharField(max_length=255)

    sold = models.BooleanField(default=False)
    sold_price = models.FloatField(null=True, blank=True)
    sold_on = models.DateTimeField(null=True, blank=True)
    sold_by = models.CharField(max_length=50, null=True, blank=True)

    lost = models.BooleanField(default=False)
    lost_on = models.DateTimeField(null=True, blank=True)
    lost_cost = models.FloatField(blank=True, null=True)

    def __str__(self):
        return self.product.name


# a data model to check the stock
class StockItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    size = models.CharField(max_length=10)
    counts = models.IntegerField(default=1, validators=[MinValueValidator(0)])
    checked_on = models.DateTimeField(null=False, blank=False, auto_now_add=True)

    def __str__(self):
        return self.product.name
