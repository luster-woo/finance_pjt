from django.urls import path
from . import views

urlpatterns = [
    path('products/<int:review_id>/', views.review_update_delete),
    path('products/<int:review_id>/react/', views.review_react),
    path('cards/<int:review_id>/', views.card_review_update_delete),
]
