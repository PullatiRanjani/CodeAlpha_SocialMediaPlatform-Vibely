from django.urls import path
from . import views
urlpatterns=[
 path('',views.home,name='home'), path('login/',views.login_view,name='login'), path('register/',views.register_view,name='register'), path('logout/',views.logout_view,name='logout'),
 path('create-post/',views.create_post,name='create_post'), path('post/<int:post_id>/',views.post_detail,name='post_detail'), path('post/<int:post_id>/like/',views.toggle_like,name='toggle_like'), path('post/<int:post_id>/comment/',views.add_comment,name='add_comment'), path('post/<int:post_id>/delete/',views.delete_post,name='delete_post'),
 path('search/',views.search,name='search'), path('u/<str:username>/',views.profile,name='profile'), path('u/<str:username>/follow/',views.toggle_follow,name='toggle_follow'),
 path('notifications/',views.notifications,name='notifications'), path('settings/',views.settings_view,name='settings'),
 path('story/create/',views.create_story,name='create_story'), path('stories/<str:username>/',views.story_viewer,name='story_viewer'), path('story/<int:story_id>/like/',views.story_like,name='story_like'), path('story/<int:story_id>/reply/',views.story_reply,name='story_reply'), path('story/<int:story_id>/delete/',views.delete_story,name='delete_story'), path('story/<int:story_id>/insights/',views.story_insights,name='story_insights'),
]
