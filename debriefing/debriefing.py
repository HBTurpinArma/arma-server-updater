import argparse
import re
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import json
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

KILL_SCORE_WEIGHTS = {
    "killsInfantry": 1,
    "killsSoft": 2,
    "killsArmor": 4,
    "killsAir": 6,
    "killsDrones": 2,
}
MAX_DEBRIEF_MEDALS = 10


def calculate_score(player):
    return sum(player[key] * weight for key, weight in KILL_SCORE_WEIGHTS.items())


def resource_path(relative_path):
    return os.path.join(SCRIPT_DIR, relative_path)

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
    data = None
    if file_path is not None:
        if file_path.lower().endswith(".json"):
            with open(file_path, "r", encoding="utf-8-sig") as f:
                mission_data = json.load(f)
            mission_metadata = mission_data.get("_mission") or {}
            mission_name = mission_metadata.get("briefingName") or mission_metadata.get("missionName")
            if mission_name:
                print(f"Mission name found: {mission_name} -> {beautify_mission_name(mission_name)}")
                return mission_name

            log_path = os.path.splitext(file_path)[0] + ".log"
            source_path = log_path if os.path.exists(log_path) else file_path
        else:
            source_path = file_path
        if source_path.lower().endswith(".log"):
            with open(source_path, "r", encoding="utf-8", errors="replace") as f:
                data = f.read()
    else:
        input_dir = os.path.join(SCRIPT_DIR, "input")
        log_files = [f for f in os.listdir(input_dir) if f.endswith(".log")]
        if not log_files:
            print("No log files found in input folder.")
            return "No Mission Name Found"
        latest_log_file = max(log_files, key=lambda f: os.path.getctime(os.path.join(input_dir, f)))
        with open(os.path.join(input_dir, latest_log_file), "r", encoding="utf-8", errors="replace") as f:
            data = f.read()

    if data:
        match = re.search(r'mission="([^"]+)"', data, re.IGNORECASE)
        if not match:
            match = re.search(r'Loaded mission:\s*(\S+)', data, re.IGNORECASE)
        if match:
            mission_name = match.group(1)
            print(f"Mission name found: {mission_name} -> {beautify_mission_name(mission_name)}")
            return mission_name

    print("Mission name not found.")
    return "No Mission Name Found"


def get_json_kill_data(file_path):
    with open(file_path, "r", encoding="utf-8-sig") as f:
        data = json.load(f)

    kill_data = {}
    for player_id, player in data.items():
        if not isinstance(player, dict):
            continue
        combat = player.get("combat", {})
        meta = player.get("meta", {})
        name = meta.get("playerName") or player_id
        if "headlessclient" in str(name).lower():
            continue

        infantry = int(combat.get("killsInfantry", 0) or 0)
        soft = int(combat.get("killsSoft", 0) or 0)
        armor = int(combat.get("killsArmored", 0) or 0)
        air = int(combat.get("killsAir", 0) or 0)
        drones = int(combat.get("killsDrones", 0) or 0)
        player_data = {
            "name": name,
            "killsInfantry": infantry,
            "killsSoft": soft,
            "killsArmor": armor,
            "killsAir": air,
            "killsDrones": drones,
            "killsCivilian": int(combat.get("killsCivilian", 0) or 0),
            "deaths": int(combat.get("deaths", 0) or 0)
        }
        player_data["score"] = calculate_score(player_data)
        kill_data[name] = player_data

    return kill_data


def get_kill_data(file_path=None):
    if file_path is not None and file_path.lower().endswith(".json"):
        return get_json_kill_data(file_path)

    if file_path is not None:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            data = f.read()
    else:
        input_dir = os.path.join(SCRIPT_DIR, "input")
        log_files = [f for f in os.listdir(input_dir) if f.endswith(".log")]
        if not log_files:
            print("No log files found in input folder.")
            return {}
        latest_log_file = max(log_files, key=lambda f: os.path.getctime(os.path.join(input_dir, f)))
        with open(os.path.join(input_dir, latest_log_file), "r", encoding="utf-8", errors="replace") as f:
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
        kills_drones = re.search(r'killsDrones\s*=\s*(\d+);', player_data)
        kills_civilian = re.search(r'killsCivilian\s*=\s*(\d+);', player_data)
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
            "killsDrones": int(kills_drones.group(1)) if kills_drones else 0,
            "killsCivilian": int(kills_civilian.group(1)) if kills_civilian else 0,
            "deaths": int(total_deaths.group(1)) if total_deaths else 0
        }
        player_data["score"] = calculate_score(player_data)

        #Skip headless clients
        if "headlessclient" in name.group(1):
            continue

        kill_data[name.group(1)] = player_data

    return kill_data

