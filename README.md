Functions:

gcloud functions deploy movie_recommender  --gen2  --region=us-east1  --runtime=python39  --source=.  --entry-point=http_movie_recommender  --trigger-http

curl -X POST https://movie-recommender-dv6vxphe3a-ue.a.run.app -H "Content-Type: application/json" -d '{"movies":["Inception","The Dark Knight","Shrek"]}'