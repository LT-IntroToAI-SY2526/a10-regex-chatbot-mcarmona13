import re, string, requests, time
from bs4 import BeautifulSoup
from match import match
from typing import List, Callable, Tuple, Any, Match


# ============================================================
# WIKIPEDIA CORE FUNCTIONS (YOUR ORIGINAL CODE)
# ============================================================

def get_page_html(title: str) -> str:
    for attempt in range(5):
        response = requests.get(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "parse",
                "page": title,
                "prop": "text",
                "format": "json",
                "redirects": True,
            },
            headers={"User-Agent": "intro-ai-class/1.0"}
        )

        if response.status_code == 429:
            wait = int(response.headers.get("Retry-After", 5))
            print(f"Rate limited — waiting {wait}s before retrying '{title}'...")
            time.sleep(wait)
            continue

        if response.status_code == 200 and response.text.strip():
            data = response.json()

            if "error" not in data:
                time.sleep(1)
                return data["parse"]["text"]["*"]

    raise ConnectionError(f"Could not retrieve Wikipedia page for '{title}'")


def get_first_infobox_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    results = soup.find_all(class_="infobox")

    if not results:
        raise LookupError("Page has no infobox")

    return results[0].get_text("\n")


def clean_text(text: str) -> str:
    only_ascii = "".join(
        [char if char in string.printable else " " for char in text]
    )

    no_dup_spaces = re.sub(r" +", " ", only_ascii)
    no_dup_newlines = re.sub(r"\n+", "\n", no_dup_spaces)

    return no_dup_newlines.strip()


def get_match(
    text: str,
    pattern: str,
    error_text: str = "Could not find requested information",
) -> Match:

    p = re.compile(pattern, re.DOTALL | re.IGNORECASE)
    result = p.search(text)

    if not result:
        raise AttributeError(error_text)

    return result


# ============================================================
# WIKIPEDIA SUMMARY FUNCTION FOR ADVENTURE MODE
# ============================================================

def get_wiki_summary(name: str) -> str:
    """
    Fetches the first meaningful paragraph from a Wikipedia page.
    """
    try:
        html = get_page_html(name)
        soup = BeautifulSoup(html, "html.parser")

        paragraphs = soup.find_all("p")
        for p in paragraphs:
            text = p.get_text().strip()
            if len(text) > 50:
                return clean_text(text)

        return "No readable summary found."

    except Exception as e:
        return f"Error fetching info: {e}"


# ============================================================
# ADVENTURE MODE FUNCTIONS (UPDATED)
# ============================================================

def start_star_wars_adventure(matches: List[str]) -> List[str]:
    return [
        "You awaken in a Jedi Temple. A hooded figure approaches.",
        "Choose your path:",
        "- JOIN THE JEDI",
        "- JOIN THE SITH",
        "- BECOME A BOUNTY HUNTER"
    ]


def choose_path(matches: List[str]) -> List[str]:
    path = " ".join(matches)
    return [
        f"You chose: {path.upper()}",
        "",
        "Now choose your master.",
        "Type: MASTER <name>",
        "Example: MASTER Yoda, MASTER Anakin Skywalker, MASTER Darth Sidious"
    ]


def choose_master(matches: List[str]) -> List[str]:
    master = " ".join(matches)
    info = get_wiki_summary(master)

    return [
        f"Your master is {master.title()}.",
        "",
        "Information from Wikipedia:",
        info,
        "",
        "Now choose a planet to train on.",
        "Type: PLANET <planet name>"
    ]


def choose_planet(matches: List[str]) -> List[str]:
    planet = " ".join(matches)
    info = get_wiki_summary(planet)

    return [
        f"You travel to {planet.title()} to begin your training.",
        "",
        "Planet information:",
        info,
        "",
        "Now choose someone to fight.",
        "Type: FIGHT <character name>"
    ]


def choose_enemy(matches: List[str]) -> List[str]:
    enemy = " ".join(matches)
    info = get_wiki_summary(enemy)

    return [
        f"You prepare to face {enemy.title()} in battle.",
        "",
        "Enemy information:",
        info,
        "",
        "Now choose your lightsaber color.",
        "Type: COLOR <blue/green/red/purple/yellow>"
    ]


def choose_color(matches: List[str]) -> List[str]:
    color = " ".join(matches).lower()

    descriptions = {
        "blue": "Blue lightsabers are used by Jedi Guardians.",
        "green": "Green lightsabers are used by Jedi Consulars.",
        "red": "Red lightsabers are used by the Sith.",
        "purple": "Purple lightsabers symbolize balance.",
        "yellow": "Yellow lightsabers are used by Temple Guards."
    }

    desc = descriptions.get(color, "A rare and mysterious lightsaber color.")

    return [
        f"You ignite a {color.upper()} lightsaber.",
        desc,
        "",
        "Now choose a starship.",
        "Type: SHIP <ship name>"
    ]


def choose_ship(matches: List[str]) -> List[str]:
    ship = " ".join(matches)
    info = get_wiki_summary(ship)

    return [
        f"You board the {ship.title()}.",
        "",
        "Starship information:",
        info,
        "",
        "Now choose your final mission.",
        "Type: MISSION <rescue/infiltrate/destroy>"
    ]


def choose_mission(matches: List[str]) -> List[str]:
    mission = " ".join(matches).lower()

    endings = {
        "rescue": "You embark on a daring rescue mission to save captured allies.",
        "infiltrate": "You sneak into an enemy base to gather intelligence.",
        "destroy": "You lead an assault to destroy a major enemy stronghold."
    }

    text = endings.get(mission, "You forge your own destiny in the galaxy.")

    return [
        text,
        "",
        "Your Star Wars journey ends... for now."
    ]


# ============================================================
# DIRECT WIKIPEDIA LOOKUP
# ============================================================

def direct_lookup(matches: List[str]) -> List[str]:
    name = " ".join(matches)
    return [get_wiki_summary(name)]


# ============================================================
# PATTERN LIST
# ============================================================

Pattern = List[str]
Action = Callable[[List[str]], List[Any]]

pa_list: List[Tuple[Pattern, Action]] = [

    # Start adventure
    (["start", "star", "wars", "adventure"], start_star_wars_adventure),

    # Choose path
    (["join", "the", "%"], choose_path),
    (["become", "a", "bounty", "hunter"], choose_path),

    # Choose master
    ("master %".split(), choose_master),

    # Choose planet
    ("planet %".split(), choose_planet),

    # Choose enemy
    ("fight %".split(), choose_enemy),

    # Choose lightsaber color
    ("color %".split(), choose_color),

    # Choose ship
    ("ship %".split(), choose_ship),

    # Choose mission
    ("mission %".split(), choose_mission),

    # Direct lookup
    ("who is %".split(), direct_lookup),
    ("tell me about %".split(), direct_lookup),
]


# ============================================================
# MAIN LOOP
# ============================================================

def search_pa_list(src: List[str]) -> List[str]:
    for pat, act in pa_list:
        mat = match(pat, src)
        if mat is not None:
            try:
                return act(mat)
            except Exception as e:
                return [str(e)]
    return ["I don't understand."]


def query_loop() -> None:
    print("Welcome to the Wikipedia-powered Star Wars Adventure Chatbot!\n")

    while True:
        try:
            query = input("\nYour query: ")
            query = query.replace("?", "").lower().split()
            answers = search_pa_list(query)
            for ans in answers:
                print(ans)
        except (KeyboardInterrupt, EOFError):
            break

    print("\nSo long!\n")


query_loop()
