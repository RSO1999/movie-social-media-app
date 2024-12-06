import os
from flask import Flask, request, jsonify
from openai import OpenAI
from datetime import datetime
import requests

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
TMBD_API_KEY = os.environ.get("TMDB_API_KEY")


app = Flask(__name__)

#ROUTES

@app.route('/health', methods=['GET'])
def health_check():
    if client:
        return jsonify(status="healthy"), 200
    else:
        return jsonify(status="inestablished"), 500
    
    
@app.route('/spoil-movie', methods=['POST'])
def spoil_movie():
    try:
        data = request.json
        movie_title = data.get('movie')
        spoiler = spoil(movie_title)
        return jsonify({"spoiler": spoiler})
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "Internal Server error in spoiling a movie"}), 500

@app.route('/suggest-movies', methods=['POST'])
def suggest_movies():
    try:
        data = request.json
        movies = data.get('movies', [])
        recommendations = movie_suggestion(movies)
        return jsonify({"movie_ids": recommendations})
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "Internal Server error in generating list"}), 500
        

@app.route('/directors-opinion', methods=['POST'])
def directors_opinion():
    try:
        data = request.json
        movie_director = data.get('director')
        movie_name = data.get('movie')
        
        if movie_name == None or movie_director == None:
            return jsonify({"error": "Incomplete Request"}), 400
        
        opinion = get_directors_opinion(movie_director, movie_name)
        return jsonify({"opinion": opinion}), 200
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "Internal Server Error in obtaining director's opinions"}), 500

#FUNCTIONS

def spoil(movie_title):
    recommendation_prompt = (
        f"I am planning on watching the movie \'{movie_title}\' \nHowever, I am skeptical of the material in the movie, and want to ensure there are no potentially triggering/offensive scenes or sequences in the movie that my audience is not prepared for.\nBased upon the intended audience of \'{movie_title}\', generate a rating on the following categories\nGore or Body Horror\nRacism or Racist Stereotypes\nProfanity\nSexism or Gender Stereotypes\nHomophobia\nReligious Intolerance/Blashpemy\nExcessive, Violent, or Gratuitous Sexual Content\nSuicide or Self Harm\nAnimal Cruelty\nDrug Usage\nAbleism\nPlease rate each category on a scale of 1-10, with 1 being no presence, and 10 being strongly present within the movie. Also, if the movie is based on a book, please ensure the descriptions pertain to just the movie, and not the book, in case there are differences.\nPlease return your response formatted like the example provided here:\nGore/Body Horror (4/10): <your description>\nWhere <your description> is replaced with a short 1-3 sentence description describing what happens in the movie related to that category. Do not be vague in your descriptions, make sure to reference the specific scene/sequence the depiction occurs in and any characters involved to ensure clarity. Do not number the categories, do not use bullet points, just separate them by a new line. Do not include any other text in your response outside of the ratings/descriptions, in other words, no boiler plate text."
    )
    return get_openai_response(recommendation_prompt)

def movie_suggestion(movies):
    recommendation_prompt = (
        f"My Friend likes these movies: {', '.join(movies)}, please recommend a list of 5 similar movies, based on my friend's taste, formatted as a comma-separated list of titles, nothing else. Do not include the movie's release year with your responses, unless it is an actual part of the movie title"
    )
    
    recommendations = get_openai_response(recommendation_prompt)
    movies_list = [movie.strip() for movie in recommendations.split(',')]
    print(movies_list)
    return list(map(search_movie_by_title, movies_list))
    
def get_directors_opinion(movie_director, movie_name):
    recommendation_prompt = (
        f"Based on {movie_director}'s thoughts on the movie '{movie_name}', do an impression of {movie_director}, and give your opinion on the film in character, as if they seen the film today. Make sure to convey the director's opinion strongly, even if their passion needs to be exaggerated a bit, but make it a bit humorous, whether it be positive or negative. Just answer with the impression, nothing else. No boiler plate text, no quotation marks or indentations"
        )
    return get_openai_response(recommendation_prompt)


def search_movie_by_title(title):
    url = f"https://api.themoviedb.org/3/search/movie"
    params = {
        'api_key': TMBD_API_KEY,
        'query': title
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        results = response.json().get('results', [])
        print(f"result:{results}")
        if len(results) <= 0:
            movie_id = -1
        else:
            movie_id = results[0]['id']
        return movie_id
    else:
        raise Exception("Invalid Response from TMDB")


def log_request(prompt, response_content):
    with open("requests.log", "a") as log_file:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{timestamp} | PROMPT: {prompt} | RESPONSE: {repr(response_content)}\n"
        log_file.write(log_entry)

def get_openai_response(prompt):
    
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="gpt-3.5-turbo",
    )
    log_request(prompt, chat_completion)
    return chat_completion.choices[0].message.content

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
