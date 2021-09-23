from typing import Optional
from rofi_menu.contrib.web_search.search_menu import SearchMenu, SearchItem
from rofi_menu.main import run
import json
from urllib.parse import urlencode, urlunparse
from urllib.request import urlopen, Request
import sys
import ssl

context = ssl.create_default_context()


class GoogleItem(SearchItem):
    search_command = "firefox https://www.google.com/search?q={searchstring}"


class GoogleMenu(SearchMenu):
    prompt = "Google{langEmoji}"
    lang = ""
    langEmoji = ""
    suggestionItem = GoogleItem

    def __init__(self, *args, **kwargs):
        self.prompt = self.__class__.prompt.format(langEmoji= self.__class__.langEmoji)
        super().__init__(*args, **kwargs)

    async def request_suggestions(self, meta):
        query = {"q": meta.user_input, "output": "firefox", "format": "json", "num": "10"}
        if not self.__class__.lang == "":
            query["hl"] = self.__class__.lang
        url = urlunparse(("https", "suggestqueries.google.com", "complete/search", "", urlencode(query), ""))
        with urlopen(Request(url, headers={"User-Agent": "Mozilla"})) as response:
            #print(bytearray(response.read()), file=sys.stderr, flush=True)
            data = response.read()
            try:
                decode = data.decode("utf-8")
            except UnicodeDecodeError:
                decode = data.decode("iso-8859-1")
            data = json.loads(decode)
            return data[1]


class GoogleDEItem(GoogleItem):
    search_command = "firefox https://www.google.com/search?q={searchstring}&hl=de"


class GoogleDEMenu(GoogleMenu):
    lang= "de"
    langEmoji = u"🇩🇪"
    suggestionItem = GoogleDEItem


class GoogleENItem(GoogleItem):
    search_command = "firefox https://www.google.com/search?q={searchstring}&hl=en"


class GoogleENMenu(GoogleMenu):
    lang = "en"
    langEmoji = u"🇬🇧"
    suggestionItem = GoogleENItem


def main(lang: Optional[str] = None):
    if lang is not None and lang == "de":
        Menu = GoogleDEMenu
    elif lang is not None and lang == "en":
        Menu = GoogleENMenu
    else:
        Menu = GoogleMenu
    run(Menu())