def get_medal_data(file_path=None):
    """Calculate in-game and debrief-only medals from the TAW stats export."""
    if file_path is None:
        input_dir = os.path.join(SCRIPT_DIR, "input")
        json_files = [
            os.path.join(input_dir, name)
            for name in os.listdir(input_dir)
            if name.lower().endswith(".json")
        ]
        if not json_files:
            return {}
        file_path = max(json_files, key=os.path.getctime)
    elif file_path.lower().endswith(".log"):
        json_path = os.path.splitext(file_path)[0] + ".json"
        if not os.path.exists(json_path):
            return {}
        file_path = json_path

    if not file_path.lower().endswith(".json"):
        return {}

    with open(file_path, "r", encoding="utf-8-sig") as f:
        player_data = json.load(f)

    players = []
    for player_id, player in player_data.items():
        if not isinstance(player, dict):
            continue
        meta = player.get("meta", {})
        name = meta.get("playerName") or player_id
        if "headlessclient" in str(name).lower():
            continue
        players.append({
            "name": name,
            "combat": player.get("combat") or {},
            "medical": player.get("medical") or {},
        })

    def stat(player, category, key):
        value = player[category].get(key, 0)
        try:
            return float(value or 0)
        except (TypeError, ValueError):
            return 0

    medical_actions = (
        "medicalAEDApplied",
        "medicalBandagesApplied",
        "medicalCPRApplied",
        "medicalInjectionsApplied",
        "medicalMedicationApplied",
        "medicalPAKApplied",
        "medicalSplintApplied",
        "medicalSurgeryApplied",
        "medicalTourniquetsApplied",
    )
    awards = (
        ("Blood Bank", "medical", "medicalBloodApplied", "ml of blood given", 1000, False),
        ("Pincushion", "medical", "medicalInjectionsRecieved", "injections received", 3, False),
        ("Longest Nap", "medical", "unconsciousTime", "seconds unconscious", 240, False),
        ("Frequent Flyer", "medical", "unconsciousCount", "times unconscious", 2, False),
        ("Mummy Impression", "medical", "medicalBandagesRecieved", "bandages received", 30, False),
        ("Trauma Queen/King", "medical_actions", None, "medical actions", 20, False),
        ("Long Shot", "combat", "killsLongest", "meters for longest kill", 300, True),
        ("Drone Hunter", "combat", "killsDrones", "drone kills", 3, False),
        ("Tank Buster", "combat", "killsArmored", "armored kills", 3, False),
        ("Bullet Magnet", "medical", "woundsReceived", "wounds received", 10, True),
        ("Death Wish", "combat", "deaths", "deaths", 2, True),
        ("Vampire", "medical", "medicalBloodDrawnApplied", "ml of blood drawn", 500, True),
        ("Sharpshooter", "combat", "hitHeadshots", "headshots", 5, True),
        ("Trigger Happy", "combat", "firedCount", "shots fired", 100, True),
        ("War Criminal", "combat", "killsCivilian", "civilian kills", 0, True),
        ("Human Colander", "medical", "totalBloodLoss", "ml of blood lost", 2000, True),
    )

    medal_data = {}
    image_path = resource_path("resources/medals/medal_generic.png")
    for medal_name, category, key, description, minimum, strict_minimum in awards:
        if not players or len(medal_data) >= MAX_DEBRIEF_MEDALS:
            break
        if category == "medical_actions":
            value_for = lambda player: sum(
                stat(player, "medical", action) for action in medical_actions
            )
        else:
            value_for = lambda player: stat(player, category, key)
        winner = max(players, key=value_for)
        value = value_for(winner)
        below_minimum = value <= minimum if strict_minimum else value < minimum
        if below_minimum:
            continue
        display_value = int(value) if value.is_integer() else round(value, 2)
        medal_data[medal_name] = {
            "medal": medal_name,
            "name": winner["name"],
            "value": str(display_value),
            "description": f"With {display_value:g} {description}",
            "image_path": image_path,
        }

    return medal_data


