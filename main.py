import hashlib
import hmac
import os
import time

from fastapi import FastAPI, Request, Form, responses
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from movie_search import search_movie 
from database import (init_db, db_add_movie, db_get_watchlist, 
                      db_get_favourites, db_clear_watchlist,
                      db_add_favourite, db_clear_favourites,
                      db_remove_from_watchlist,
                      db_remove_from_favourite,
                      db_update_favourite)

app = FastAPI()
templates = Jinja2Templates(directory="templates")

init_db()

AUTH_COOKIE = "scottflix_session"
SESSION_SECONDS = 60 * 60 * 24 * 30

def passcode_required():
    return bool(os.getenv("SCOTTFLIX_PASSCODE")) or os.getenv("VERCEL") == "1"

def auth_configured():
    return bool(os.getenv("SCOTTFLIX_PASSCODE") and os.getenv("SCOTTFLIX_SECRET_KEY"))

def sign_session(expires):
    secret = os.getenv("SCOTTFLIX_SECRET_KEY", "")
    return hmac.new(secret.encode("utf-8"), str(expires).encode("utf-8"), hashlib.sha256).hexdigest()

def create_session_token():
    expires = int(time.time()) + SESSION_SECONDS
    return f"{expires}:{sign_session(expires)}"

def valid_session(request: Request):
    token = request.cookies.get(AUTH_COOKIE, "")
    try:
        expires_text, signature = token.split(":", 1)
        expires = int(expires_text)
    except ValueError:
        return False

    if expires < int(time.time()):
        return False

    expected = sign_session(expires)
    return hmac.compare_digest(signature, expected)

@app.middleware("http")
async def protect_scottflix(request: Request, call_next):
    public_paths = {"/login", "/favicon.ico"}
    if request.url.path in public_paths:
        return await call_next(request)

    if not passcode_required():
        return await call_next(request)

    if not auth_configured():
        return HTMLResponse(
            "ScottFlix passcode protection is enabled, but SCOTTFLIX_PASSCODE and SCOTTFLIX_SECRET_KEY are not configured.",
            status_code=503,
        )

    if valid_session(request):
        return await call_next(request)

    return responses.RedirectResponse(url="/login", status_code=303)

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    if passcode_required() and auth_configured() and valid_session(request):
        return responses.RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request, "error": ""})

@app.post("/login")
def login(request: Request, passcode: str = Form(...)):
    configured_passcode = os.getenv("SCOTTFLIX_PASSCODE", "")
    if not configured_passcode or not hmac.compare_digest(passcode, configured_passcode):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "That passcode was not right."},
            status_code=401,
        )

    response = responses.RedirectResponse(url="/", status_code=303)
    response.set_cookie(
        AUTH_COOKIE,
        create_session_token(),
        max_age=SESSION_SECONDS,
        httponly=True,
        secure=os.getenv("VERCEL") == "1",
        samesite="lax",
    )
    return response

@app.get("/logout")
def logout():
    response = responses.RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(AUTH_COOKIE)
    return response

def enrich_saved_movies(movies, list_name):
    for movie in movies:
        if (
            movie.overview
            and not movie.overview.endswith("...")
            and movie.genres
            and movie.trailer_url
        ):
            continue

        data = search_movie(movie.title)
        matches = data.get("all_matches", [])
        if not matches:
            continue

        match = next(
            (
                item for item in matches
                if item.get("title") == movie.title and (not movie.year or item.get("year") == movie.year)
            ),
            matches[0],
        )

        movie.overview = match.get("overview", "")
        movie.tmdb_id = match.get("tmdb_id", movie.tmdb_id)
        movie.genres = match.get("genres", movie.genres)
        movie.trailer_url = match.get("trailer_url", movie.trailer_url)
        if (not movie.poster or movie.poster == "N/A") and match.get("poster"):
            movie.poster = match["poster"]
        if not movie.year and match.get("year"):
            movie.year = match["year"]

        if list_name == "watchlist":
            db_add_movie(movie.title, movie.year, movie.poster, movie.overview, movie.tmdb_id, movie.genres, movie.trailer_url)
        else:
            db_add_favourite(movie.title, movie.year, movie.poster, movie.rating, movie.notes, movie.overview, movie.tmdb_id, movie.genres, movie.trailer_url)

