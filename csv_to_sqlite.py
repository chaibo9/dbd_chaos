import pandas as pd
import sqlite3

# Load the CSV file into a pandas DataFrame
csv_file = 'data/perks_data.csv'  # Path to your downloaded CSV file
df = pd.read_csv(csv_file)

# Connect to SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect('perks.db')
c = conn.cursor()

# Create a table for perks data (if it doesn't already exist)
c.execute('''
CREATE TABLE IF NOT EXISTS perks (
    perk_id INTEGER PRIMARY KEY,     -- Use perk_id as the primary key
    perk_name TEXT NOT NULL,          -- Perk name from CSV
    image_filename TEXT NOT NULL      -- Filename of the image
)
''')

# Insert data from DataFrame into SQLite table
for _, row in df.iterrows():
    c.execute('INSERT INTO perks (perk_id, perk_name, image_filename) VALUES (?, ?, ?)', 
              (row['ID'], row['Perk'], row['Image']))

# Commit and close the connection
conn.commit()
conn.close()

print("CSV data has been inserted into the SQLite database successfully.")
