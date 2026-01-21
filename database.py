import os
from pymongo import MongoClient
from dotenv import load_dotenv

# 1. Load the secrets from the .env file
load_dotenv()

# 2. Pull the URI from the "environment"
# If the .env is set up correctly, this replaces the long messy string
uri = os.getenv("MONGO_URI") 

client = MongoClient(uri)
db = client.ScottFlix_DB
watchlist_col = db.watchlist
favs_col = db.favourites


def init_db():
    """MongoDB creates everything automatically on the first insert, 
    so we just print a success message here."""
    print("✅ Cloud Database Connected!")

def db_add_movie(title, year, poster):
    movie_doc = {"title": title, "year": year, "poster": poster}
    watchlist_col.insert_one(movie_doc)
    print(f"✅ Added {title} to Cloud Watchlist")

def db_get_watchlist():
    # .find() gets everything. We convert it to a list for the HTML.
    # we exclude the '_id' because it's a special Mongo object that HTML doesn't like
    movies = list(watchlist_col.find({}, {"_id": 0}))
    return movies

def db_get_favourites():
    return list(favs_col.find({}, {"_id": 0}))

def db_add_favourite(title, year, notes):
    fav_doc = {"title": title, "year": year, "notes": notes}
    favs_col.insert_one(fav_doc)
    print(f"✅ Added {title} to Cloud Favourites")

def db_clear_watchlist():
    watchlist_col.delete_many({})
    print("🗑️ Watchlist Cleared")

def db_clear_favourites():
    favs_col.delete_many({})
    print("🗑️ Favourites Cleared")

def db_remove_from_watchlist(title):
    """Deletes a single movie from the MongoDB watchlist collection by title."""
    watchlist_col.delete_one({"title": title})
    print(f"🗑️ MongoDB: Deleted {title}")