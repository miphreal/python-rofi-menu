from typing import Optional
from rofi_menu.contrib.web_search.search_menu import SearchMenu, SearchItem
from rofi_menu.main import run
import json
from urllib.parse import urlencode, urlunparse
from urllib.request import urlopen, Request
import sys
import ssl
import re
context = ssl.create_default_context()


class YoutubeItem(SearchItem):
    search_command = "firefox https://www.youtube.com/results?search_query={searchstring}&search_type=&aq=f"


class YoutubeMenu(SearchMenu):
    prompt = "YouTube{langEmoji}"
    lang = ""
    langEmoji = ""
    suggestionItem = YoutubeItem

    def __init__(self, *args, **kwargs):
        self.prompt = self.__class__.prompt.format(langEmoji= self.__class__.langEmoji)
        super().__init__(*args, **kwargs)

    async def request_suggestions(self, meta):
        query = {"q": meta.user_input, "client": "youtube", "num": "10"}
        if not self.__class__.lang == "":
            query["hl"] = self.__class__.lang
        url = urlunparse(("https", "clients1.google.com", "complete/search", "", urlencode(query), ""))
        with urlopen(Request(url, headers={"User-Agent": "Mozilla"})) as response:
            #print(bytearray(response.read()), file=sys.stderr, flush=True)
            data = response.read()
            try:
                decode = data.decode("utf-8")
            except UnicodeDecodeError:
                decode = data.decode("iso-8859-1")
            data = json.loads(re.match(r".*\((.*)\)", decode).group(1))[1]
            return [s[0] for s in data]


"""choosing a language seems useless, because cookies overwrite the settings from the url"""
class YoutubeDEItem(YoutubeItem):
    search_command = "firefox https://www.youtube.com/results?search_query={searchstring}&search_type=&aq=f&hl=de"


class YoutubeDEMenu(YoutubeMenu):
    lang= "de"
    langEmoji = u"🇩🇪"
    suggestionItem = YoutubeDEItem


class YoutubeENItem(YoutubeItem):
    search_command = "firefox https://www.youtube.com/results?search_query={searchstring}&search_type=&aq=f&hl=en"


class YoutubeENMenu(YoutubeMenu):
    lang = "en"
    langEmoji = u"🇬🇧"
    suggestionItem = YoutubeENItem


def main(lang: Optional[str] = None):
    if lang is not None and lang == "de":
        Menu = YoutubeDEMenu
    elif lang is not None and lang == "en":
        Menu = YoutubeENMenu
    else:
        Menu = YoutubeMenu
    run(Menu())
