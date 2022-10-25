from django.urls import path
from .views import search, HomeView, ProductDetailView, ProductListView

urlpatterns = [
    path('', search, name='search'),
    path('test', HomeView.as_view(), name='index'),
    path('product/<str:pk>', ProductDetailView.as_view(), name="product_detail"),
    path('products', ProductListView.as_view(), name="product_list"),
]
