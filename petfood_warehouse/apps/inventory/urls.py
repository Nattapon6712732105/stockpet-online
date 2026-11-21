from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('', views.product_list, name='list'),
    path('receive/', views.receive_stock_view, name='receive_stock'),
    path('movements/', views.stock_movement_list, name='movements'),
    path('manage/', views.product_manage, name='manage'),
]
