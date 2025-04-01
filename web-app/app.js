const express = require("express");
const path = require("path");
const app = express();
const CLOUD_RUN_URL = 'https://movie-recommender-dv6vxphe3a-ue.a.run.app';

app.use(express.static(path.join(__dirname, "public")));
app.use(express.json());

app.post("/process", async(req, res) => {
    const movies = req.body.movies || [];

    if (movies.length === 0) {
        return res.status(400).json({ error: "No movies provided." });
    }

    try {
        // Send request to Cloud Run function
        const response = await fetch(CLOUD_RUN_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ movies: movies }),
        });

        if (!response.ok) {
            throw new Error(`Cloud Run request failed with status ${response.status}`);
        }

        const data = await response.json();
        res.json(data); // Forward response to frontend
    } catch (error) {
        console.error("Error fetching recommendations:", error);
        res.status(500).json({ error: "Failed to fetch recommendations." });
    }
});

const PORT = process.env.PORT || 8080;
app.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`);
});
