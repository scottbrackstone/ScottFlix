import os
import requests
from dotenv import load_dotenv

load_dotenv()
ACCESS_TOKEN = os.getenv("TMDB_TOKEN")

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

def search_movie(title):
    url = "https://api.themoviedb.org/3/search/movie"
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }
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
            
            if len(top_overview) > 200:
                top_overview = top_overview[:200] + "..."

            top_pick = {
                "title": top_movie.get('title', 'Unknown'),
                "overview": top_overview
            }

            movie_list = []
            for movie in results[:5]:
                full_overview = movie.get('overview', 'No description')
            
                if len(full_overview) > 150:
                    clean_overview = full_overview[:150] + "..."
                else:
                    clean_overview = full_overview

                movie_data = {
                    "title": movie.get('title', 'Unknown'),
                    "year": movie.get('release_date', '0000')[:4],
                    "rating": round(movie.get('vote_average', 0), 1), 
                    "overview": clean_overview,
                    "poster": base_image_url + movie.get('poster_path') if movie.get('poster_path') else 'N/A'
                }
                movie_list.append(movie_data)

            return {
                "top_result": top_pick,
                "all_matches": movie_list
            }

        return {"message": "No movies found."}

    except requests.exceptions.RequestException as e:
        return {"error": "Connection failed", "details": str(e)}