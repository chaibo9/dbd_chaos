import pandas as pd
import sqlite3

# load csv file
csv_file = 'data/perks_data.csv'  # path
df = pd.read_csv(csv_file)

# connect/create db
conn = sqlite3.connect('perks.db')
c = conn.cursor()

# table if not existed already
c.execute('''
CREATE TABLE IF NOT EXISTS perks (
    perk_id INTEGER PRIMARY KEY,     -- Use perk_id as the primary key
    perk_name TEXT NOT NULL,          -- Perk name from CSV
    image_filename TEXT NOT NULL      -- Filename of the image
)
''')

# insert data from DataFrame into SQLite
for _, row in df.iterrows():
    c.execute('INSERT INTO perks (perk_id, perk_name, image_filename) VALUES (?, ?, ?)', 
              (row['ID'], row['Perk'], row['Image']))

# close
conn.commit()
conn.close()

print("CSV data has been inserted into the SQLite database successfully.")
