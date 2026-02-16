import re
from matplotlib import font_manager
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import json
import os

def draw_blurred_rectangle(base_img, xy, fill, outline, outline_width=2, blur_radius: float = 2):
    # Create a transparent layer
    temp = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(temp)
    x0, y0, x1, y1 = xy

    # Draw outline (larger rectangle)
    for i in range(outline_width):
        draw.rectangle([x0 - i, y0 - i, x1 + i, y1 + i], fill=outline)
    # Draw filled rectangle
    draw.rectangle([x0, y0, x1, y1], fill=fill)

    # Apply blur to the whole temp image
    temp = temp.filter(ImageFilter.GaussianBlur(blur_radius))

    # Composite onto base image
    base_img.alpha_composite(temp)

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

    # Use regex to find the mission name in the log file, which is usually in the format: mission="mission_name"
    match = re.search(r'mission="([^"]+)"', data)

    if match:
        mission_name = match.group(1)
        print(f"Mission name found: {mission_name} -> {beautify_mission_name(mission_name)}")
        return mission_name
    else:
        print("Mission name not found.")
        return "No Mission Name Found"


def get_kill_data(file_path=None):
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

    kill_data = {}

    # Find each player and their kill counts using regex
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

        # Print and log the kill counts to a json file for each player
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
        # Search input folder for a .log file and read it in, if there are multiple log files read the most recent one
        log_files = [f for f in os.listdir("input") if f.endswith(".rpt")]
        if not log_files:
            print("No log files found in input folder.")
            return
        latest_log_file = max(log_files, key=lambda f: os.path.getctime(os.path.join("input", f)))
        with open(os.path.join("input", latest_log_file), "r") as f:
            data = f.read()

    # medal_data = {}
    #temporary hardcoded medal data until I can figure out how to parse it from the log files
    medal_data = {
        "Blood Bank": {"medal": "Blood Bank", "name": "HBTurpin [AM 2]", "value": "100", "description": "With 8 bags of blood used", "image_path": "resources/medals/medal_generic.png"},
        "Pincushion": {"medal": "Pincushion", "name": "HBTurpin [AM 2]", "value": "9", "description": "With 9 needle injections", "image_path": "resources/medals/medal_generic.png"},
        "Bullet Magnet": {"medal": "Bullet Magnet", "name": "HBTurpin [AM 2]", "value": "50", "description": "With 50 wounds", "image_path": "resources/medals/medal_generic.png"},
        "Longest Nap": {"medal": "Longest Nap", "name": "HBTurpin [AM 2]", "value": "220", "description": "220 seconds unconscious", "image_path": "resources/medals/medal_generic.png"},
        "Blood Bank2": {"medal": "Blood Bank", "name": "HBTurpin [AM 2]", "value": "100", "description": "With 8 bags of blood used", "image_path": "resources/medals/medal_generic.png"},
        "Pincushion2": {"medal": "Pincushion", "name": "HBTurpin [AM 2]", "value": "9", "description": "With 9 needle injections", "image_path": "resources/medals/medal_generic.png"},
        "Bullet Magnet2": {"medal": "Bullet Magnet", "name": "HBTurpin [AM 2]", "value": "50", "description": "With 50 wounds", "image_path": "resources/medals/medal_generic.png"},
        "Longest Nap2": {"medal": "Longest Nap", "name": "HBTurpin [AM 2]", "value": "220", "description": "220 seconds unconscious", "image_path": "resources/medals/medal_generic.png"},
    }


    return medal_data


