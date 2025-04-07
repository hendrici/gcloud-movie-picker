import functions_framework
import json
from flask import request, jsonify
from google.cloud import bigquery
from rapidfuzz import process, fuzz
import google.auth
import google.auth.transport.requests
import requests

query_client = bigquery.Client()
query = "SELECT title, movieId FROM `hendrick-cis655-finalproject.bq_movies.movies`"

movie_list = [(row["title"], row["movieId"]) for row in query_client.query(query)]
movie_titles_list = [title for title, _ in movie_list]

def get_movie_id(user_input):
    best_match = process.extractOne(user_input, movie_titles_list, scorer=fuzz.token_set_ratio)
    if best_match:
        matched_title = best_match[0]
        movie_id = next(mId for title, mId in movie_list if title == matched_title)
        return movie_id

    return None


def get_movie_title(movie_id):
    movie_title = next(title for title, mId in movie_list if mId == movie_id)
    return movie_title


def send_request_to_ai_model(movie_ids):
    credentials, _ = google.auth.default()
    auth_req = google.auth.transport.requests.Request()
    credentials.refresh(auth_req)
    access_token = credentials.token

    model_url = "https://retail.googleapis.com/v2/projects/hendrick-cis655-finalproject/locations/global/catalogs/default_catalog/servingConfigs/movie-recommender-config:predict"

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
    movie_ids = [get_movie_id(title) for title in user_movies if get_movie_id(title)]
    response = send_request_to_ai_model(movie_ids)

    recommended_movies = [get_movie_title(int(movie["id"])) for movie in response["results"][:3]]
    return recommended_movies


@functions_framework.http
def http_movie_recommender(request):
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