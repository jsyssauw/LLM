import sqlite3

print("starting")

# Connect to the SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect("D:\Programs\LLM\projects\llm_engineering\Anthropic\SQLLITEDB\cache_db")

# Create a cursor object using the connection
cursor = conn.cursor()

# Create a table if it doesn't exist
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    age INTEGER NOT NULL
)
''')

# Insert rows into the table
cursor.execute("INSERT INTO users (name, age) VALUES ('Alice', 30)")
cursor.execute("INSERT INTO users (name, age) VALUES ('Bob', 25)")

# Commit the changes to the database
conn.commit()

# Update a row in the table
cursor.execute("UPDATE users SET age = 31 WHERE name = 'Alice'")
conn.commit()

# Retrieve and print all rows from the table
cursor.execute("SELECT * FROM users")
rows = cursor.fetchall()
print("Users in the database:")
for row in rows:
    print(row)

# Close the connection to the database
conn.close()