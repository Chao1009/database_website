from django.urls import path
from .views import index, ProductDetailView, ProductListView

urlpatterns = [
    path('', index, name='index'),
    path('product/<str:pk>', ProductDetailView.as_view(), name="product_detail"),
    path('products', ProductListView.as_view(), name="product_list"),
]
