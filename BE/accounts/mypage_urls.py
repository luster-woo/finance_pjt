from django.urls import path
from . import views

urlpatterns = [
    path('', views.mypage),
    path('password/', views.change_password),
    path('products/favorites/', views.mypage_product_favorites),
    path('products/subscriptions/', views.mypage_product_subscriptions),
    path('products/recent/', views.mypage_product_recent),
    path('stocks/favorites/', views.mypage_stock_favorites),
    path('reviews/', views.mypage_reviews),
    path('community/', views.mypage_community),
    path('test-result/', views.mypage_test_result),
]
