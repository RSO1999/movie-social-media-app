
import requests
from django.conf import settings
from .models import Movie

TMDB_API_KEY = settings.TMDB_API_KEY
tmdb_url = "https://api.themoviedb.org/3/"


WATCHMODE_API_KEY = settings.WATCHMODE_API_KEY

# Function to get streaming sources from Watchmode


def get_streaming_sources(tmdb_id):
    try:
        response = requests.get(
            f'https://api.watchmode.com/v1/title/movie-{tmdb_id}/sources/?apiKey={WATCHMODE_API_KEY}',
            params={
                "regions": "US"
            }
        )
        if response.status_code == 200:
            return response.json()
        else:
            return []
    except Exception as e:
        print(f"Error fetching streaming sources: {e}")
        return []

# Calls the TMDB TopRated endpoint and gets the given page number (about 20 movies per page)


def get_top_rated_movies(page):
    response = requests.get(
        f"{tmdb_url}movie/top_rated?language=en-US&page={page}&region=US&api_key={TMDB_API_KEY}")
    if response.status_code == 200:
        return response.json().get("results", [])
    else:
        return

# Calls the TMDV Discover endpoint to get popular movies in the US from 1980 to 2020


def get_popular_movies(page):
    response = requests.get(
        f"{tmdb_url}discover/movie?include_adult=false&include_video=false&language=en-US&page={page}&region=US&release_date.gte=1980-01-01&release_date.lte=2020-01-01&sort_by=popularity.desc&watch_region=US&api_key={TMDB_API_KEY}")
    if response.status_code == 200:
        return response.json().get("results", [])
    else:
        return

# Calls the movie details endpoint and appends release_dates, credits, and videos to collect all the movie data we need


def get_movie_details(tmdb_id):
    response = requests.get(
        f"{tmdb_url}movie/{tmdb_id}?append_to_response=release_dates%2Ccredits%2Cvideos&language=en-US&api_key={TMDB_API_KEY}")
    if response.status_code == 200:
        return response.json()
    else:
        return

# Extracts the content rating (R, PG-13, etc.) from the release_dates JSON data


def get_content_rating(release_dates):
    for country_release in release_dates.get("results", []):
        if country_release["iso_3166_1"] == "US":
            for release in country_release.get("release_dates", []):
                if release.get("certification") != "":
                    return release.get("certification")

# Gets the movie trailer (makes sure its official, on Youtube and localized to the US)


def get_trailer(videos):
    for video in videos.get("results", []):
        if all([video["iso_3166_1"] == "US", video["site"] == "YouTube", video["type"] == "Trailer", video["official"] == True]):
            return video["key"]

# Call the tmdb person search to get movie staff member data


def get_person(name):
    url = f"{tmdb_url}search/person"
    params = {
        "query": name,
        "api_key": TMDB_API_KEY,
        "include_adult": "false",
        "language": "en-US"
    }
    response = requests.get(url=url, params=params)
    if response.status_code == 200:
        return response.json().get("results", [])[0]


def add_movie(tmdb_id):
    details = get_movie_details(tmdb_id)
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
    return movie
