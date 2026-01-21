from fastapi import FastAPI, Request, Form, responses
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from movie_search import search_movie 
from database import (init_db, db_add_movie, db_get_watchlist, 
                      db_get_favourites, db_clear_watchlist,
                      db_add_favourite, db_clear_favourites,
                      db_remove_from_watchlist) # Added the remove import

app = FastAPI()
templates = Jinja2Templates(directory="templates")

init_db()

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    current_watchlist = db_get_watchlist()
    current_favourites = db_get_favourites()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "watchlist": current_watchlist,
        "favourites": current_favourites
    })

@app.get("/search")
def search(request: Request, title: str):
    data = search_movie(title)
    actual_movies = data.get("all_matches", []) 
    return templates.TemplateResponse("results.html", {
        "request": request, 
        "results": actual_movies
    })

@app.post("/add-to-watchlist")
def add_movie(title: str = Form(...), year: str = Form(...), poster: str = Form(...)):
    db_add_movie(title, year, poster)
    return responses.RedirectResponse(url="/", status_code=303)

# --- NEW ROUTES FOR THE HTML BUTTONS ---

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
    # Direct logic to remove from favorites collection
    from database import favs_col
    favs_col.delete_one({"title": title})
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