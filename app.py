import threading
from flask import Flask, render_template, jsonify, session, redirect, url_for, request, flash
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
from waitress import serve
from flask_session import Session

app = Flask(__name__)

#config
app.secret_key = "TW3runB5HCB2tZ8eNQp0kMc4no5sXyVk"
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Constants
STEAM_OPENID_URL = "https://steamcommunity.com/openid/login"
STEAM_API_KEY = "insert key"  # steam api key
BOT_DISCORD = "insert key here"  # discord bot key

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
    conn = sqlite3.connect('database/info.db')
    c = conn.cursor()
    c.execute('SELECT perk_name, image_filename FROM perks WHERE perk_name = ?', (perk_name,))
    perk_data = c.fetchone()
    conn.close()
    return perk_data


@app.route('/login')
def login():
    return redirect(
        f"{STEAM_OPENID_URL}?openid.ns=http://specs.openid.net/auth/2.0"
        f"&openid.mode=checkid_setup"
        f"&openid.return_to={url_for('authorize', _external=True)}"
        f"&openid.realm={url_for('authorize', _external=True)}"
        f"&openid.identity=http://specs.openid.net/auth/2.0/identifier_select"
        f"&openid.claimed_id=http://specs.openid.net/auth/2.0/identifier_select"
    )


@app.route('/authorize')
def authorize():
    if 'openid.claimed_id' not in request.args:
        flash("Login failed", "error")
        return redirect(url_for('home'))

    # Parse SteamID from the claimed_id
    steam_id = request.args['openid.claimed_id'].split('/')[-1]
    session['steam_id'] = steam_id

    # Fetch additional user info
    user_info = fetch_steam_user_info(steam_id)
    session['user_info'] = user_info

    flash(f"Welcome, {user_info['personaname']}!", "success")
    return redirect(url_for('home'))


def fetch_steam_user_info(steam_id):
    try:
        # Fetch basic user info
        response = requests.get(
            f"http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={STEAM_API_KEY}&steamids={steam_id}"
        )
        if response.status_code == 200:
            user_info = response.json()['response']['players'][0]
        else:
            user_info = {}

        # Fetch playtime data for Dead by Daylight
        playtime_response = requests.get(
            f"https://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={STEAM_API_KEY}&steamid={steam_id}&format=json"
        )
        if playtime_response.status_code == 200:
            games = playtime_response.json().get('response', {}).get('games', [])
            dbd_game = next((game for game in games if game['appid'] == 381210), None)
            if dbd_game:
                user_info['playtime_forever'] = dbd_game.get('playtime_forever', 0) // 60  # convert minutes to hours
                user_info['playtime_2weeks'] = dbd_game.get('playtime_2weeks', 0) // 60 
                user_info['last_played'] = datetime.fromtimestamp(dbd_game.get('rtime_last_played', 0)).strftime('%Y-%m-%d %H:%M:%S')
            else:
                user_info['playtime_forever'] = 0
                user_info['playtime_2weeks'] = 0
                user_info['last_played'] = 'N/A'
        else:
            user_info['playtime_forever'] = 0
            user_info['playtime_2weeks'] = 0
            user_info['last_played'] = 'N/A'

        # fetch extra DBD stats
        stats_response = requests.get(
            f"https://api.steampowered.com/ISteamUserStats/GetUserStatsForGame/v0002/?appid=381210&key={STEAM_API_KEY}&steamid={steam_id}"
        )
        if stats_response.status_code == 200:
            stats = stats_response.json().get('playerstats', {}).get('stats', [])
            user_info['DBD_BloodwebPoints'] = f"{next((stat['value'] for stat in stats if stat['name'] == 'DBD_BloodwebPoints'), 0):,}"
            user_info['DBD_MaxBloodwebPointsOneCategory'] = f"{next((stat['value'] for stat in stats if stat['name'] == 'DBD_MaxBloodwebPointsOneCategory'), 0):,}"
            user_info['DBD_BloodwebMaxPrestigeLevel'] = next((stat['value'] for stat in stats if stat['name'] == 'DBD_BloodwebMaxPrestigeLevel'), 0)
        else:
            user_info['DBD_BloodwebPoints'] = "0"
            user_info['DBD_MaxBloodwebPointsOneCategory'] = "0"
            user_info['DBD_BloodwebMaxPrestigeLevel'] = 0

        return user_info
    except IndexError:
        return None
    
