import os
import requests
from dotenv import load_dotenv

load_dotenv()
ACCESS_TOKEN = os.getenv("TMDB_TOKEN")

GENRES = {
    28: "Action",
    12: "Adventure",
    16: "Animation",
    35: "Comedy",
    80: "Crime",
    99: "Documentary",
    18: "Drama",
    10751: "Family",
    14: "Fantasy",
    36: "History",
    27: "Horror",
    10402: "Music",
    9648: "Mystery",
    10749: "Romance",
    878: "Sci-Fi",
    10770: "TV Movie",
    53: "Thriller",
    10752: "War",
    37: "Western",
}

def get_watchlist():
    try:
        with open("watchlist.txt", "r", encoding="utf-8") as file:
            movies = [line.strip() for line in file.readlines()]
        return {"status": "Success", "watchlist": movies}
    except FileNotFoundError:
        return {"status": "Error", "message": "Watchlist file not found."}

def add_to_watchlist(movie_title: str):
    with open("watchlist.txt", "a", encoding="utf-8") as file:
        file.write(f"{movie_title}\n")
        return {"status": "success", "message": f"Added '{movie_title}' to your watchlist."}

def clear_watchlist():
    with open("watchlist.txt", "w", encoding="utf-8") as file:
        pass
    return {"message": "Watchlist has been completely cleared."}

def tmdb_headers():
    return {
        "accept": "application/json",
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }

def get_trailer_url(movie_id):
    if not movie_id:
        return ""

    url = f"https://api.themoviedb.org/3/movie/{movie_id}/videos"
    try:
        response = requests.get(url, headers=tmdb_headers(), params={"language": "en-US"})
        response.raise_for_status()
        videos = response.json().get("results", [])
        trailer = next(
            (
                video for video in videos
                if video.get("site") == "YouTube" and video.get("type") == "Trailer"
            ),
            None,
        )
        if not trailer:
            trailer = next((video for video in videos if video.get("site") == "YouTube"), None)
        if trailer and trailer.get("key"):
            return f"https://www.youtube.com/watch?v={trailer['key']}"
    except requests.exceptions.RequestException:
        return ""

    return ""

def genre_names(genre_ids):
    return ", ".join(GENRES.get(genre_id, "") for genre_id in genre_ids if GENRES.get(genre_id))

def search_movie(title):
    url = "https://api.themoviedb.org/3/search/movie"
    headers = tmdb_headers()
    params = {"query": title, "language": "en-US"}

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        results = data.get("results", [])

        if results: 
            base_image_url = "http://image.tmdb.org/t/p/w500"           
            top_movie = results[0]
            top_overview = top_movie.get('overview', 'No description')
            
            if len(top_overview) > 450:
                top_overview = top_overview[:450] + "..."

            top_pick = {
                "title": top_movie.get('title', 'Unknown'),
                "overview": top_overview
            }

            movie_list = []
            for movie in results[:5]:
                full_overview = movie.get('overview', 'No description')
            
                if len(full_overview) > 450:
                    clean_overview = full_overview[:450] + "..."
                else:
                    clean_overview = full_overview

                movie_data = {
                    "tmdb_id": str(movie.get('id', '')),
                    "title": movie.get('title', 'Unknown'),
                    "year": movie.get('release_date', '0000')[:4],
                    "rating": round(movie.get('vote_average', 0), 1), 
                    "overview": clean_overview,
                    "poster": base_image_url + movie.get('poster_path') if movie.get('poster_path') else 'N/A',
                    "genres": genre_names(movie.get('genre_ids', [])),
                    "trailer_url": get_trailer_url(movie.get('id')),
                }
                movie_list.append(movie_data)

            return {
                "top_result": top_pick,
                "all_matches": movie_list
            }

        return {"message": "No movies found."}

    except requests.exceptions.RequestException as e:
        return {"error": "Connection failed", "details": str(e)}
