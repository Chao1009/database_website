from django.contrib import admin
from .models import *
from import_export.admin import ImportExportModelAdmin
from import_export import fields, resources
from import_export.widgets import ForeignKeyWidget
from django.db.models import Count, Sum, Min, Max, DateTimeField
from django.db.models.functions import Trunc
import json


# use this to pass datetime values to js (ignore timezone now)
ISO8601_DT_FORMAT = '%Y-%m-%dT%H:%M:%S'


class ProductResource(resources.ModelResource):
    class Meta:
        model = Product
        skip_unchanged = True
        report_skipped = True
        exclude = ('id',)
        import_id_fields = ('sku',)


class ProductAdmin(ImportExportModelAdmin):
    resource_class = ProductResource
    list_filter = ('top_seller', 'category')
    list_display = ('name', 'sku', 'total_count', 'top_seller')
    list_editable = ('top_seller',)


class ProductItemResource(resources.ModelResource):
    product = fields.Field(
        column_name='product',
        attribute='product',
        widget=ForeignKeyWidget(Product, 'sku'))

    class Meta:
        model = ProductItem
        skip_unchanged = True
        report_skipped = True


class ProductItemAdmin(ImportExportModelAdmin):
    resource_class = ProductItemResource
    list_filter = ('product__category', 'product__brand', 'product')
    list_display = ('product', 'get_sku', 'size', 'storage_addr', 'sold', 'sold_price', 'sold_on', 'sold_by')
    list_editable = ('sold', 'sold_price', 'sold_on', 'sold_by')

    def get_sku(self, obj):
        return obj.product.sku
    get_sku.short_description = 'SKU'
    get_sku.admin_order_field = 'product__sku'

    def get_category(self, obj):
        return obj.product.category
    get_category.short_description = 'Category'
    get_category.admin_order_field = 'product__category'


class InventoryDatumResources(resources.ModelResource):

    class Meta:
        model = InventoryDatum
        skip_unchanged = True
        report_skipped = True


class InventoryDatumAdmin(ImportExportModelAdmin):
    resource_class = InventoryDatumResources


def get_next_in_date_hierarchy(request, date_hierarchy):
    if date_hierarchy + '__day' in request.GET:
        return 'hour'
    if date_hierarchy + '__month' in request.GET:
        return 'day'
    if date_hierarchy + '__year' in request.GET:
        return 'week'
    return 'month'


class SaleSummaryAdmin(admin.ModelAdmin):
    change_list_template = 'admin/dashboard/sales_change_list.html'
    actions = None
    date_hierarchy = 'sold_on'
    # Prevent additional queries for pagination.
    show_full_result_count = False
    list_filter = ('product__category', 'product__brand', 'product')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return True

    def has_module_permission(self, request):
        return True

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)

        # self.get_queryset would return the base queryset. ChangeList
        # apply the filters from the request so this is the only way to
        # get the filtered queryset.
        try:
            qs = response.context_data['cl'].queryset.filter(sold=True)
        except (AttributeError, KeyError):
            # See issue #172.
            # When an invalid filter is used django will redirect. In this
            # case the response is an http redirect response and so it has
            # no context_data.
            return response

        # List view
        metrics = {
            'total': Count('id'),
            'total_sales': Sum('sold_price'),
        }

        response.context_data['summary'] = list(
            qs.values('product__sku', 'product__name').annotate(**metrics).order_by('-total_sales')
        )

        # List view summary
        response.context_data['summary_total'] = dict(qs.aggregate(**metrics))

        # Chart
        period = get_next_in_date_hierarchy(request, self.date_hierarchy)
        response.context_data['period'] = period
        summary_over_time = qs.annotate(
            period=Trunc('sold_on', period, output_field=DateTimeField()),
        ).values('period')\
         .annotate(total=Sum('sold_price'))\
         .order_by('period')

        response.context_data['json_chart_data'] = json.dumps({
            'period': period,
            'sales_over_time': [{
                'x': x['period'].strftime(ISO8601_DT_FORMAT),
                'y': x['total'] or 0,
            } for x in summary_over_time]
        })

        return response


admin.site.register(Product, ProductAdmin)
admin.site.register(ProductItem, ProductItemAdmin)
admin.site.register(InventoryDatum, InventoryDatumAdmin)
admin.site.register(SaleSummary, SaleSummaryAdmin)