def resolve_vanity_url(vanity_url):
    url = f'http://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/?key={STEAM_API_KEY}&vanityurl={vanity_url}'
    response = requests.get(url)
    data = response.json()
    if data['response']['success'] == 1:
        return data['response']['steamid']
    return None

@app.route('/')
def home():
    top_3_1v1 = get_top_3_1v1()
    top_3_4v1 = get_top_3_4v1()
    tournament_name, _ = get_4v1_leaderboard()  # Fetch the tournament name
    return render_template('home.html', top_3_1v1=top_3_1v1, top_3_4v1=top_3_4v1, tournament_name=tournament_name)

def get_top_3_1v1():
    conn = sqlite3.connect('lb_sc/1v1/lb.db')
    c = conn.cursor()
    c.execute("SELECT Name, Wins, Points FROM \"1V1LB\" ORDER BY Points DESC LIMIT 3")
    top_3 = c.fetchall()
    conn.close()
    return top_3

def get_top_3_4v1():
    conn = sqlite3.connect('lb_sc/Teams/teams_lb.db')
    c = conn.cursor()
    c.execute("""
        SELECT r.rank, r.team_name, r.elo
        FROM results r
        JOIN tournaments t ON r.tournament_id = t.tournament_id
        ORDER BY r.rank ASC
        LIMIT 3
    """)
    top_3 = c.fetchall()
    conn.close()
    return top_3

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('home'))

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    if query:
        # first check their steam id
        user_info = fetch_steam_user_info(query)
        if user_info:
            return redirect(url_for('profile', steam_id=query))
        
        # if not, check custom steam id
        steam_id = resolve_vanity_url(query)
        if steam_id:
            return redirect(url_for('profile', steam_id=steam_id))
        
        flash("Invalid Steam ID or Vanity URL!", "error")
    return redirect(url_for('home'))

@app.route('/profile/<steam_id>')
def profile(steam_id):
    user_info = fetch_steam_user_info(steam_id)
    if not user_info:
        return redirect(url_for('home'))
    
    user_role = get_user_role(steam_id)
    return render_template('profile.html', user_info=user_info, user_role=user_role)

