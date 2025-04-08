import functions_framework
import json
from flask import request, jsonify
from google.cloud import bigquery
from rapidfuzz import process, fuzz
import google.auth
import google.auth.transport.requests
import requests

PROJECT_ID = "hendrick-cis655-finalproject"

query_client = bigquery.Client()
query = f"SELECT title, movieId FROM `{PROJECT_ID}.bq_movies.movies`"

movie_list = [(row["title"], row["movieId"]) for row in query_client.query(query)]
movie_titles_list = [title for title, _ in movie_list]

def get_movie_id(user_input):
    """
        Convert a given movie title from user input to the best title match within the dataset, then 
        return the associated movie ID.

        Args:
            user_input: Movie title from user input.

        Returns:
            Movie ID of closest movie title match with user input.
    """
    best_match = process.extractOne(user_input, movie_titles_list, scorer=fuzz.token_set_ratio)
    if best_match:
        matched_title = best_match[0]
        movie_id = next(mId for title, mId in movie_list if title == matched_title)
        return movie_id

    return None


def get_movie_title(movie_id):
    """
        Convert a given movie ID to its associated movie title using the movie list (generated from BigQuery query). 

        Args:
            movie_id: ID of movie within dataset.

        Returns:
            Movie title associated with the provided movie ID.
    """
    movie_title = next(title for title, mId in movie_list if mId == movie_id)
    return movie_title


def send_request_to_ai_model(movie_ids):
    """
        Generate authenticated access token and invoke AI model with HTTP request, sending list of user inputted movies.

        Args:
            movie_ids: List of user input movie IDs.

        Returns:
            Json response of recommended movies from AI model.
    """
    credentials, _ = google.auth.default()
    auth_req = google.auth.transport.requests.Request()
    credentials.refresh(auth_req)
    access_token = credentials.token

    model_url = f"https://retail.googleapis.com/v2/projects/{PROJECT_ID}/locations/global/catalogs/default_catalog/servingConfigs/movie-recommender-config:predict"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    user_event = {
        "userEvent": {
            "eventType": "detail-page-view",
            "visitorId": "visitor-123",
            "productDetails": [{"product": {"id": str(movie_id)}} for movie_id in movie_ids]
        },
        "pageSize": 3
    }

    response = requests.post(model_url, headers=headers, json=user_event)
    if response.status_code != 200:
        return {"error": response.text}, response.status_code

    return response.json()


def get_recommendations(user_movies):
    """
        Get closest title matches from user input and convert to movie IDs, send request to AI model,
        convert resulting recommended movie IDs to movie titles.
     
        Args:
            user_movies: List of movies title input from the user. 

        Returns:
            The recommended movie titles from the Vertex AI model.
    """
    movie_ids = [get_movie_id(title) for title in user_movies if get_movie_id(title)]
    response = send_request_to_ai_model(movie_ids)

    recommended_movies = [get_movie_title(int(movie["id"])) for movie in response["results"][:3]]
    return recommended_movies


@functions_framework.http
def http_movie_recommender(request):
    """
        This is the enter point for the Cloud Run function, the input movies from the user 
        are received and processed before being sent to the Vertex AI. After the response from
        the model, the resulting recommended movies are processed and then returned.

        Args:
            request: List of user input movies in json format.

        Returns:
            Returns recommended movies in json format.
    """
    try: 
        request_json = request.get_json()

        if not request_json or "movies" not in request_json:
            return jsonify({"error": "Missing 'movies' field in request"}), 400

        movies = request_json.get("movies", [])
        if not movies:
            return jsonify({"error": "No movies provided"}), 400

        return jsonify({"recommendation_movies": get_recommendations(movies)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500