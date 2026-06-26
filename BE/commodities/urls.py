from django.urls import path
from . import views

urlpatterns = [
    path('import/', views.import_commodities),
    path('summary/', views.commodity_summary),
    path('', views.commodity_list),
]
