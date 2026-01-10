import json

# 1. This is a "String" - it looks like a dictionary but it's just text
raw_json_from_api = '{"movie_title": "The Matrix", "release_year": 1999, "is_available": true}'

# 2. This is the "Magic" - it converts the text into a real Python Dictionary
movie_data = json.loads(raw_json_from_api)

# 3. Now we can access specific data points
print(f"🎬 Title: {movie_data['movie_title']}")
print(f"📅 Year:  {movie_data['release_year']}")

# 4. Prove it's a Dictionary now
print(f"🔍 Type check: {type(movie_data)}")
