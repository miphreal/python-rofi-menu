from typing import Optional
from rofi_menu.contrib.web_search.search_menu import SearchMenu, SearchItem
from rofi_menu.main import run
import json
from urllib.parse import urlencode, urlunparse
from urllib.request import urlopen
import ssl

context = ssl.create_default_context()


class WolframItem(SearchItem):
    search_command = "firefox https://www.wolframalpha.com/input?i={searchstring}"


class WolframMenu(SearchMenu):
    prompt = "wolfram|α"
    suggestionItem = WolframItem

    async def request_suggestions(self, meta):
        query = {"i": meta.user_input}
        url = urlunparse(("https", "www.wolframalpha.com", "n/v1/api/autocomplete/", "", urlencode(query), ""))
        with urlopen(url) as response:
            data = json.loads(response.read().decode())
            return [d["input"] for d in data["results"]]


def main(lang: Optional[str] = None):
    Menu = WolframMenu
    run(Menu())
