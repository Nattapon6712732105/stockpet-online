from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.reports_home, name='home'),
    path('movements/csv/', views.export_movements_csv, name='movements_csv'),
]
