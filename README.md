<!-- HEADER -->
# gcloud-movie-picker
Need help finding a movie to watch?
<div align="left">
  <p>
    <a href="https://hendrick-cis655-finalproject.ue.r.appspot.com/">
      <img src="https://img.shields.io/badge/Click_here_to_use_application!-blue?style=for-the-badge&">
    </a>
    <a href="https://www.youtube.com/">
      <img src="https://img.shields.io/badge/Presentation-red?style=for-the-badge&logo=youtube">
    </a>
  </p>
</div>

> **NOTE:** If the application website is not working, it is most likely because I took it down for the time being. The App Engine instance costs about $1.50/day to run.

<!-- TABLE OF CONTENTS -->
### Table of Contents
<ol>
  <li>
    <a href="#about-the-project">About The Project</a>
  </li>
  <li>
    <a href="#instructions">Instructions</a>
    <ul>
      <li><a href="#cloud-storage">Cloud Storage</a></li>
      <li><a href="#big-query">Big Query</a></li>
      <li><a href="#vertex-ai-search-for-commerce">Vertex AI (Search for Commerce)</a></li>
      <li><a href="#cloud-run">Cloud Run</a></li>
      <li><a href="#app-engine">App Engine</a></li>
    </ul>
  </li>
  <li><a href="#usage">Usage</a></li>
</ol>



<!-- ABOUT THE PROJECT -->
## About The Project

I have always loved watching movies, but most of the time, I seem to have trouble deciding which film to watch, or sometimes simply finding a film that peaks my interest. This tool implements a machine learning model, trained with user ratings using Vertex AI, to generate recommended movies based on those provided by a user. This project served as a way for me to gain hands-on experience with Google Cloud and its services, a skill that could be helpful with various projects in the future.



<!-- INSTRUCTIONS -->
## Instructions

This project implements Google Cloud services, specifically Cloud Storage, Big Query, Vertex AI (Search for Commerce), Cloud Run, and App Engine. For anybody that would like to replicate this project or something similar, this is a brief description of how each service was implemented.

This also means that a Google Cloud account is required, since all instructions are meant for use within the Cloud Console (using these services may incur charges to your account, especially when training the AI model).

### Cloud Storage

The data needed for training the Vertex AI model was stored within Cloud Storage, which was done with the following commands (make sure you are in the same directory as the .csv files when executing):

```
gcloud storage buckets create gs://{PROJECT_ID}-recommended-movies-bucket
```
```
gcloud storage cp movies.csv ratings.csv gs://{PROJECT_ID}-recommended-movies-bucket
```

