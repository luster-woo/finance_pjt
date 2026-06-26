from django.urls import path
from . import views

urlpatterns = [
    path('', views.stock_list),
    path('<int:stock_id>/', views.stock_detail),
    path('<int:stock_id>/latest-price/', views.stock_latest_price),
    path('<int:stock_id>/prices/', views.stock_prices),
    path('<int:stock_id>/favorite/', views.stock_favorite_toggle),
    path('<int:stock_id>/news/', views.stock_news),
    path('import/issues/', views.import_stock_issues),
    path('import/prices/', views.import_stock_prices),
]
