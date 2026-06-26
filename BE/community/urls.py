from django.urls import path
from . import views

urlpatterns = [
    path('posts/', views.post_list_create),
    path('posts/<int:post_id>/', views.post_detail),
    path('posts/<int:post_id>/like/', views.post_like_toggle),
    path('posts/<int:post_id>/comments/', views.comment_list_create),
    path('comments/<int:comment_id>/', views.comment_update_delete),
    path('comments/<int:comment_id>/like/', views.comment_like_toggle),
]
