from . import views 
from django.urls import path

urlpatterns = [
    path("", views.home, name="home"),
    path("register/", views.register, name="register"),
    path('', views.content_list, name='content_list'),
    path('create/', views.content_create, name='content_create'),
    path('<int:pk>/', views.content_detail, name='content_detail'),
]