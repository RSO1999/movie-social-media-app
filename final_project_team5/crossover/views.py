

from django.http import Http404, HttpResponseBadRequest, HttpResponseServerError, JsonResponse
import requests
from final_project_team5.settings import TMDB_API_KEY
from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.urls import reverse
from django.core.mail import send_mail
from django.views.generic.edit import FormView
from django.db.models import Q
from .models import Movie, User, Favorites, Follow, MovieStaff
from .forms import Registration, EditPasswordForm, EditProfileForm
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
# added streaming sources import
from .movie_functions import add_movie, get_movie_details, get_content_rating, get_trailer, get_streaming_sources
from django.core.paginator import Paginator

# Updated homepage to integrate search functionality, displays all movies if no search is entered (will be changed eventually to have lazy loading/genre selection)


def movie_cards(request):

    # Collect any filters that were applied
    movie_query = request.GET.get("search", "")
    selected_genres = request.GET.getlist("genre", "")
    selected_ratings = request.GET.getlist("rating", "")
    selected_decades = request.GET.getlist("decade", "")

    genres = [
        "Action", "Adventure", "Animation", "Comedy", "Crime",
        "Documentary", "Drama", "Family", "Fantasy", "History",
        "Horror", "Music", "Mystery", "Romance", "Science Fiction",
        "TV Movie", "Thriller", "War", "Western"
    ]

    decades = ["1950s", "1960s", "1970s", "1980s",
               "1990s", "2000s", "2010s", "2020s"]

    ratings = ["G", "PG", "PG-13", "R"]

    # Building a query based on the filter choices
    movie_filters = Q()

    # Checking if a search was entered or filters were selected and building the query
    if movie_query:
        movie_filters &= Q(title__icontains=movie_query)

    if selected_genres:
        genre_filters = Q()
        for genre in selected_genres:
            genre_filters &= Q(genre__icontains=genre)
        movie_filters &= genre_filters

    if selected_ratings:
        movie_filters &= Q(rated__in=selected_ratings)

    if selected_decades:
        decade_filters = Q()
        for decade in selected_decades:
            start_year = int(decade[:-1])
            end_year = start_year + 9
            decade_filters |= Q(
                release_date__year__range=(start_year, end_year))
        movie_filters &= decade_filters

    # Filter the movies from our database based off the built query
    movies = Movie.objects.filter(movie_filters)

    # If no movies are found, or `tmdb_search` specified, make the TMDb search API call
    tmdb_results = []
    if not movies or "tmdb_search" in request.GET:
        response = requests.get(
            f"https://api.themoviedb.org/3/search/movie?query={movie_query}&include_adult=false&language=en-US&region=US&api_key={TMDB_API_KEY}"
        )
        if response.status_code == 200:
            tmdb_results = [
                result for result in response.json().get("results", [])
                if result["poster_path"] and result["release_date"] and int(result["release_date"][:4]) < 2024 and result["vote_count"] >= 500
            ]
            tmdb_results.sort(
                key=lambda result: (
                    result["popularity"],
                    result["vote_average"],
                    result["vote_count"]
                ),
                reverse=True
            )

    # Creating the paginator object for the filtered movies (20 movies per page)
    paginator = Paginator(movies, 20)
    page_number = request.GET.get("page")
    movie_page = paginator.get_page(page_number)

    query_params = request.GET.copy()
    if "page" in query_params:
        del query_params["page"]

    return render(request, "movies/movie_cards.html", {
        "movies": movie_page,
        "query": movie_query,
        "genres": genres,
        "decades": decades,
        "ratings": ratings,
        "selected_genres": selected_genres,
        "selected_decades": selected_decades,
        "selected_ratings": selected_ratings,
        "tmdb_results": tmdb_results,
        "query_params": query_params
    })

# Once a movie card is clicked, it will attempt to retrieve the details from our db. If it does not have the movie details yet, we call the "movie" endpoint of TMDB to get them


