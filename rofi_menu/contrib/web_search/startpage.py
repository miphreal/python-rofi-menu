from typing import Optional
from rofi_menu.contrib.web_search.search_menu import SearchMenu, SearchItem
from rofi_menu.main import run
import json
from urllib.parse import urlencode, urlunparse
from urllib.request import urlopen
import ssl

context = ssl.create_default_context()


class StartpageItem(SearchItem):
    search_command = "firefox https://www.startpage.com/do/dsearch?query={searchstring}"


class StartpageMenu(SearchMenu):
    prompt = "StartPage{langEmoji}"
    lang = ""
    langEmoji = ""
    suggestionItem = StartpageItem

    def __init__(self, *args, **kwargs):
        self.prompt = self.__class__.prompt.format(langEmoji= self.__class__.langEmoji)
        super().__init__(*args, **kwargs)

    async def request_suggestions(self, meta):
        query = {"query" : meta.user_input, "limit": "10", "format": "json"}
        if not self.__class__.lang == "":
            query["lang"] = self.__class__.lang
        url = urlunparse(("https", "www.startpage.com", "do/suggest", "", urlencode(query), ""))
        with urlopen(url) as response:
            data = json.loads(response.read().decode())
            return data[1]


class StartpageDEItem(StartpageItem):
    search_command = "firefox https://www.startpage.com/do/dsearch?query={searchstring}&lang=deutsch"


class StartpageDEMenu(StartpageMenu):
    lang= "deutsch"
    langEmoji = u"🇩🇪"
    suggestionItem = StartpageDEItem


class StartpageENItem(StartpageItem):
    search_command = "firefox https://www.startpage.com/do/dsearch?query={searchstring}&lang=english"


class StartpageENMenu(StartpageMenu):
    lang = "english"
    langEmoji = u"🇬🇧"
    suggestionItem = StartpageENItem


def main(lang: Optional[str] = None):
    if lang is not None and lang == "de":
        Menu = StartpageDEMenu
    elif lang is not None and lang == "en":
        Menu = StartpageENMenu
    else:
        Menu = StartpageMenu
    run(Menu())