def create_image_summary(file_path=None, output_path=None):
    # Load the debriefing template image
    img = Image.open(resource_path("resources/templates/debriefing_template_medals.png")).convert("RGBA")
    img_draw = ImageDraw.Draw(img)

    # Setup fonts
    medium_title_font = ImageFont.truetype(resource_path("resources/fonts/Purista-Medium.ttf"), 16)
    medium_body_font = ImageFont.truetype(resource_path("resources/fonts/Purista-Medium.ttf"), 13)
    small_body_font = ImageFont.truetype(resource_path("resources/fonts/Purista-Medium.ttf"), 10)
    header_number_font = ImageFont.truetype(resource_path("resources/fonts/Purista-Bold.ttf"), 18)
    mission_name_font = ImageFont.truetype(resource_path("resources/fonts/Purista-Bold.ttf"), 13)

    # Setup the mission name at the top
    mission_name = get_mission_name(file_path)
    mission_name_beautify = beautify_mission_name(mission_name)
    img_draw.text((img.width // 2, 102), mission_name_beautify.upper(), fill=(255, 255, 255), font=mission_name_font, anchor="mm")

    # Setup most used weapon
    img_draw.text((img.width - 864, 102), "", fill=(255, 255, 255), font=mission_name_font, anchor="mm")
    # Setup medal titles
    img_draw.text((864, 102), "", fill=(255, 255, 255), font=mission_name_font, anchor="mm")

    #####################################

    # Get the total kills and civilian casualties
    kill_data = get_kill_data(file_path)
    kill_data = dict(sorted(kill_data.items(), key=lambda item: item[1]["score"], reverse=True))
    total_kills = sum(
        player[key] for player in kill_data.values() for key in KILL_SCORE_WEIGHTS
    )
    total_deaths = sum(player["deaths"] for player in kill_data.values())
    civilian_casualties = sum(player["killsCivilian"] for player in kill_data.values())

    # Draw the total kills, deaths, and civilian casualties at the top of the image
    img_kills = Image.new('RGBA', img.size, (255, 255, 255, 0))
    img_kills_draw = ImageDraw.Draw(img_kills)
    img_kills_draw.text((372, 132), f"{total_kills}", fill=(255, 255, 255), font=header_number_font, align="right", anchor="rm")
    img_kills_draw.text((563, 132), f"{total_deaths}", fill=(255, 255, 255), font=header_number_font, align="right", anchor="rm")
    img_kills_draw.text((753, 132), f"{civilian_casualties}", fill=(255, 255, 255), font=header_number_font, align="right", anchor="rm")

    # Player stats header
    player_spacing = 62
    player_stat_x = 420
    img_kills_draw.text((207, 170), "Name", fill=(255, 255, 255), font=medium_title_font, anchor="lm")
    leaderboard_titles = ("Infantry", "Light", "Armor", "Air", "Drones", "Deaths")
    for index, title in enumerate(leaderboard_titles):
        img_kills_draw.text((player_stat_x + (player_spacing * index), 170), title, fill=(255, 255, 255), font=medium_title_font, anchor="mm")

    # List each player's stats
    for index, pdata in enumerate(kill_data.values()):
        if index >= 10:
            break
        y_position = 193 + index * 20
        values = (
            pdata["killsInfantry"],
            pdata["killsSoft"],
            pdata["killsArmor"],
            pdata["killsAir"],
            pdata["killsDrones"],
            pdata["deaths"],
        )
        img_kills_draw.text((207, y_position), pdata["name"], fill=(255, 255, 255), font=medium_body_font, anchor="lm")
        for column, value in enumerate(values):
            img_kills_draw.text((player_stat_x + (player_spacing * column), y_position), str(value), fill=(255, 255, 255), font=medium_body_font, anchor="mm")

    # Composite the kills and medals onto the main image
    img = Image.alpha_composite(img, img_kills)

    #####################################

    # Custom medals
    medal_data = get_medal_data(file_path)
    card_height = 72
    row_step = card_height + 4
    template_rows = 5
    rows_per_column = max(template_rows, (len(medal_data) + 1) // 2)
    if rows_per_column > template_rows:
        extra_height = (rows_per_column - template_rows) * row_step
        canvas = Image.new("RGBA", (img.width, img.height + extra_height), (10, 10, 10, 255))
        canvas.paste(img, (0, 0))
        img = canvas
    img_medals = Image.new('RGBA', img.size, (0, 0, 0, 0))
    img_medals_draw = ImageDraw.Draw(img_medals)

    def draw_medal_container(image, medal=None, position=(0, 0), size=(178, card_height)):
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

    for index, medal in enumerate(medal_data.values()):
        column, row = divmod(index, rows_per_column)
        draw_medal_container(img_medals, medal=medal, position=((7, 775)[column], 113 + row * row_step))

    # Composite the kills and medals onto the main image
    img = Image.alpha_composite(img, img_medals)

    ##############################

    if output_path is None:
        output_dir = os.path.join(SCRIPT_DIR, "output")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{mission_name}.png")
    img.save(output_path)
    print(output_path)
    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate an Arma debriefing leaderboard image")
    parser.add_argument("--input", dest="input_path", help="TAW JSON or legacy debriefing log")
    parser.add_argument("--output", dest="output_path", help="PNG output path")
    args = parser.parse_args()

    input_path = args.input_path
    if input_path is None:
        input_dir = os.path.join(SCRIPT_DIR, "input")
        json_file = next(
            (name for name in sorted(os.listdir(input_dir)) if name.lower().endswith(".json")),
            None,
        )
        if json_file is None:
            parser.error(f"No JSON files found in {input_dir}")
        input_path = os.path.join(input_dir, json_file)

    create_image_summary(input_path, args.output_path)
