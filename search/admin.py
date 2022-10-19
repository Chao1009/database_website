from django.contrib import admin

from .models import Product, ProductItem
from import_export.admin import ImportExportModelAdmin
from import_export import fields, resources
from import_export.widgets import ForeignKeyWidget


class ProductResource(resources.ModelResource):
    class Meta:
        model = Product
        skip_unchanged = True
        report_skipped = True
        exclude = ('id',)
        import_id_fields = ('sku',)


class ProductAdmin(ImportExportModelAdmin):
    resource_class = ProductResource


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


admin.site.register(Product, ProductAdmin)
admin.site.register(ProductItem, ProductItemAdmin)
