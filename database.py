import os
import sqlite3
from datetime import datetime, timezone
from pymongo import MongoClient
from pymongo.errors import ConfigurationError
from dotenv import load_dotenv

# 1. Load the secrets from the .env file
load_dotenv()

# 2. Pull the URI from the "environment"
# If the .env is set up correctly, this replaces the long messy string
uri = os.getenv("MONGO_URI") 

client = None
watchlist_col = None
favs_col = None
USE_MONGO = False
SQLITE_DB = "movies.db"

try:
    if uri:
        client = MongoClient(uri)
        db = client.ScottFlix_DB
        watchlist_col = db.watchlist
        favs_col = db.favourites
        USE_MONGO = True
except ConfigurationError as error:
    print(f"MongoDB unavailable, using local SQLite instead: {error}")

def _ensure_column(connection, table, column, definition):
    columns = [row[1] for row in connection.execute(f"PRAGMA table_info({table})")]
    if column not in columns:
        connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

class Movie:
    title: str
    year: str
    poster: str
    rating: str
    notes: str
    overview: str
    tmdb_id: str
    genres: str
    trailer_url: str
    added_at: str

    def __init__(
        self,
        title: str,
        year: str,
        poster: str,
        rating: str = "",
        notes: str = "",
        overview: str = "",
        tmdb_id: str = "",
        genres: str = "",
        trailer_url: str = "",
        added_at: str = "",
    ):
        self.title = title
        self.year = year
        self.poster = poster
        self.rating = rating
        self.notes = notes
        self.overview = overview
        self.tmdb_id = tmdb_id
        self.genres = genres
        self.trailer_url = trailer_url
        self.added_at = added_at

    def __repr__(self):
        return f"Movie('{self.title}', {self.year})"
    


def init_db():
    if USE_MONGO:
        print("Cloud Database Connected!")
        return

    with sqlite3.connect(SQLITE_DB) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS watchlist (
                title TEXT PRIMARY KEY,
                year TEXT,
                poster TEXT,
                overview TEXT,
                tmdb_id TEXT,
                genres TEXT,
                trailer_url TEXT,
                added_at TEXT
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS favourites (
                title TEXT PRIMARY KEY,
                year TEXT,
                poster TEXT,
                rating TEXT,
                notes TEXT,
                overview TEXT,
                tmdb_id TEXT,
                genres TEXT,
                trailer_url TEXT,
                added_at TEXT
            )
            """
        )
        _ensure_column(connection, "watchlist", "year", "TEXT")
        _ensure_column(connection, "watchlist", "poster", "TEXT")
        _ensure_column(connection, "watchlist", "overview", "TEXT")
        _ensure_column(connection, "watchlist", "tmdb_id", "TEXT")
        _ensure_column(connection, "watchlist", "genres", "TEXT")
        _ensure_column(connection, "watchlist", "trailer_url", "TEXT")
        _ensure_column(connection, "watchlist", "added_at", "TEXT")
        _ensure_column(connection, "favourites", "year", "TEXT")
        _ensure_column(connection, "favourites", "poster", "TEXT")
        _ensure_column(connection, "favourites", "rating", "TEXT")
        _ensure_column(connection, "favourites", "notes", "TEXT")
        _ensure_column(connection, "favourites", "overview", "TEXT")
        _ensure_column(connection, "favourites", "tmdb_id", "TEXT")
        _ensure_column(connection, "favourites", "genres", "TEXT")
        _ensure_column(connection, "favourites", "trailer_url", "TEXT")
        _ensure_column(connection, "favourites", "added_at", "TEXT")
    print("Local SQLite database ready.")

def _now():
    return datetime.now(timezone.utc).isoformat()

def _movie_from_doc(doc):
    return Movie(
        doc.get('title', ''),
        doc.get('year', ''),
        doc.get('poster', ''),
        doc.get('rating', ''),
        doc.get('notes', ''),
        doc.get('overview', ''),
        doc.get('tmdb_id', ''),
        doc.get('genres', ''),
        doc.get('trailer_url', ''),
        doc.get('added_at', ''),
    )

def db_add_movie(title, year, poster, overview="", tmdb_id="", genres="", trailer_url=""):
    added_at = _now()
    movie_doc = {
        "title": title,
        "year": year,
        "poster": poster,
        "overview": overview,
        "tmdb_id": tmdb_id,
        "genres": genres,
        "trailer_url": trailer_url,
        "added_at": added_at,
    }
    if USE_MONGO:
        existing = watchlist_col.find_one({"title": title}, {"_id": 0, "added_at": 1})
        if existing and existing.get("added_at"):
            movie_doc["added_at"] = existing["added_at"]
        watchlist_col.update_one({"title": title}, {"$set": movie_doc}, upsert=True)
    else:
        with sqlite3.connect(SQLITE_DB) as connection:
            existing = connection.execute("SELECT added_at FROM watchlist WHERE title = ?", (title,)).fetchone()
            if existing and existing[0]:
                movie_doc["added_at"] = existing[0]
            connection.execute(
                """
                INSERT OR REPLACE INTO watchlist
                (title, year, poster, overview, tmdb_id, genres, trailer_url, added_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    title,
                    year,
                    poster,
                    overview,
                    tmdb_id,
                    genres,
                    trailer_url,
                    movie_doc["added_at"],
                ),
            )
    print(f"Added {title} to Watchlist")

