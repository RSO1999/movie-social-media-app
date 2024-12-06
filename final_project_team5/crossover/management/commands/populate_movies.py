from django.core.management.base import BaseCommand
from crossover.models import Movie, MovieStaff
from crossover.movie_functions import get_top_rated_movies, get_popular_movies, get_movie_details, get_content_rating, get_trailer, get_person
import time

class Command(BaseCommand):
    def handle(self, *args, **options):
        # Change this to get more movies
        for i in range(1, 20):
            top_rated = get_top_rated_movies(i)
            popular = get_popular_movies(i)
            movies = top_rated + popular

            for movie in movies:
                # For the sake of the AI recommendations, we aren't getting movies released in 2024 or later
                if int(movie["release_date"][:4]) >= 2024:
                    continue

                # Get movie details using the get_movie_details function
                details = get_movie_details(movie["id"])

                release_dates = details.get("release_dates", [])
                content_rating = get_content_rating(release_dates) if release_dates else None

                trailer = get_trailer(details.get("videos", {}))

                # Filtering out unrated and movies that do not have trailers
                if not content_rating or content_rating == "NR" or not trailer:
                    continue

                genres = [genre["name"] for genre in details.get("genres", [])]
                directors = [crew["name"] for crew in details.get("credits", {}).get("crew", []) if crew["job"] == "Director"]
                writers = [crew["name"] for crew in details.get("credits", {}).get("crew", []) if crew["job"] == "Screenplay"]
                cast = [cast["name"] for cast in details.get("credits", {}).get("cast", [])[:5]]

                # Update or create the movie record in the database
                Movie.objects.update_or_create(
                    tmdb_id=details.get("id"),
                    defaults={
                        "title": details.get("title", "N/A"),
                        "release_date": details.get("release_date", "N/A"),
                        "rated": content_rating,
                        "runtime": details.get("runtime", 0),
                        "genre": ", ".join(genres),
                        "director": ", ".join(directors),
                        "writer": ", ".join(writers),
                        "cast": ", ".join(cast),
                        "plot": details.get("overview", "No plot available."),
                        "poster": f"https://image.tmdb.org/t/p/w500{details.get('poster_path', '')}",
                        "trailer": trailer
                    }
                )

        # Curated list of directors for the opinions feature
        directors = [
            "Alfred Hitchcock", "Quentin Tarantino", "Jordan Peele", 
            "Martin Scorsese", "Bong Joon-ho", "Sofia Coppola", "Ridley Scott", 
            "Stanley Kubrick", "Jean-Luc Godard", "Kevin Feige", "Céline Sciamma", 
            "Agnès Varda", "Wes Anderson"
        ]

        for director in directors:
            data = get_person(director)
            if data:
                MovieStaff.objects.update_or_create(
                    tmdb_id=data.get("id"),
                    defaults={
                        "name": data.get("name", "Unknown"),
                        "known_for_department": data.get("known_for_department", "Unknown"),
                        "profile": f"https://image.tmdb.org/t/p/w500{data.get('profile_path', '')}"
                    }
                )

        self.stdout.write(self.style.SUCCESS('Successfully populated movies and directors'))
