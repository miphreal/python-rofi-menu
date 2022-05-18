from typing import Optional
from rofi_menu.contrib.web_search.search_menu import SearchMenu, SearchItem
from rofi_menu.main import run
import json
from urllib.parse import urlencode, urlunparse
from urllib.request import urlopen
import ssl

context = ssl.create_default_context()


class WikipediaItem(SearchItem):
    search_command = "firefox https://wikipedia.org/wiki/{searchstring}"


class WikipediaMenu(SearchMenu):
    prompt = "Wikipedia{langEmoji}"
    sub = ""
    langEmoji = ""
    suggestionItem = WikipediaItem

    def __init__(self, *args, **kwargs):
        self.prompt = self.__class__.prompt.format(langEmoji= self.__class__.langEmoji)
        super().__init__(*args, **kwargs)

    async def request_suggestions(self, meta):
        query = {"search": meta.user_input, "limit": "10", "format": "json", "namespace": "0", "formatversion": "2", "action": "opensearch"}
        url = urlunparse(("https", f"{self.__class__.sub}wikipedia.org", "w/api.php", "", urlencode(query), ""))
        with urlopen(url) as response:
            data = json.loads(response.read().decode())
            return [s.replace(" ", "_") for s in data[1]]


class WikipediaDEItem(WikipediaItem):
    search_command = "firefox https://de.wikipedia.org/wiki/{searchstring}"


class WikipediaDEMenu(WikipediaMenu):
    sub = "de."
    langEmoji = u"🇩🇪"
    suggestionItem = WikipediaDEItem


class WikipediaENItem(WikipediaItem):
    search_command = "firefox https://en.wikipedia.org/wiki/{searchstring}"


class WikipediaENMenu(WikipediaMenu):
    sub = "en."
    langEmoji = u"🇬🇧"
    suggestionItem = WikipediaENItem


def main(lang: Optional[str] = None):
    if lang is not None and lang == "de":
        Menu = WikipediaDEMenu
    elif lang is not None and lang == "en":
        Menu = WikipediaENMenu
    else:
        Menu = WikipediaMenu
    run(Menu())