def get_user_role(steam_id):
    conn = sqlite3.connect('database/info.db')
    c = conn.cursor()
    c.execute('SELECT role FROM user_roles WHERE steam_id = ?', (steam_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None


# route to display the Shrine of Secrets
@app.route('/shrine')
def shrine_of_secrets():
    return render_template('shrine.html', perks=perks_to_display)

@app.route('/leaderboards')
def leaderboards():
    leaderboard_1v1 = get_1v1_leaderboard()
    tournament_name, leaderboard_4v1 = get_4v1_leaderboard()
    return render_template('leaderboards.html', leaderboard_1v1=leaderboard_1v1, leaderboard_4v1=leaderboard_4v1, tournament_name=tournament_name)

def get_leaderboard():
    conn = sqlite3.connect('lb_sc/lb.db')
    c = conn.cursor()
    c.execute("SELECT Name, Wins, Points FROM \"1V1LB\" ORDER BY Points DESC LIMIT 50")
    leaderboard = c.fetchall()
    conn.close()
    return leaderboard

def get_1v1_leaderboard():
    conn = sqlite3.connect('lb_sc/1v1/lb.db')
    c = conn.cursor()
    c.execute("SELECT Name, Wins, Points FROM \"1V1LB\" ORDER BY Points DESC LIMIT 50")
    leaderboard = c.fetchall()
    conn.close()
    return leaderboard

def get_4v1_leaderboard():
    conn = sqlite3.connect('lb_sc/Teams/teams_lb.db')
    c = conn.cursor()
    c.execute("""
        SELECT t.name, r.rank, r.team_name, r.elo
        FROM results r
        JOIN tournaments t ON r.tournament_id = t.tournament_id
        ORDER BY r.rank ASC
        LIMIT 50
    """)
    data = c.fetchall()
    conn.close()
    
    if data:
        tournament_name = data[0][0]
        leaderboard = [(row[1], row[2], row[3]) for row in data]
        return tournament_name, leaderboard
    return None, []

# route to display the Staff page
@app.route('/staff')
def staff():
    staff_members = get_staff_members()
    return render_template('staff.html', staff_members=staff_members)

def get_staff_members():
    conn = sqlite3.connect('database/info.db')
    c = conn.cursor()
    roles = ['Owner', 'Admin', 'Manager', 'Developer', 'Moderator']
    staff_members = {}

    for role in roles:
        c.execute("SELECT steam_id FROM user_roles WHERE role = ?", (role,))
        members = c.fetchall()
        if members:
            staff_members[role] = []
            for member in members:
                steam_id = member[0]
                user_info = fetch_steam_user_info(steam_id)
                if user_info:
                    staff_members[role].append({
                        'steam_id': steam_id,
                        'username': user_info['personaname'],
                        'profile_image': user_info['avatarfull']
                    })

    conn.close()
    return staff_members

@app.route('/api/perks')
def get_perks():
    return jsonify(perks_to_display)

# scheduler config to run the job daily and check shrine of secrets
def start_scheduler():
    scheduler = BackgroundScheduler()
    # Schedule the task to run every day at 3:00 PM UTC (adjust the time as needed)
    scheduler.add_job(fetch_and_update_perks, 'cron', hour=15, minute=1)
    scheduler.start()

def create_perk_image(perks):
    # load background image
    background = Image.open("static/perks_bg/sos_bg.jpg")

    # positions for the perk logos
    positions = [(77, 161), (420, 161), (77, 495), (420, 495)]

    # put perk logos on background
    for i, perk in enumerate(perks):
        if i < 4:  # only the first 4 perks
            perk_image_path = os.path.join("static", "perks", perk['image'])
            print(f"Loading perk image from: {perk_image_path}")  # debug statement
            perk_image = Image.open(perk_image_path)
            perk_image = perk_image.resize((300,300))  # resize the perk image
            background.paste(perk_image, positions[i], perk_image)

    # save image
    output_path = "static/output.png"
    background.save(output_path)
    return output_path

# run discord bot
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
                output_path = "static/output.png"  # use the pre-generated image
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

                # Fetch the bot's custom emojis
                emoji_response = requests.get(
                    'https://discord.com/api/applications/1310334123990188032/emojis',
                    headers={'Authorization': 'MTMxMDMzNDEyMzk5MDE4ODAzMg.G6byoi.UniCASsqST0dbulPDvVJHTSlgOZx72BDNmW1Qo'}
                )
                

                for i, perk in enumerate(perks):
                    perk_name = perk['name']
                    image_filename = perk['image']

                    if i < 2:
                        embed.add_field(name=f"Perk {i + 1}", value=f"{perk_name}", inline=True)
                    elif i == 2:
                        embed.add_field(name="", value="", inline=False)  # Add a blank line
                        embed.add_field(name=f"Perk {i + 1}", value=f"{perk_name}", inline=True)
                    else:
                        embed.add_field(name=f"Perk {i + 1}", value=f"{perk_name}", inline=True)

                embed.set_footer(
                    text="DBD Chaos | Shrine of Secrets",
                    icon_url="https://cdn.discordapp.com/attachments/1033180877267685406/1310460354664464454/bot_logo.jpg"
                )

                await ctx.send(embed=embed)
            else:
                await ctx.send("No perks available at the moment.")
        else:
            await ctx.send("Failed to fetch the Shrine of Secrets perks.")

    client.run(BOT_DISCORD)

# Function to run the Flask server
def run_flask():
    fetch_and_update_perks()  # Initial call to fetch data
    start_scheduler()  # Start scheduler for daily updates
    app.run(debug=True)

# Start both the Flask server and the Discord bot concurrently
if __name__ == '__main__':
    discord_thread = threading.Thread(target=run_discord_bot, daemon=True)
    discord_thread.start()
    run_flask()  # Run Flask in the main thread
