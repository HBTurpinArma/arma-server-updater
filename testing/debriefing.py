##Read in the killcounts from the txt file using regex and print them out in a formatted way.
import re
from matplotlib import font_manager
from PIL import Image, ImageDraw, ImageFont
import json

kill_data = {}

def get_kill_data():
    with open('S:\\Github\\HBTurpinArma\\arma-server-updater\\testing\\killcounts.txt', 'r') as f:
        data = f.read()

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


get_kill_data()

def create_image_summary():
    #Load the debriefing template image
    img = Image.open("debriefing_template.png")
    draw = ImageDraw.Draw(img)

    #Setup fonts
    medium_title_font = ImageFont.truetype("Purista-Medium.ttf", 16)
    medium_body_font = ImageFont.truetype("Purista-Medium.ttf", 13)
    header_number_font = ImageFont.truetype("Purista-Bold.ttf", 18)
    mission_name_font = ImageFont.truetype("Purista-Bold.ttf", 13)

    #Get the total kills and civilian casualties
    total_kills = sum(player["killsInfantry"] for player in kill_data.values())
    total_deaths = sum(player["deaths"] for player in kill_data.values())
    civilian_casualties = 0  # Placeholder for civilian casualties
    draw.text((372, 132), f"{total_kills}", fill=(255, 255, 255), font=header_number_font, align="right", anchor="rm")
    draw.text((563, 132), f"{total_deaths}", fill=(255, 255, 255), font=header_number_font, align="right", anchor="rm")
    draw.text((753, 132), f"{civilian_casualties}", fill=(255, 255, 255), font=header_number_font, align="right", anchor="rm")

    #Setup the mission name at the top
    mission_name = "Atlas War Finale".upper()  # Placeholder mission name
    draw.text((img.width // 2, 102), mission_name, fill=(255, 255, 255), font=mission_name_font, anchor="mm")


    #Player stats header
    spacing = 62
    draw.text((207, 170), "Name", fill=(255, 255, 255), font=medium_title_font, anchor="lm")
    draw.text((420 + (spacing * 0), 170), "Infantry", fill=(255, 255, 255), font=medium_title_font, anchor="mm")
    draw.text((420 + (spacing * 1), 170), "Light", fill=(255, 255, 255), font=medium_title_font, anchor="mm")
    draw.text((420 + (spacing * 2), 170), "Armored", fill=(255, 255, 255), font=medium_title_font, anchor="mm")
    draw.text((420 + (spacing * 3), 170), "Air", fill=(255, 255, 255), font=medium_title_font, anchor="mm")
    draw.text((420 + (spacing * 4), 170), "Score", fill=(255, 255, 255), font=medium_title_font, anchor="mm")
    draw.text((420 + (spacing * 5), 170), "Deaths", fill=(255, 255, 255), font=medium_title_font, anchor="mm")

    #List each player's stats
    for player in kill_data:
        pdata = kill_data[player]
        index = list(kill_data.keys()).index(player)
        if index >= 10:
            break
        y_position = 193 + index * 20
        draw.text((207, y_position), pdata["name"], fill=(255, 255, 255), font=medium_body_font, anchor="lm")
        draw.text((420+(spacing*0), y_position), str(pdata["killsInfantry"]), fill=(255, 255, 255), font=medium_body_font, anchor="mm")
        draw.text((420+(spacing*1), y_position), str(pdata["killsSoft"]), fill=(255, 255, 255), font=medium_body_font, anchor="mm")
        draw.text((420+(spacing*2), y_position), str(pdata["killsArmor"]), fill=(255, 255, 255), font=medium_body_font, anchor="mm")
        draw.text((420+(spacing*3), y_position), str(pdata["killsAir"]), fill=(255, 255, 255), font=medium_body_font, anchor="mm")
        draw.text((420+(spacing*4), y_position), str(pdata["score"]), fill=(255, 255, 255), font=medium_body_font, anchor="mm")
        draw.text((420+(spacing*5), y_position), str(pdata["deaths"]), fill=(255, 255, 255), font=medium_body_font, anchor="mm")





    #Save and show the image
    img.save('killcounts_output.png')
    img.show()

create_image_summary()
