from django.urls import path
from . import views
from .stats_views import similar_users_stats

urlpatterns = [
    path('', views.submit_test),
    path('result/', views.test_result),
    path('recommendations/products/', views.recommend_products),
    path('recommendations/stocks/', views.recommend_stocks),
    path('recommendations/cards/', views.recommend_cards),
    path('recommendations/by-criteria/', views.recommend_products_by_criteria),
    path('recommendations/cards/by-habits/', views.recommend_cards_by_habits),
    path('recommendations/stocks/page/', views.recommend_stocks_page),
    path('stats/similar-users/', similar_users_stats),
]
