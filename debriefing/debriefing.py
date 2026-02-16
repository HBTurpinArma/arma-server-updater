import re
from matplotlib import font_manager
from PIL import Image, ImageDraw, ImageFont
import json
import os

def beautify_mission_name(raw_name):
    words = raw_name.split('_')
    return ' '.join(word.capitalize() for word in words)

def get_mission_name(file_path=None):
    if file_path is not None:
        with open(file_path, "r") as f:
            data = f.read()
    else:
        # Search input folder for a .log file and read it in, if there are multiple log files read the most recent one
        log_files = [f for f in os.listdir("input") if f.endswith(".log")]
        if not log_files:
            print("No log files found in input folder.")
            return
        latest_log_file = max(log_files, key=lambda f: os.path.getctime(os.path.join("input", f)))
        with open(os.path.join("input", latest_log_file), "r") as f:
            data = f.read()

    match = re.search(r'mission="([^"]+)"', data)

    if match:
        mission_name = match.group(1)
        print(mission_name)
        print(beautify_mission_name(mission_name))
        return mission_name
    else:
        print("Mission name not found.")
        return "No Mission Name Found"


def get_kill_data(file_path=None):
    if file_path is not None:
        with open(file_path, "r") as f:
            data = f.read()
    else:
        #Search input folder for a .log file and read it in, if there are multiple log files read the most recent one
        log_files = [f for f in os.listdir("input") if f.endswith(".log")]
        if not log_files:
            print("No log files found in input folder.")
            return
        latest_log_file = max(log_files, key=lambda f: os.path.getctime(os.path.join("input", f)))
        with open(os.path.join("input", latest_log_file), "r") as f:
            data = f.read()

    kill_data = {}

    #Find each player and their kill counts using regex
    player_pattern = r'class\s+(\w+)\s*{([^}]*)};'
    players = re.findall(player_pattern, data, re.DOTALL)
    for player_index, player_data in players:
        name = re.search(r'name\s*=\s*"([^"]+)"\s*;', player_data)
        kills_inf = re.search(r'killsInfantry\s*=\s*(\d+);', player_data)
        kills_soft = re.search(r'killsSoft\s*=\s*(\d+);', player_data)
        kills_armored = re.search(r'killsArmor\s*=\s*(\d+);', player_data)
        kills_air = re.search(r'killsAir\s*=\s*(\d+);', player_data)
        total_score = re.search(r'killsTotal\s*=\s*(\d+);', player_data)
        total_deaths = re.search(r'killed\s*=\s*(\d+);', player_data)

        #Print and log the kill counts to a json file for each player
        try:
            print(f"{name.group(1)} has {kills_inf.group(1)} total kills.")
        except AttributeError:
            continue

        # Save total kills to json file
        player_data = {
            "name": name.group(1),
            "killsInfantry": int(kills_inf.group(1)) if kills_inf else 0,
            "killsSoft": int(kills_soft.group(1)) if kills_soft else 0,
            "killsArmor": int(kills_armored.group(1)) if kills_armored else 0,
            "killsAir": int(kills_air.group(1)) if kills_air else 0,
            "score": int(total_score.group(1)) if total_score else 0,
            "deaths": int(total_deaths.group(1)) if total_deaths else 0
        }
        kill_data[name.group(1)] = player_data

    return kill_data

def get_medal_data(file_path=None):
    if file_path is not None:
        with open(file_path, "r") as f:
            data = f.read()
    else:
        #Search input folder for a .log file and read it in, if there are multiple log files read the most recent one
        log_files = [f for f in os.listdir("input") if f.endswith(".rpt")]
        if not log_files:
            print("No log files found in input folder.")
            return
        latest_log_file = max(log_files, key=lambda f: os.path.getctime(os.path.join("input", f)))
        with open(os.path.join("input", latest_log_file), "r") as f:
            data = f.read()

    medal_data = {}

    return medal_data


