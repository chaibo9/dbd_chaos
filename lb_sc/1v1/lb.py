import re
import sqlite3

# Specify the input file containing the leaderboard data
input_file = "leaderboard_data.txt"

# Read the data from the text file
with open(input_file, "r", encoding="utf-8") as file:
    data = file.read()

# Define the regex pattern to extract Placement, Name, Wins, and Points
pattern = re.compile(
    r"#(\d+)\s+(.+?)\n(?:.*\n)?(\d+)\s+won\s+\|\s+(\d+)\s+pts"
)

# Extract the data
matches = pattern.findall(data)

# Connect to the SQLite database
db_file = "lb.db"
connection = sqlite3.connect(db_file)
cursor = connection.cursor()

try:
    # Ensure the table exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS "1V1LB" (
            Placement INTEGER PRIMARY KEY,
            Name TEXT,
            Wins INTEGER,
            Points INTEGER
        );
    """)
    connection.commit()

    # Clear the table before inserting new data
    cursor.execute("DELETE FROM \"1V1LB\";")
    connection.commit()

    # insert data extracted into database
    for match in matches:
        placement, name, wins, points = match
        cursor.execute(
            "INSERT INTO \"1V1LB\" (Placement, Name, Wins, Points) VALUES (?, ?, ?, ?);",
            (int(placement), name.strip().replace("'", "''"), int(wins), int(points))
        )
    connection.commit()
    print(f"Data has been successfully inserted into the database '{db_file}'.")
except sqlite3.Error as e:
    print(f"An error occurred: {e}")
    connection.rollback()
finally:
    # close connection
    connection.close()
