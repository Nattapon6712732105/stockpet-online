from django.urls import path
from . import views

app_name = 'requisitions'

urlpatterns = [
    path('', views.request_list, name='list'),
    path('new/', views.create_request, name='create'),
    path('<int:pk>/', views.request_detail, name='detail'),
    path('<int:pk>/approve/', views.approve_view, name='approve'),
    path('<int:pk>/reject/', views.reject_view, name='reject'),
    path('<int:pk>/cancel/', views.cancel_view, name='cancel'),
]
