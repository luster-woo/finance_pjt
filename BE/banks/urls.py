from django.urls import path
from . import views

urlpatterns = [
    path('', views.bank_list),
    path('nearby/', views.bank_nearby),
    path('route/', views.route_to_bank),
]
