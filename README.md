
# Chaos | Dead by Daylight

The project was something temporary that I wanted to work on towards the competitive scene of Dead by Daylight. This is my first Flask Project from development to deployment.

Simply put, it would keep track daily of teams who competed in the tournaments both in a 4v1 and 1v1 aspect of the game. At this time, 1v1 ELO was calculated from a discord server named 'DBDLeague' that would keep track of this. The 4v1 ELO(was still thinking of a formula) was calculated using a sole tournament from 2024 of the teams that participated in it.

> [!IMPORTANT]  
> The project is archived as I was solely using it to demonstrate my learning and skills for a class. Some things may be outdated due to game updates, requiring restructuring in certain parts of it.


## Features

- Steam Login Support
- Profile Searching (steamID and Steam Custom Username)
- Ranks
  - Staff Ranks
  - VIP Ranks
- Leaderboards (Teams & Users)
- Shrine of Secrets (Thanks to NightLight.gg)
- Discord Bot
    - Image Generation for the Shrine of Secrets


## Dependencies
The `requirements.txt` file contains all the python libraries that are dependent on the Flask Website and Discord Bot running.
```
pip install -r requirements.txt
```
You require your own keys to connect to the Steam API and for the discord bot, which can be found under `STEAM_API_KEY` and `BOT_DISCORD`.

## Acknowledgements

 - Thanks to [BritishBoop](https://github.com/britishboop) for his API on [NightLight](https://nightlight.gg)
  - Thank you to the [DBDLeague Team](https://www.youtube.com/channel/UCK-Pz9EPp0IQe2HpKoXJS1w) for helping me in retrieve information on both the '1v1' and '4v1' games

## Preview
> [!WARNING]  
> For the 4th image, the project did not load all 4 perks due to the game having 2 **new perks** that were not in my database.
<p align="center">
  <img src ="https://github.com/chaibo9/dbd_chaos/blob/master/static/md_images_github/image1.png" width="90%">
  <img src ="https://github.com/chaibo9/dbd_chaos/blob/master/static/md_images_github/image2.png" width="90%">
  <img src ="https://github.com/chaibo9/dbd_chaos/blob/master/static/md_images_github/image3.png" width="90%">
  <img src="https://github.com/chaibo9/dbd_chaos/blob/master/static/md_images_github/image4.png" width="40%">
  <img src="https://github.com/chaibo9/dbd_chaos/blob/master/static/md_images_github/image5.png" width="40%">
</p>