The datasets were initially downloaded from [Kaggle - MovieLens 20M Dataset](https://www.kaggle.com/datasets/grouplens/movielens-20m-dataset), and uploaded to the Cloud Console.

> **NOTE:** The web application also makes a call directly to Cloud Storage, allowing the user to download the movie dataset. In order for this call to work properly, the bucket permissions must be updated. In the permissions tab of the recommended-movies-bucket details within Cloud Console, grant the "Storage Object Viewer" role to the principal "allUsers". If creating your own bucket, you will also need to change the URL within the "downloadDataset()" function in [index.html](web-app/public/index.html).

### Big Query

Big Query was used for preparing the movie and ratings data when training the Vertex AI model, as well as generating a complete list of movies within the Cloud Run function. This was done to match input from the user, which is prone to typos and skewed format, to the actual movie titles stored in the dataset.

Create a Big Query dataset with the command:

```
bq mk bq_movies
```

To load the movies and ratings data into the Big Query datasets, use the following commands:

```
bq load --skip_leading_rows=1 bq_movies.movies gs://{PROJECT_ID}-recommended-movies-dataset/movies.csv movieId:integer,title:string,genres:string
```

```
bq load --skip_leading_rows=1 bq_movies.ratings gs://{PROJECT_ID}-recommended-movies-dataset/ratings.csv userId:integer,movieId:integer,rating:float,time:timestamp
``` 

### Vertex AI (Search for Commerce)

This [guide](https://cloud.google.com/retail/docs/movie-rec-tutorial) from Google was used to assist in the creation and training of the Vertex AI model. The created model is specifically designed for use in commerce, recommending "products" (movies in this case) to users based on previous "user_events" (movie ratings in this case). In order to upload data and train the model, the "Vertex AI Search for Commerce" API must be enabled through Cloud Console.

The guide includes two queries to re-format the movie and ratings data into new tables, as "products" and "user_events", respectively. Both of these tables must then be imported from Big Query into the "Search for Commerce" data page of the Cloud Console in order to train the model. After both imports have completed (this may take a couple of hours), a model can be created and trained with the options "Others you may like" and "Click-through rate (CTR)".

> **Note:** The model takes approximately two days to train using the given ratings dataset. Luckily I was responsible and started this project early instead of procrastinating it until the last second, so this was not an issue :) 

### Cloud Run

A Cloud Run function was developed using Python to invoke the Vertex AI model and generate predicted movies using input from the user. The model identifies movies by ID, not title, so the program searches the database for the closest title match given the user input using Big Query and invokes the model with the associated ID. The Google Cloud Big Query API library must be imported in order for this function to work. The "PROJECT_ID" variable in [main.py](cloud_funcs/main.py) must also be updated to the correct string (the current string is custom to my implementation).

I attempted to invoke the AI model using the Google Cloud Retail API, however, I unfortunately was not able to get it working properly (this would be an excellent feature to implement in the future). Instead, I was forced to call the model via an HTTP request, which created a new issue pertaining to authentication (meaning I was required to setup a dedicated service account and add access tokens within code). 

> **IMPORTANT:** In order for this method to work, a service account (separate from the application default) needs to be created (I followed the format "*retail@{PROJECT_ID}.iam.gserviceaccount.com*") with ATLEAST the following roles: *BigQuery Data Viewer, BigQuery Job User, Cloud Run Invoker, Retail Viewer, Service Account Token Creator*.

To deploy this function to Cloud Run, use the command:

```
gcloud functions deploy movie_recommender --gen2 --region=us-east1 --runtime=python39 --source=. --entry-point=http_movie_recommender --trigger-http --service-account=retail@{PROJECT_ID}.iam.gserviceaccount.com
```

Use a cURL command to ensure the function is working properly, the response should include the recommended movies in JSON format (make sure to replace {GENERATED_CLOUD_RUN_URL} with the URL generated by the deploy command). Feel free to edit the input movies to see different reponses. 

```
curl -X POST {GENERATED_CLOUD_RUN_URL} -H "Content-Type: application/json" -d '{"movies":["Beauty and the Beast","Cinderella","The Little Mermaid"]}'
```

### App Engine

App Engine was used for hosting the web application. NodeJS, HTML, and CSS were used to develop the application; make sure you install npm before trying to run the application locally:

```
npm install
```

Make sure that the CLOUD_RUN_URL constant is correctly defined within [app.js](web-app/app.js). For testing purposes, the web server can be ran locally to view the effect of any changes quickly using this command (make sure to run within the web-app subdirectory):

```
npm start
```

For deploying the application to App Engine, use the command (make sure to run within the web-app subdirectory):

```
gcloud app deploy
```

The application should now be ready to use! Access using the URL generated from the previous command.



<!-- USAGE EXAMPLE -->
## Usage

The application itself should be self explanatory. The user has the option to input up to five of their movies, and clicking "Submit" will generate their top three recommended movies based on a Vertex AI model. It is important to note that that dataset being used is older and will only recognize movies released in 2015 or earlier.

The user also has the option of downloading the movie dataset (in the form of a .txt file) by clicking "Download Dataset." This dataset includes the list of movies and the genres associated with each.

![Usage](screenshots/usage.png)