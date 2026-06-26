from django.urls import path
from . import views

urlpatterns = [
    path('', views.favorite_list),
    path('<int:product_id>/', views.favorite_toggle),
]