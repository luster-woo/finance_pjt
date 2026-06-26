from django.contrib import admin
from django.urls import path, include

# 1. 미디어 파일 서빙을 위해 새로 추가할 import
from django.conf import settings
from django.conf.urls.static import static

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('admin/', admin.site.urls),

    path('accounts/', include('accounts.urls')),
    path('accounts/login/', TokenObtainPairView.as_view()),
    path('accounts/refresh/', TokenRefreshView.as_view()),
    path('mypage/', include('accounts.mypage_urls')),

    path('products/', include('products.urls')),
    path('stocks/', include('stocks.urls')),
    path('cards/', include('cards.urls')),
    path('community/', include('community.urls')),
    path('banks/', include('banks.urls')),
    path('news/', include('news.urls')),
    path('commodities/', include('commodities.urls')),

    path('reviews/', include('reviews.urls')),
    path('favorites/', include('favorites.urls')),
    path('tests/', include('financial_tests.urls')),
    path('planner/', include('planner.urls')),
    path('chat/', include('chat.urls')),
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 