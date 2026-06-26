from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.signup),
    path('profile/', views.profile),
    path('logout/', views.logout),
]
