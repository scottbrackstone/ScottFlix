import sqlite3

def init_db():
    connection = sqlite3.connect("movies.db")
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS watchlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT UNIQUE NOT NULL,
            year TEXT,
            rating REAL,
            category TEXT DEFAULT 'Uncategorized'
        )
    """)

    connection.commit()
    connection.close()
    print("✅ Database initialized and Table created!")

def db_add_movie(title, year, rating):
    connection = sqlite3.connect("movies.db")
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO watchlist (title, year, rating)
        VALUES (?, ?, ?)
    """, (title, year, rating))

    connection.commit()
    connection.close()

    return {"status": "success", "message": f"Saved {title} to the SQL Database!"}   

def db_get_watchlist():
    connection = sqlite3.connect("movies.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute("SELECT id, title, year, rating FROM watchlist")
    rows = cursor.fetchall()
    
    watchlist = [dict(row) for row in rows]
    
    connection.close()
    return watchlist

def db_clear_watchlist():
    connection = sqlite3.connect("movies.db")
    cursor = connection.cursor()

    cursor.execute("DELETE FROM watchlist")
    
    connection.commit()
    connection.close()
    return {"status": "success", "message": "SQL Watchlist cleared!"}

if __name__ == "__main__":
    init_db()
    
    db_add_movie("The Matrix", "1999", 8.7)
    
    my_movies = db_get_watchlist()
    print(f"Watchlist: {my_movies}")


