import re, string, requests, time
from bs4 import BeautifulSoup
from match import match
from typing import List, Callable, Tuple, Any, Match


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


def get_polar_radius(planet_name: str) -> str:
    infobox_text = clean_text(
        get_first_infobox_text(get_page_html(planet_name))
    )

    pattern = r"(?:Polar radius|Mean radius).*?(?P<radius>[\d,\.]+)\s*km"

    result = get_match(
        infobox_text,
        pattern,
        "Page infobox has no radius information",
    )

    return result.group("radius") + " km"


def get_birth_date(name: str) -> str:
    infobox_text = clean_text(
        get_first_infobox_text(get_page_html(name))
    )

    pattern = r"Born.*?(?P<birth>\d{4}-\d{2}-\d{2})"

    result = get_match(
        infobox_text,
        pattern,
        "Page infobox has no birth information",
    )

    return result.group("birth")


def get_currency(country: str) -> str:
    infobox_text = clean_text(
        get_first_infobox_text(get_page_html(country))
    )

    pattern = r"Currency\s*\n(?P<currency>[^\n]+)"

    result = get_match(
        infobox_text,
        pattern,
        "Page infobox has no currency information",
    )

    return result.group("currency").strip()


def get_date_format(country: str) -> str:
    infobox_text = clean_text(
        get_first_infobox_text(get_page_html(country))
    )

    pattern = r"Date format\s*\n(?P<format>[^\n]+)"

    result = get_match(
        infobox_text,
        pattern,
        "Page infobox has no date format information",
    )

    return result.group("format").strip()


def get_calling_code(country: str) -> str:
    infobox_text = clean_text(
        get_first_infobox_text(get_page_html(country))
    )

    pattern = r"Calling code\s*\n(?P<code>\+[\d\s,\-\(\)]+)"

    result = get_match(
        infobox_text,
        pattern,
        "Page infobox has no calling code information",
    )

    return result.group("code").strip()


# ACTIONS

def birth_date(matches: List[str]) -> List[str]:
    return [get_birth_date(" ".join(matches))]


def polar_radius(matches: List[str]) -> List[str]:
    return [get_polar_radius(" ".join(matches))]


def currency(matches: List[str]) -> List[str]:
    return [get_currency(" ".join(matches))]


def date_format(matches: List[str]) -> List[str]:
    return [get_date_format(" ".join(matches))]


def calling_code(matches: List[str]) -> List[str]:
    return [get_calling_code(" ".join(matches))]


def bye_action(dummy: List[str]) -> None:
    raise KeyboardInterrupt


Pattern = List[str]
Action = Callable[[List[str]], List[Any]]


pa_list: List[Tuple[Pattern, Action]] = [

    ("when was % born".split(), birth_date),

    ("what is the polar radius of %".split(), polar_radius),

    ("what is the currency of %".split(), currency),
    ("what currency does % use".split(), currency),

    ("what is the date format of %".split(), date_format),
    ("what date format does % use".split(), date_format),

    ("what is the calling code of %".split(), calling_code),
    ("what calling code does % use".split(), calling_code),
    ("what is %s calling code".split(), calling_code),

    (["bye"], bye_action),
]


def search_pa_list(src: List[str]) -> List[str]:

    for pat, act in pa_list:
        mat = match(pat, src)

        if mat is not None:
            try:
                answer = act(mat)
                return answer if answer else ["No answers"]

            except Exception as e:
                return [str(e)]

    return ["I don't understand"]


def query_loop() -> None:

    print("Welcome to the wikipedia chatbot!\n")

    while True:
        try:
            print()

            query = input("Your query? ")
            query = query.replace("?", "").lower().split()

            answers = search_pa_list(query)

            for ans in answers:
                print(ans)

        except (KeyboardInterrupt, EOFError):
            break

    print("\nSo long!\n")


query_loop()