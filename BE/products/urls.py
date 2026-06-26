from django.urls import path
from . import views
from reviews import views as review_views

urlpatterns = [
    path('', views.product_list),
    path('save-products/', views.save_financial_products),
    path('save-saving-products/', views.save_saving_products),
    path('search/', views.product_search),
    path('compare/', views.product_compare),
    path('calculate/', views.product_calculate),
    path('<int:product_id>/status/', views.product_status),
    path('<int:product_id>/favorite/', views.favorite_toggle),
    path('<int:product_id>/subscribe/', views.subscribe_toggle),
    path('<int:product_id>/recent/', views.recent_product),
    path('<int:product_id>/reviews/', review_views.review_list_create),
    path('<int:product_id>/', views.product_detail),
]