def movie_details(request, movie_id):
    movie = Movie.objects.filter(tmdb_id=movie_id).first()
    directors = MovieStaff.objects.all()

    if not movie:
        details = get_movie_details(movie_id)
        content_rating = get_content_rating(details.get("release_dates", []))
        trailer = get_trailer(details.get("videos", {}))

        movie, created = Movie.objects.update_or_create(
            tmdb_id=details["id"],
            defaults={
                "title": details["title"],
                "release_date": details["release_date"],
                "rated": content_rating,
                "runtime": details["runtime"],
                "genre": ", ".join([genre["name"] for genre in details.get("genres", [])]),
                "director": ", ".join([crew["name"] for crew in details.get("credits", {}).get("crew", []) if crew["job"] == "Director"]),
                "writer": ", ".join([crew["name"] for crew in details.get("credits", {}).get("crew", []) if crew["job"] == "Screenplay"]),
                "cast": ", ".join([cast["name"] for cast in details.get("credits", {}).get("cast", [])[:5]]),
                "plot": details["overview"],
                "poster": f"https://image.tmdb.org/t/p/w500{details['poster_path']}",
                "trailer": trailer
            }
        )
        # Makes sure all the new data is popualted before sending the movie to the details template
        movie.refresh_from_db()

    is_favorited = Favorites.objects.filter(user=request.user, movie=movie).exists(
    ) if request.user.is_authenticated else False
    
    # watchmode api call
    streaming_sources = get_streaming_sources(movie.tmdb_id)

    # If they select a director for a movie opinion
    if request.method == "POST":
        if "director" in request.POST:
            director = request.POST.get("director")
            movie_title = request.POST.get("movie")

            json_data = {
                "director": director,
                "movie": movie_title
            }
            # Call the flask API to get the generated opinion (address may need to be changed)
            response = requests.post(
                "http://api_worker:8000/directors-opinion", json=json_data)

            if response.status_code == 200:
                selected_director = MovieStaff.objects.filter(
                    name=director).first()
                opinion = response.json().get("opinion")
                return render(request, "movies/movie_details.html", {"movie": movie, "directors": directors, "is_favorited": is_favorited, "selected_director": selected_director, "opinion": opinion, "streaming_sources": streaming_sources})
            else:
                return HttpResponseServerError(f"Internal Server Error: when acquiring director's opinion")

        elif "trigger_movie" in request.POST:
            movie_title = movie.title

            json_data = {
                "movie":  movie_title
            }
            response = requests.post(
                "http://api_worker:8000/spoil-movie", json=json_data)
            # return the streaming sources
            if response.status_code == 200:
                triggers = response.json().get("spoiler")
                return render(request, "movies/movie_details.html", {
                    "movie": movie,
                    "is_favorited": is_favorited,
                    "trigger_description": triggers,
                    "directors": directors,
                    "streaming_sources": streaming_sources
                })
            else:
                return HttpResponseServerError(f"Internal Server Error: when acquiring trigger")
        else:
            return HttpResponseBadRequest("Bad Request: Invalid POST field.")

    return render(request, "movies/movie_details.html", {"movie": movie, "directors": directors, "is_favorited": is_favorited, "streaming_sources": streaming_sources})


def movie_login(request):
    next_page = request.GET.get('next', '')

    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        user = authenticate(request, email=email, password=password)

        if user is not None:
            login(request, user)

            return redirect("movie_cards")
        else:
            messages.error(request, "Invalid email or password.")

    return render(request, "login.html", {'next': next_page})


@login_required
def movie_picker(request, recipient_id):
    recipient = get_object_or_404(User, id=recipient_id)
    favorites = Favorites.objects.filter(user_id=recipient_id)
    favorite_movies = [favorite.movie for favorite in favorites]

    if request.method == 'POST':
        selected_movies = request.POST.getlist('selected_movies')
        json_data = {
            "movies": selected_movies,
        }

        # Call the flask API to get the generated opinion (address may need to be changed)
        response = requests.post(
            "http://api_worker:8000/suggest-movies", json=json_data)

        if response.status_code == 200:
            recommendations = response.json().get("movie_ids", [])
            movies = []

            for movie_id in recommendations:
                if movie_id != -1:
                    try:
                        movie = Movie.objects.get(tmdb_id=movie_id)
                        movies.append(movie)
                    except ObjectDoesNotExist:
                        movie = add_movie(movie_id)
                        movies.append(movie)
            # Store the recommended movies in the session
            request.session['recommended_movies'] = [
                movie.tmdb_id for movie in movies]
            return redirect('recommendation_display', recipient_id)
        else:
            return JsonResponse({'error': 'Failed to get recommendations'}, status=response.status_code)

    context = {
        'recipient': recipient,
        'favorite_movies': favorite_movies,
    }
    return render(request, "ai/movie_picker.html", context)


@login_required
def recommendation_display(request, recipient_id):
    recipient = get_object_or_404(User, id=recipient_id)
    if 'recommended_movies' not in request.session:
        return redirect('movie_cards')
    movie_ids = request.session['recommended_movies']
    movies = [Movie.objects.get(tmdb_id=movie_id) for movie_id in movie_ids]

    if request.method == 'POST':
        if 'send' in request.POST:
            recommendation_string = ''
            for movie in movies:
                title = movie.title
                link = f"http://localhost:8000/movie/{movie.tmdb_id}/"
                appendee = f"{title}\n{link}\n\n"
                recommendation_string += appendee
            send_mail(
                f'You Have Been Recommended Movies!',
                f'Hello, {recipient.username}!\nYour Friend, {request.user.username} has recommended you some movies!\n{recommendation_string}\nHappy Watching!',
                "{csc394.group5@gmail.com}",
                [recipient.email],
                fail_silently=False,
            )
            messages.success(request, 'Email sent successfully!')
            return redirect('movie_cards')

        elif 'cancel' in request.POST:
            return redirect('profile_view', recipient_id)

    context = {
        'recommended_movies': movies,
    }
    return render(request, "ai/recommendation_display.html", context)


