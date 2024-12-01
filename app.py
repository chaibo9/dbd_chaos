import threading
from flask import Flask, render_template, jsonify
import requests
import sqlite3
from apscheduler.schedulers.background import BackgroundScheduler
import discord
from discord.ext import commands
from discord.ext.commands import HybridCommand
from PIL import Image
import os
from datetime import datetime
import time

app = Flask(__name__)

# Global variable to store perks data
perks_to_display = []

# API URL for the Shrine of Secrets
SHRINE_API_URL = "https://api.nightlight.gg/v1/shrine"

# Fetch perks data from API
def fetch_and_update_perks():
    global perks_to_display
    response = requests.get(SHRINE_API_URL)
    if response.status_code == 200:
        shrine_data = response.json()
        perks_from_api = shrine_data['data']['perks']

        # Fetch the perks' images from the database
        updated_perks = []
        for perk in perks_from_api:
            perk_name = perk['name']
            #character name that perk comes from
            character_name = perk['character']
            perk_data = get_perk_data_from_db(perk_name)
            if perk_data:
                updated_perks.append({
                    'name': perk_data[0],  # perk_name
                    'image': perk_data[1],  # image_filename
                    'character': character_name # character_name
                })

        # Update the global perks_to_display
        perks_to_display = updated_perks
        print(f"Perks updated successfully.")

        # Create the image with the perk logos
        create_perk_image(perks_to_display)

# Get perk data (name + image) from the local SQLite database
def get_perk_data_from_db(perk_name):
    conn = sqlite3.connect('database/perks.db')
    c = conn.cursor()
    c.execute('SELECT perk_name, image_filename FROM perks WHERE perk_name = ?', (perk_name,))
    perk_data = c.fetchone()
    conn.close()
    return perk_data

# Route to display the Shrine of Secrets
@app.route('/')
def shrine_of_secrets():
    return render_template('shrine.html', perks=perks_to_display)

@app.route('/api/perks')
def get_perks():
    return jsonify(perks_to_display)

# Scheduler configuration to run the job daily
def start_scheduler():
    scheduler = BackgroundScheduler()
    # Schedule the task to run every day at 3:00 PM UTC (adjust the time as needed)
    scheduler.add_job(fetch_and_update_perks, 'cron', hour=15, minute=1)
    scheduler.start()

# Function to run the Flask server
def run_flask():
    fetch_and_update_perks()  # Initial call to fetch data
    start_scheduler()  # Start scheduler for daily updates
    app.run(host='0.0.0.0')

def create_perk_image(perks):
    # Load the background image
    background = Image.open("static/perks_bg/sos_bg.jpg")

    # Define the positions for the perk logos
    positions = [(77, 161), (420, 161), (77, 495), (420, 495)]

    # Paste the perk logos onto the background
    for i, perk in enumerate(perks):
        if i < 4:  # Only handle the first 4 perks
            perk_image_path = os.path.join("static", "perks", perk['image'])
            print(f"Loading perk image from: {perk_image_path}")  # Debugging statement
            perk_image = Image.open(perk_image_path)
            perk_image = perk_image.resize((300,300))  # Resize the perk image
            background.paste(perk_image, positions[i], perk_image)

    # Save the resulting image
    output_path = "static/output.png"
    background.save(output_path)
    return output_path

# Function to run the Discord bot
def run_discord_bot():
    client = commands.Bot(command_prefix="!", intents=discord.Intents.all())

    @client.event
    async def on_ready():
        await client.tree.sync() # sync global commands
        await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name='/shrine'))
        print(f'Logged in as {client.user}')
        print("---------------------------")


    @client.hybrid_command(name="shrine", with_app_command=True, description="Display the current Shrine of Secrets perks")
    async def shrine(ctx):
        response = requests.get('http://127.0.0.1:5000/api/perks')
        if response.status_code == 200:
            perks = response.json()
            if perks:
                output_path = "static/output.png"  # Use the pre-generated image
                await ctx.send(file=discord.File(output_path))

                embed = discord.Embed(
                    title="Shrine of Secrets",
                    url="http://dbdchaos.com/",
                    colour=0xa31aff,
                    timestamp=datetime.now()
                )

                embed.set_author(
                    name="DBD Chaos",
                    url="http://dbdchaos.com/",
                    icon_url="https://cdn.discordapp.com/attachments/1033180877267685406/1310460354664464454/bot_logo.jpg"
                )

                for i, perk in enumerate(perks):
                    if i < 2:
                        embed.add_field(name=f"Perk {i + 1}", value=perk['name'], inline=True)
                    elif i == 2:
                        embed.add_field(name="", value="", inline=False)  # Add a blank line
                        embed.add_field(name=f"Perk {i + 1}", value=perk['name'], inline=True)
                    else:
                        embed.add_field(name=f"Perk {i + 1}", value=perk['name'], inline=True)

                embed.set_footer(
                    text="DBD Chaos | Shrine of Secrets",
                    icon_url="https://cdn.discordapp.com/attachments/1033180877267685406/1310460354664464454/bot_logo.jpg"
                )

                await ctx.send(embed=embed)
            else:
                await ctx.send("No perks available at the moment.")
        else:
            await ctx.send("Failed to fetch the Shrine of Secrets perks.")

    client.run("MTMxMDMzNDEyMzk5MDE4ODAzMg.G6byoi.UniCASsqST0dbulPDvVJHTSlgOZx72BDNmW1Qo")

# Start both the Flask server and the Discord bot concurrently
if __name__ == '__main__':
    discord_thread = threading.Thread(target=run_discord_bot, daemon=True)
    discord_thread.start()
    time.sleep(1)
    run_flask()  # Run Flask in the main thread
