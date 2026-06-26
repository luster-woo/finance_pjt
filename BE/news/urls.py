from django.urls import path
from . import views

urlpatterns = [
    path('', views.news_list),
    path('import/', views.import_news),
    path('briefing/', views.weekly_briefing),
    path('briefing/generate/', views.generate_briefing),
    path('<int:news_id>/', views.news_detail),
]
