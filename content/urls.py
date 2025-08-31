from . import views 
from django.urls import path

urlpatterns = [
    path("", views.home, name="home"),

    path("register/", views.register, name="register"),

    path('content/', views.content_list, name='content_list'), 
    path('create/', views.content_create, name='content_create'),
    path('edit/<int:pk>/', views.content_edit, name='content_edit'),
    path('content/<int:pk>/', views.content_detail, name='content_detail'),
    path('delete/<int:pk>/', views.content_delete, name='content_delete'),

    path('myupload/', views.my_upload, name='my_upload'),

    path('profile/<int:user_id>/', views.profile_view, name='profileview'),
    path('profileedit/', views.profile_edit, name='profileedit'),

    path('bookmark/<int:content_id>/', views.bookmark, name='toggle_bookmark'),
    path('mybookmark/', views.bookmarked_contents, name='my_bookmarks'),
    
    path('search/api/', views.search_api, name='search_api'),

    path('content/<int:content_id>/rate/', views.rate_content, name='rate_content'),
    path('content/<int:pk>/report/', views.report_content, name='report_content'),
    path('follow/<int:user_id>/', views.toggle_follow, name='toggle_follow'),
    path('profile/<int:user_id>/followers/', views.followers_list, name='followers_list'),
    path('profile/<int:user_id>/following/', views.following_list, name='following_list'),
    
    path('content/<int:content_id>/download/', views.increment_download, name='increment_download'),
]