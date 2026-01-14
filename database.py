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

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS favourites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT UNIQUE NOT NULL,
            year TEXT,
            personal_notes TEXT,
            added_on DATETIME DEFAULT CURRENT_TIMESTAMP
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

def db_add_favourite(title, year, notes):
    connection = sqlite3.connect("movies.db")
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO favourites (title, year, personal_notes)
        VALUES (?, ?, ?)
    """, (title, year, notes))

    connection.commit()
    connection.close()

    return {"status": "success", "message": f"Added {title} to your Favourites!"}

def db_get_favourites():
    connection = sqlite3.connect("movies.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute("SELECT id, title, year, personal_notes, added_on FROM favourites")
    rows = cursor.fetchall()

    favourites = [dict(row) for row in rows]

    connection.close()
    return favourites

def db_clear_favourites():
    connection = sqlite3.connect("movies.db")
    cursor = connection.cursor()

    cursor.execute("DELETE FROM favourites")

    connection.commit()
    connection.close()
    return {"status": "success", "message": "SQL Favourites table cleared!"}

if __name__ == "__main__":
    init_db()
    
    db_add_favourite("Inception", "2010", "Absolutely mind-bending, loved the ending.")
    print("Test movie added to Favourites!")