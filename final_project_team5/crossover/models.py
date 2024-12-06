
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import User


class Movie(models.Model):
    tmdb_id = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=255)
    release_date = models.DateField("Release Year", blank=True, null=True)
    rated = models.CharField(
        "Content Rating", max_length=10, blank=True, null=True)
    runtime = models.CharField(
        "Movie Length", max_length=10, blank=True, null=True)
    genre = models.TextField(blank=True, null=True)
    director = models.CharField(max_length=255, blank=True, null=True)
    writer = models.CharField(max_length=255, blank=True, null=True)
    cast = models.TextField("Movie Cast", blank=True, null=True)
    plot = models.TextField("Movie Story", blank=True, null=True)
    poster = models.URLField("Poster Image", blank=True, null=True)
    trailer = models.URLField("Movie Trailer", blank=True, null=True)


class User(AbstractUser):
    email = models.EmailField(unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email


class Favorites(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="favorites")
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    # added_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'movie')

    def __str__(self):
        return f"{self.user.username} - {self.movie.title}"


class Follow(models.Model):
    follower = models.ForeignKey(
        User, related_name='following', on_delete=models.CASCADE)
    following = models.ForeignKey(
        User, related_name='followers', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('follower', 'following')

    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"

class MovieStaff(models.Model):
    tmdb_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=255)
    known_for_department = models.CharField(max_length=255, blank=True, null=True)
    profile = models.URLField("Profile Picture", blank=True, null=True)