def register(request):
    if request.method == "POST":
        form = Registration(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            email = form.cleaned_data.get('email')
            form.save()
            send_mail(
                # also considering shuttercut
                f'Welcome to CineVita, {username}!',
                'In Film, Find Heart\n\nHappy Watching!',
                "{csc394.group5@gmail.com}",
                [email],
                fail_silently=False,
            )
            messages.success(
                request, "Registration successful! Please log in.")
            return redirect("movie_login")
        else:
            messages.error(request, "Invalid registration details.")
            return render(request, "registration.html", {"error": "Invalid registration details.", "form": form})
    form = Registration()
    return render(request, "registration.html", {"form": form})


@login_required
def add_to_favorites(request, movie_id):
    movie = Movie.objects.filter(tmdb_id=movie_id).first()

    if not movie:
        details = get_movie_details(movie_id)
        if details:
            movie, created = Movie.objects.update_or_create(
                tmdb_id=details["id"],
                defaults={
                    "title": details["title"],
                    "release_date": details["release_date"],
                    "runtime": details["runtime"],
                    "genre": ", ".join([genre["name"] for genre in details.get("genres", [])]),
                    "plot": details["overview"],
                    "poster": f"https://image.tmdb.org/t/p/w500{details['poster_path']}",
                }
            )
        else:
            messages.error(request, "Could not find movie details.")
            return redirect("movie_cards")

    favorite, created = Favorites.objects.get_or_create(
        user=request.user, movie=movie)
    if created:
        messages.success(request, "Movie added to favorites.")
    else:
        messages.info(request, "Movie is already in your favorites.")
        return render(request, "movies/movie_details.html", {"movie": movie})

    return redirect("movie_details", movie_id=movie.tmdb_id)


@login_required
def remove_from_favorites(request, movie_id):
    movie = get_object_or_404(Movie, tmdb_id=movie_id)
    favorite = Favorites.objects.filter(user=request.user, movie=movie).first()

    if favorite:
        favorite.delete()
        messages.success(request, "Movie removed from favorites!")
    else:
        messages.error(request, "Movie not found in favorites.")

    referer = request.META.get('HTTP_REFERER', '')
    if 'favorites/' in referer:
        return redirect("profile")
    else:
        return redirect("movie_details", movie_id=movie.tmdb_id)


@login_required
def favorites_list(request):
    user_favorites = Favorites.objects.filter(
        user=request.user).select_related('movie')
    favorites = []
    for favorite in user_favorites:
        favorites.append(favorite)

    return render(request, "movies/profile.html", {"favorites": favorites})


@login_required
def search_users(request):
    # Get the search query and delete whitespace
    query = request.GET.get('q', '').strip()
    users = []

    if query:  # search if query is not empty
        users = User.objects.exclude(id=request.user.id).filter(
            Q(username__icontains=query) | Q(email__icontains=query)
        )

    return render(request, 'movies/user_search.html', {'users': users, 'query': query})


@login_required
def follow_user(request, user_id):
    user_to_follow = get_object_or_404(User, id=user_id)
    Follow.objects.get_or_create(
        follower=request.user, following=user_to_follow)
    messages.success(
        request, f"You are now following {user_to_follow.username}.")
    return redirect('search_users')


@login_required
def unfollow_user(request, user_id):
    user_to_unfollow = get_object_or_404(User, id=user_id)
    try:
        follow_relation = Follow.objects.get(
            follower=request.user, following=user_to_unfollow)
        follow_relation.delete()
        messages.success(
            request, f"You have unfollowed {user_to_unfollow.username}.")
    except Follow.DoesNotExist:
        messages.warning(
            request, f"You are not following {user_to_unfollow.username}.")

    return redirect('profile_view', user_id=request.user.id)


@login_required
def profile_view(request, user_id):
    user_profile = get_object_or_404(User, id=user_id)
    followers = user_profile.followers.all()
    following = user_profile.following.all()

    favorites = Favorites.objects.filter(user=user_profile)
    # Calculate counts
    followers_count = followers.count()
    following_count = following.count()

    is_own_profile = request.user.id == user_profile.id

    return render(request, 'movies/profile.html', {
        'user_profile': user_profile,
        'followers': followers,
        'following': following,
        'followers_count': followers_count,
        'following_count': following_count,
        'favorites': favorites,
        'is_own_profile': is_own_profile,
    })


@login_required
def follower_view(request, user_id):
    user_profile = get_object_or_404(User, id=user_id)
    followers = user_profile.followers.all()  # Get list of followers

    return render(request, 'movies/followers_view.html', {
        'user_profile': user_profile,
        'followers': followers,
    })


@login_required
def following_view(request, user_id):
    user_profile = get_object_or_404(User, id=user_id)
    following = user_profile.following.all()

    # Check if the profile belongs to the logged-in user
    is_own_profile = request.user.id == user_profile.id

    return render(request, 'movies/following_view.html', {
        'user_profile': user_profile,
        'following': following,
        'is_own_profile': is_own_profile,  # Pass the variable to the template
    })


def edit_profile(request):
    if request.method == "POST":
        form = EditProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('profile_view', user_id=request.user.id)
    return render(request, "edit_profile.html", {"form": EditProfileForm(instance=request.user)})


def edit_password(request):
    if request.method == "POST":
        form = EditPasswordForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request, "Password updated successfully. Please log in again.")
            return redirect("movie_login")
    return render(request, "edit_password.html", {"form": EditPasswordForm(user=request.user)})