def db_get_watchlist():
    if USE_MONGO:
        raw_data = list(watchlist_col.find({}, {"_id": 0}))
        return [_movie_from_doc(movie) for movie in raw_data]

    with sqlite3.connect(SQLITE_DB) as connection:
        rows = connection.execute(
            """
            SELECT title, year, poster, overview, tmdb_id, genres, trailer_url, added_at
            FROM watchlist
            ORDER BY title
            """
        ).fetchall()
    return [
        Movie(title, year, poster, overview=overview, tmdb_id=tmdb_id, genres=genres, trailer_url=trailer_url, added_at=added_at)
        for title, year, poster, overview, tmdb_id, genres, trailer_url, added_at in rows
    ]

def db_get_favourites():
    if USE_MONGO:
        raw_data = list(favs_col.find({}, {"_id": 0}))
        return [_movie_from_doc(movie) for movie in raw_data]

    with sqlite3.connect(SQLITE_DB) as connection:
        rows = connection.execute(
            """
            SELECT title, year, poster, rating, notes, overview, tmdb_id, genres, trailer_url, added_at
            FROM favourites
            ORDER BY title
            """
        ).fetchall()
    return [
        Movie(title, year, poster, rating, notes, overview, tmdb_id, genres, trailer_url, added_at)
        for title, year, poster, rating, notes, overview, tmdb_id, genres, trailer_url, added_at in rows
    ]

def db_add_favourite(title, year, poster, rating, notes="", overview="", tmdb_id="", genres="", trailer_url=""):
    added_at = _now()
    fav_doc = {
        "title": title,
        "year": year,
        "poster": poster,
        "rating": rating,
        "notes": notes,
        "overview": overview,
        "tmdb_id": tmdb_id,
        "genres": genres,
        "trailer_url": trailer_url,
        "added_at": added_at,
    }
    if USE_MONGO:
        existing = favs_col.find_one({"title": title}, {"_id": 0, "added_at": 1})
        if existing and existing.get("added_at"):
            fav_doc["added_at"] = existing["added_at"]
        favs_col.update_one({"title": title}, {"$set": fav_doc}, upsert=True)
    else:
        with sqlite3.connect(SQLITE_DB) as connection:
            existing = connection.execute("SELECT added_at FROM favourites WHERE title = ?", (title,)).fetchone()
            if existing and existing[0]:
                fav_doc["added_at"] = existing[0]
            connection.execute(
                """
                INSERT OR REPLACE INTO favourites
                (title, year, poster, rating, notes, overview, tmdb_id, genres, trailer_url, added_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (title, year, poster, rating, notes, overview, tmdb_id, genres, trailer_url, fav_doc["added_at"]),
            )
    print(f"Added {title} to Favourites")

def db_update_favourite(title, rating, notes):
    update_doc = {"rating": rating, "notes": notes}
    if USE_MONGO:
        favs_col.update_one({"title": title}, {"$set": update_doc})
    else:
        with sqlite3.connect(SQLITE_DB) as connection:
            connection.execute(
                "UPDATE favourites SET rating = ?, notes = ? WHERE title = ?",
                (rating, notes, title),
            )
    print(f"Updated {title} in Favourites")

def db_clear_watchlist():
    if USE_MONGO:
        watchlist_col.delete_many({})
    else:
        with sqlite3.connect(SQLITE_DB) as connection:
            connection.execute("DELETE FROM watchlist")
    print("Watchlist cleared")

def db_clear_favourites():
    if USE_MONGO:
        favs_col.delete_many({})
    else:
        with sqlite3.connect(SQLITE_DB) as connection:
            connection.execute("DELETE FROM favourites")
    print("Favourites cleared")

def db_remove_from_watchlist(title):
    if USE_MONGO:
        watchlist_col.delete_one({"title": title})
    else:
        with sqlite3.connect(SQLITE_DB) as connection:
            connection.execute("DELETE FROM watchlist WHERE title = ?", (title,))
    print(f"Removed {title} from Watchlist")

def db_remove_from_favourite(title):
    if USE_MONGO:
        favs_col.delete_one({"title": title})
    else:
        with sqlite3.connect(SQLITE_DB) as connection:
            connection.execute("DELETE FROM favourites WHERE title = ?", (title,))
    print(f"Removed {title} from Favourites")