def create_image_summary():
    #Load the debriefing template image
    img = Image.open("resources/templates/debriefing_template.png")
    draw = ImageDraw.Draw(img)

    #Setup fonts
    medium_title_font = ImageFont.truetype("resources/fonts/Purista-Medium.ttf", 16)
    medium_body_font = ImageFont.truetype("resources/fonts/Purista-Medium.ttf", 13)
    header_number_font = ImageFont.truetype("resources/fonts/Purista-Bold.ttf", 18)
    mission_name_font = ImageFont.truetype("resources/fonts/Purista-Bold.ttf", 13)

    #Get the total kills and civilian casualties
    kill_data = get_kill_data()
    total_kills = sum(player["killsInfantry"] for player in kill_data.values())
    total_deaths = sum(player["deaths"] for player in kill_data.values())
    civilian_casualties = 0  # Placeholder for civilian casualties
    draw.text((372, 132), f"{total_kills}", fill=(255, 255, 255), font=header_number_font, align="right", anchor="rm")
    draw.text((563, 132), f"{total_deaths}", fill=(255, 255, 255), font=header_number_font, align="right", anchor="rm")
    draw.text((753, 132), f"{civilian_casualties}", fill=(255, 255, 255), font=header_number_font, align="right", anchor="rm")

    #Setup the mission name at the top
    draw.text((img.width // 2, 102), get_mission_name().upper(), fill=(255, 255, 255), font=mission_name_font, anchor="mm")

    #Player stats header
    player_spacing = 62
    draw.text((207, 170), "Name", fill=(255, 255, 255), font=medium_title_font, anchor="lm")
    draw.text((420 + (player_spacing * 0), 170), "Infantry", fill=(255, 255, 255), font=medium_title_font, anchor="mm")
    draw.text((420 + (player_spacing * 1), 170), "Light", fill=(255, 255, 255), font=medium_title_font, anchor="mm")
    draw.text((420 + (player_spacing * 2), 170), "Armored", fill=(255, 255, 255), font=medium_title_font, anchor="mm")
    draw.text((420 + (player_spacing * 3), 170), "Air", fill=(255, 255, 255), font=medium_title_font, anchor="mm")
    draw.text((420 + (player_spacing * 4), 170), "Score", fill=(255, 255, 255), font=medium_title_font, anchor="mm")
    draw.text((420 + (player_spacing * 5), 170), "Deaths", fill=(255, 255, 255), font=medium_title_font, anchor="mm")

    #List each player's stats
    for player in kill_data:
        pdata = kill_data[player]
        index = list(kill_data.keys()).index(player)
        if index >= 10:
            break
        y_position = 193 + index * 20
        draw.text((207, y_position), pdata["name"], fill=(255, 255, 255), font=medium_body_font, anchor="lm")
        draw.text((420 + (player_spacing * 0), y_position), str(pdata["killsInfantry"]), fill=(255, 255, 255), font=medium_body_font, anchor="mm")
        draw.text((420 + (player_spacing * 1), y_position), str(pdata["killsSoft"]), fill=(255, 255, 255), font=medium_body_font, anchor="mm")
        draw.text((420 + (player_spacing * 2), y_position), str(pdata["killsArmor"]), fill=(255, 255, 255), font=medium_body_font, anchor="mm")
        draw.text((420 + (player_spacing * 3), y_position), str(pdata["killsAir"]), fill=(255, 255, 255), font=medium_body_font, anchor="mm")
        draw.text((420 + (player_spacing * 4), y_position), str(pdata["score"]), fill=(255, 255, 255), font=medium_body_font, anchor="mm")
        draw.text((420 + (player_spacing * 5), y_position), str(pdata["deaths"]), fill=(255, 255, 255), font=medium_body_font, anchor="mm")


    #Custom medals
    medal_data = {
        "Top Gun": {"count": sum(player["killsAir"] for player in kill_data.values()), "image_path": "medals/top_gun.png", "x": 372, "y": 162},
        "Tank Hunter": {"count": sum(player["killsArmor"] for player in kill_data.values()), "image_path": "medals/tank_hunter.png", "x": 563, "y": 162},
        "Infantry Slayer": {"count": sum(player["killsInfantry"] for player in kill_data.values()), "image_path": "medals/infantry_slayer.png", "x": 753, "y": 162},
    }
    #
    # for medal in medal_data:
    #     mdata = medal_data[medal]
    #     if mdata["count"] > 0:
    #         medal_img = Image.open(mdata["image_path"]).convert("RGBA")
    #         medal_img = medal_img.resize((20, 20))
    #         # img.paste(medal_img, (mdata["x"] - 10, mdata["y"] - 10), medal_img)




    #Save and show the image
    img.save('killcounts_output.png')
    img.show()

create_image_summary()