def rating_value(movie):
    try:
        return float(movie.rating)
    except (TypeError, ValueError):
        return 0

def recent_value(movie):
    return movie.added_at or ""

def build_genre_rows(movies):
    rows = {}
    for movie in movies:
        for genre in [item.strip() for item in movie.genres.split(",") if item.strip()]:
            rows.setdefault(genre, []).append(movie)
    return sorted(rows.items())

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    watchlist = db_get_watchlist()
    favourites = db_get_favourites()
    enrich_saved_movies(watchlist, "watchlist")
    enrich_saved_movies(favourites, "favourites")
    top_rated = sorted(favourites, key=rating_value, reverse=True)
    recently_added = sorted(watchlist + favourites, key=recent_value, reverse=True)
    featured = top_rated[0] if top_rated else (recently_added[0] if recently_added else None)
    genre_rows = build_genre_rows(watchlist + favourites)
    return templates.TemplateResponse("index.html", {
        "request": request,
        "watchlist": watchlist,
        "favourites": favourites,
        "top_rated": top_rated,
        "recently_added": recently_added,
        "featured": featured,
        "genre_rows": genre_rows,
    })

@app.get("/search")
def search(request: Request, title: str):
    data = search_movie(title)
    actual_movies = data.get("all_matches", []) 
    saved_titles = {movie.title for movie in db_get_watchlist()} | {movie.title for movie in db_get_favourites()}
    return templates.TemplateResponse("results.html", {
        "request": request, 
        "results": actual_movies,
        "saved_titles": saved_titles,
    })

@app.post("/add-to-watchlist")
def add_movie(
    title: str = Form(...),
    year: str = Form(...),
    poster: str = Form(...),
    overview: str = Form(""),
    tmdb_id: str = Form(""),
    genres: str = Form(""),
    trailer_url: str = Form("")
):
    db_add_movie(title, year, poster, overview, tmdb_id, genres, trailer_url)
    return responses.RedirectResponse(url="/", status_code=303)

@app.post("/add-to-favourites")
def add_favourite(
    title: str = Form(...),
    year: str = Form(...),
    poster: str = Form(...),
    rating: str = Form(...),
    notes: str = Form(""),
    overview: str = Form(""),
    tmdb_id: str = Form(""),
    genres: str = Form(""),
    trailer_url: str = Form("")
):
    db_add_favourite(title, year, poster, rating, notes, overview, tmdb_id, genres, trailer_url)
    return responses.RedirectResponse(url="/", status_code=303)

@app.post("/update-favourite")
def update_favourite(
    title: str = Form(...),
    rating: str = Form(...),
    notes: str = Form("")
):
    db_update_favourite(title, rating, notes)
    return responses.RedirectResponse(url="/#favourites", status_code=303)

@app.post("/move-to-favourites")
def move_to_favourites(
    title: str = Form(...),
    year: str = Form(""),
    poster: str = Form(""),
    rating: str = Form(...),
    notes: str = Form(""),
    overview: str = Form(""),
    tmdb_id: str = Form(""),
    genres: str = Form(""),
    trailer_url: str = Form("")
):
    db_add_favourite(title, year, poster, rating, notes, overview, tmdb_id, genres, trailer_url)
    db_remove_from_watchlist(title)
    return responses.RedirectResponse(url="/#favourites", status_code=303)

@app.post("/remove-from-watchlist")
def remove_movie(title: str = Form(...)):
    db_remove_from_watchlist(title)
    return responses.RedirectResponse(url="/", status_code=303)

@app.post("/clear-watchlist")
def clear_watchlist_ui():
    db_clear_watchlist()
    return responses.RedirectResponse(url="/", status_code=303)

@app.post("/remove-from-favourites")
def remove_favourite(title: str = Form(...)):
    db_remove_from_favourite(title)
    return responses.RedirectResponse(url="/", status_code=303)

@app.post("/clear-favourites")
def clear_favourites_ui():
    db_clear_favourites()
    return responses.RedirectResponse(url="/", status_code=303)

# --- API ROUTES (Keep these for /docs testing) ---

@app.get("/greet/{name}")
def greet_user(name: str):
    return {"message": f"Hello, {name}! Your API is running perfectly."}

@app.get("/watchlist")
def web_get_watchlist():
    return db_get_watchlist()

@app.get("/favourites")
def web_get_favourites():
    return db_get_favourites()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
