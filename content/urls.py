from . import views 
from django.urls import path

urlpatterns = [
    path("", views.home, name="home"),
    path("register/", views.register, name="register"),
    path('', views.content_list, name='content_list'),
    path('create/', views.content_create, name='content_create'),
    path('<int:pk>/', views.content_detail, name='content_detail'),
    path('myupload/',views.my_upload, name='my_upload'),
    path('profileview/',views.profile_view, name='profileview'),
    path('profileedit/',views.profile_edit, name='profileedit'),
    path('bookmark/<int:content_id>/', views.bookmark, name='toggle_bookmark'),
    path('mybookmark/', views.bookmarked_contents, name='my_bookmarks'),
    
]