import json
import urllib.request
import urllib.error

from urllib.parse import urlsplit

from bs4 import BeautifulSoup

REQUEST_TIMEOUT = 15

USER_AGENT = (
    "Mozilla/5.0 (compatible; LoreLinker/1.0; "
    "+https://universe.leagueoflegends.com/)"
)

def validate_story_url(url):
    if not url:
        return False

    try:
        parsed_url = urlsplit(url.strip())

    except ValueError:
        return False

    if parsed_url.scheme != "https":
        return False

    if parsed_url.hostname != "universe.leagueoflegends.com":
        return False

    if parsed_url.username or parsed_url.password:
        return False

    return True

def fetch_story_json(url):
    if not validate_story_url(url):
        raise ValueError("Invalid Riot Universe URL.")

    parsed_url = urlsplit(url.strip())

    path_parts = [
        part for part in parsed_url.path.split("/")
        if part
    ]

    if (
        len(path_parts) != 4
        or path_parts[1] != "story"
        or path_parts[2] != "champion"
    ):
        raise ValueError("Invalid Riot Universe story URL.")

    locale = path_parts[0].lower()
    story_id = path_parts[3]

    if not story_id:
        raise ValueError("Invalid Riot Universe story URL.")

    api_url = (
        "https://universe-meeps.leagueoflegends.com/"
        f"v1/{locale}/story/{story_id}/index.json"
    )

    request = urllib.request.Request(
        api_url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=REQUEST_TIMEOUT,
        ) as response:
            if response.status != 200:
                raise RuntimeError(
                    f"HTTP error: {response.status}"
                )

            data = json.loads(
                response.read().decode("utf-8")
            )

            return data

    except urllib.error.HTTPError as error:
        raise RuntimeError(
            f"HTTP request failed: {error.code}"
        ) from error

    except urllib.error.URLError as error:
        raise RuntimeError(
            f"Connection failed: {error.reason}"
        ) from error

    except TimeoutError as error:
        raise RuntimeError(
            "The request timed out."
        ) from error

    except json.JSONDecodeError as error:
        raise RuntimeError(
            "The server returned invalid JSON."
        ) from error

def extract_champion_biographies(data):
    biographies = []

    sections = data.get("story", {}).get(
        "story-sections", []
    )

    for section in sections:
        champions = section.get(
            "featured-champions", []
        )

        for champion in champions:
            champion_name = champion.get("name")

            if not isinstance(champion_name, str) or not champion_name.strip():
                continue

            biography = champion.get("biography") or {}
            full = biography.get("full", "")

            if not full:
                continue

            soup = BeautifulSoup(full, "html.parser")

            paragraphs = [
                paragraph.get_text(" ", strip=True)
                for paragraph in soup.find_all("p")
                if paragraph.get_text(" ", strip=True)
            ]

            if not paragraphs:
                continue

            biographies.append({
                "champion_name": champion_name.strip(),
                "body": "\n\n".join(paragraphs),
            })

    return biographies

def extract_story_title_from_json(data):
    title = data.get("story", {}).get("title")

    if isinstance(title, str) and title.strip():
        return title.strip()

    return None
