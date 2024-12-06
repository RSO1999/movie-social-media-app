
from django.urls import path
from . import views
from .views import *
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("", views.movie_login, name="movie_login"),
    path("registration/", views.register, name="register"),
    path("home/", views.movie_cards, name="movie_cards"),
    path("search/", views.search_users, name="search_users"),
    path("follow/<int:user_id>/", views.follow_user, name="follow_user"),
    path('unfollow/<int:user_id>/', views.unfollow_user, name='unfollow_user'),
    path("profile/<int:user_id>/", views.profile_view, name="profile_view"),

    path("profile/<int:user_id>/followers/",
         views.follower_view, name="followers_view"),
    path("profile/<int:user_id>/following/",
         views.following_view, name="following_view"),

    path("change-password/", views.edit_password, name="change_password"),
    path("edit-profile/", views.edit_profile, name="edit_profile"),
    path("logout/", auth_views.LogoutView.as_view(next_page='movie_login'), name="logout"),
    path("movie/<int:movie_id>/", views.movie_details, name="movie_details"),
    path('favorites/add/<int:movie_id>/',
         views.add_to_favorites, name='add_to_favorites'),
    path('favorites/remove/<int:movie_id>/',
         views.remove_from_favorites, name='remove_from_favorites'),
    path('favorites/', views.favorites_list, name='favorites_list'),
    path('movie-picker/<int:recipient_id>/',
         movie_picker, name='movie_picker'),
    path('recommendations/<int:recipient_id>/',
         recommendation_display, name='recommendation_display'),
]
