from typing import Optional
from rofi_menu.contrib.web_search.search_menu import SearchMenu, SearchItem
from rofi_menu.main import run
import json
from urllib.parse import urlencode, urlunparse
from urllib.request import urlopen
import ssl

context = ssl.create_default_context()


class EcosiaItem(SearchItem):
    search_command = "firefox https://www.ecosia.org/search?q={searchstring}"


class EcosiaMenu(SearchMenu):
    prompt = "Ecosia{langEmoji}"
    lang = ""
    langEmoji = ""
    suggestionItem = EcosiaItem

    def __init__(self, *args, **kwargs):
        self.prompt = self.__class__.prompt.format(langEmoji= self.__class__.langEmoji)
        super().__init__(*args, **kwargs)

    async def request_suggestions(self, meta):
        query = {"q" : meta.user_input}
        if not self.__class__.lang == "":
            query["mkt"] = self.__class__.lang
        url = urlunparse(("https", "ac.ecosia.org", "", "", urlencode(query), ""))
        with urlopen(url) as response:
            data = json.loads(response.read().decode())
            return data["suggestions"]


def main(lang: Optional[str] = None):
    Menu = EcosiaMenu
    run(Menu())
