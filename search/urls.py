from django.urls import path
from .views import HomeView, ProductDetailView, ProductListView

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('product/<str:pk>', ProductDetailView.as_view(), name="product_detail"),
    path('products', ProductListView.as_view(), name="product_list"),
]
