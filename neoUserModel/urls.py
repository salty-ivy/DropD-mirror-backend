from django.urls import path
from .views import *

app_name = 'neoUserModel'

urlpatterns = [

    path('create-post/',CreatePost,name='create-post'),
	path('view-post/<str:pid>/',viewPost,name='get-post'),
	path('update-post/',updatePost,name="update-post"),
	path('user-posts/',getUserPosts,name='get-user-posts'),
	path('like-post/',likePost,name='like-post'),
	path('comment-post/',commentOnPost,name='comment-post'),

]