def create_image_summary():
    # Load the debriefing template image
    img = Image.open("resources/templates/debriefing_template_medals.png").convert("RGBA")
    img_draw = ImageDraw.Draw(img)

    # Setup fonts
    medium_title_font = ImageFont.truetype("resources/fonts/Purista-Medium.ttf", 16)
    medium_body_font = ImageFont.truetype("resources/fonts/Purista-Medium.ttf", 13)
    small_body_font = ImageFont.truetype("resources/fonts/Purista-Medium.ttf", 10)
    header_number_font = ImageFont.truetype("resources/fonts/Purista-Bold.ttf", 18)
    mission_name_font = ImageFont.truetype("resources/fonts/Purista-Bold.ttf", 13)

    # Setup the mission name at the top
    mission_name = get_mission_name()
    mission_name_beautify = beautify_mission_name(mission_name)
    img_draw.text((img.width // 2, 102), mission_name_beautify.upper(), fill=(255, 255, 255), font=mission_name_font, anchor="mm")

    # Setup most used weapon
    img_draw.text((img.width - 864, 102), "", fill=(255, 255, 255), font=mission_name_font, anchor="mm")
    # Setup medal titles
    img_draw.text((864, 102), "", fill=(255, 255, 255), font=mission_name_font, anchor="mm")

    #####################################

    # Get the total kills and civilian casualties
    kill_data = get_kill_data()
    total_kills = sum(player["killsInfantry"] for player in kill_data.values())
    total_deaths = sum(player["deaths"] for player in kill_data.values())
    civilian_casualties = 0  # Placeholder for civilian casualties

    # Draw the total kills, deaths, and civilian casualties at the top of the image
    img_kills = Image.new('RGBA', img.size, (255, 255, 255, 0))
    img_kills_draw = ImageDraw.Draw(img_kills)
    img_kills_draw.text((372, 132), f"{total_kills}", fill=(255, 255, 255), font=header_number_font, align="right", anchor="rm")
    img_kills_draw.text((563, 132), f"{total_deaths}", fill=(255, 255, 255), font=header_number_font, align="right", anchor="rm")
    img_kills_draw.text((753, 132), f"{civilian_casualties}", fill=(255, 255, 255), font=header_number_font, align="right", anchor="rm")

    # Player stats header
    player_spacing = 62
    img_kills_draw.text((207, 170), "Name", fill=(255, 255, 255), font=medium_title_font, anchor="lm")
    img_kills_draw.text((420 + (player_spacing * 0), 170), "Infantry", fill=(255, 255, 255), font=medium_title_font, anchor="mm")
    img_kills_draw.text((420 + (player_spacing * 1), 170), "Light", fill=(255, 255, 255), font=medium_title_font, anchor="mm")
    img_kills_draw.text((420 + (player_spacing * 2), 170), "Armored", fill=(255, 255, 255), font=medium_title_font, anchor="mm")
    img_kills_draw.text((420 + (player_spacing * 3), 170), "Air", fill=(255, 255, 255), font=medium_title_font, anchor="mm")
    img_kills_draw.text((420 + (player_spacing * 4), 170), "Score", fill=(255, 255, 255), font=medium_title_font, anchor="mm")
    img_kills_draw.text((420 + (player_spacing * 5), 170), "Deaths", fill=(255, 255, 255), font=medium_title_font, anchor="mm")

    # List each player's stats
    for player in kill_data:
        pdata = kill_data[player]
        index = list(kill_data.keys()).index(player)
        if index >= 10:
            break
        y_position = 193 + index * 20
        img_kills_draw.text((207, y_position), pdata["name"], fill=(255, 255, 255), font=medium_body_font, anchor="lm")
        img_kills_draw.text((420 + (player_spacing * 0), y_position), str(pdata["killsInfantry"]), fill=(255, 255, 255), font=medium_body_font, anchor="mm")
        img_kills_draw.text((420 + (player_spacing * 1), y_position), str(pdata["killsSoft"]), fill=(255, 255, 255), font=medium_body_font, anchor="mm")
        img_kills_draw.text((420 + (player_spacing * 2), y_position), str(pdata["killsArmor"]), fill=(255, 255, 255), font=medium_body_font, anchor="mm")
        img_kills_draw.text((420 + (player_spacing * 3), y_position), str(pdata["killsAir"]), fill=(255, 255, 255), font=medium_body_font, anchor="mm")
        img_kills_draw.text((420 + (player_spacing * 4), y_position), str(pdata["score"]), fill=(255, 255, 255), font=medium_body_font, anchor="mm")
        img_kills_draw.text((420 + (player_spacing * 5), y_position), str(pdata["deaths"]), fill=(255, 255, 255), font=medium_body_font, anchor="mm")

    # Composite the kills and medals onto the main image
    img = Image.alpha_composite(img, img_kills)

    #####################################

    # Custom medals
    medal_data = get_medal_data()
    img_medals = Image.new('RGBA', img.size, (0, 0, 0, 0))
    img_medals_draw = ImageDraw.Draw(img_medals)

    def draw_medal_container(image, medal=None, position=(0, 0), size=(178, 72)):
        draw_blurred_rectangle(image, (position[0], position[1], position[0] + size[0], position[1] + size[1]), fill=(0, 0, 0, 170), outline=(0, 0, 0, 40), outline_width=1, blur_radius=0.6)
        draw_blurred_rectangle(image, (position[0] + 6, position[1] + 6, position[0] + size[0] - 6, position[1] + size[1] - 6), fill=(121, 121, 121, 28), outline=(0, 0, 0, 60), outline_width=1, blur_radius=0.6)
        if medal is not None:
            #Draw transparent medal image
            try:
                medal_img = Image.open(medal["image_path"]).convert("RGBA").resize((size[1] - 18, size[1] - 18))
                image.paste(medal_img, (position[0] + (size[0] // 2) - ((size[1] - 18) // 2), position[1] + (size[1] // 2) - ((size[1] - 18) // 2)), medal_img)
            except Exception as e:
                print(f"Error loading medal image: {e}")
            #Draw medal information
            img_medals_draw.text((position[0] + (size[0] // 2), position[1] + (size[1] // 2) - 14), str(medal["medal"]), fill=(255, 255, 255), font=header_number_font, anchor="mm")
            img_medals_draw.text((position[0] + (size[0] // 2), position[1] + (size[1] // 2) + 4), str(medal["name"]), fill=(255, 255, 255), font=medium_body_font, anchor="mm")
            img_medals_draw.text((position[0] + (size[0] // 2), position[1] + (size[1] // 2) + 18), str(medal["description"]), fill=(255, 255, 255, 100), font=small_body_font, anchor="mm")

    for medal in medal_data:
        mdata = medal_data[medal]
        index = list(medal_data.keys()).index(medal)
        if index < 4:
            draw_medal_container(img_medals, medal=mdata, position=(7, 113 + (index * (72 + 4))))
        elif index < 8:
            draw_medal_container(img_medals, medal=mdata, position=(775, 113 + ((index-4) * (72 + 4))))
        else:
            pass

    # Composite the kills and medals onto the main image
    img = Image.alpha_composite(img, img_medals)

    ##############################

    #Save and show the image
    img.save(f'output/{mission_name}.png')
    img.show()

create_image_summary()
