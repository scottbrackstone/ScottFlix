from fastapi import FastAPI
from movie_search import search_movie 
from database import (db_add_movie, db_get_watchlist, init_db, db_clear_watchlist,
    db_add_favourite, db_get_favourites, db_clear_favourites
)

app = FastAPI()

init_db()

@app.get("/")
def home():
    return {
        "user": "Scott",
        "role": "Full-Stack Developer Learner",
        "status": "Online",
        "message": "Welcome to the Scott Codes Movie API!"
    }

@app.get("/search")
def web_search(title: str):
    data = search_movie(title)
    return data

@app.get("/greet/{name}")
def greet_user(name: str):
    return {"message": f"Hello, {name}! Your API is running perfectly."}

@app.get("/watchlist")
def web_get_watchlist():
    return db_get_watchlist()

@app.post("/watchlist")
def web_add_to_watchlist(title: str, year: str = "Unknown", rating: float = 0.0):
    result = db_add_movie(title, year, rating)
    return result

@app.delete("/watchlist")
def web_clear_watchlist():
    return db_clear_watchlist() 

@app.get("/favourites")
def web_get_favourites():
    return db_get_favourites()

@app.post("/favourites")
def web_add_to_favourite(title: str, year: str, notes: str = "No notes added"):
    return db_add_favourite(title, year, notes)

@app.delete("/favourites")
def web_clear_favourites():
    return {"message": "Endpoint ready! Next, build the database function."}

@app.delete("/favourites")
def web_clear_favourites():
    return db_clear_favourites()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)