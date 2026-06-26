from django.urls import path
from . import views

urlpatterns = [
    path('', views.card_list),
    path('import/', views.import_cards),
    path('<int:card_id>/', views.card_detail),
    path('<int:card_id>/benefits/', views.card_benefits),
    path('<int:card_id>/reviews/', views.card_review_list_create),
]
