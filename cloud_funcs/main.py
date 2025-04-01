import functions_framework
import json
from flask import request, jsonify
from google.cloud import bigquery, aiplatform

def get_ai_recommendations(movies):
    pass
    # """Calls Vertex AI AutoML model for movie recommendations."""
    # PROJECT_ID = "your-project-id"
    # LOCATION = "us-central1"
    # MODEL_ID = "your-model-id"

    # # Create endpoint client
    # endpoint = aiplatform.Endpoint(
    #     endpoint_name=f"projects/{PROJECT_ID}/locations/{LOCATION}/endpoints/{MODEL_ID}"
    # )

    # # Format input
    # instances = [{"title": movie} for movie in movies]

    # # Call Vertex AI model
    # response = endpoint.predict(instances=instances)

    # # Extract predictions
    # predictions = response.predictions
    # recommended_movies = [pred["title"] for pred in predictions[:3]]

    # return recommended_movies
    
@functions_framework.http
def http_movie_recommender(request):
    try: 
        request_json = request.get_json()

        if not request_json or "movies" not in request_json:
            return jsonify({"error": "Missing 'movies' field in request"}), 400

        movies = request_json.get("movies", [])
        if not movies:
            return jsonify({"error": "No movies provided"}), 400

        query_client = bigquery.Client()

        placeholders = ", ".join([f"@movie_{i}" for i in range(len(movies))])
        query = f"""
            SELECT title, genres, vote_avg, vote_cnt
            FROM `hendrick-cis655-finalproject.bq_movies.tmdb_movie_list`
            WHERE title IN ({placeholders})
            ORDER BY vote_avg DESC
        """

        query_params = [
            bigquery.ScalarQueryParameter(f"movie_{i}", "STRING", movie)
            for i, movie in enumerate(movies)
        ]

        job_config = bigquery.QueryJobConfig(query_parameters=query_params)
        query_job = query_client.query(query, job_config=job_config)

        movies_found = [
            {"title": row["title"], "genre": row["genres"], "vote_avg": row["vote_avg"]}
            for row in query_job
        ]
        # return jsonify({"input_movies": movies, "recommendation_movies": movies_found})
        recommendations = movies_found
        # recommendations = get_ai_recommendations(movies_found)

        return jsonify({"input_movies": movies, "recommendation_movies": recommendations})
    except Exception as e:
        return jsonify({"error": str(e)}), 500