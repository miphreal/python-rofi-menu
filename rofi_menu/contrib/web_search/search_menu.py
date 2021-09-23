from rofi_menu.menu import Menu, Operation, MetaStore
from rofi_menu.contrib.shell import ShellItem
from urllib.parse import quote_plus
from typing import Type
import sys


class SearchItem(ShellItem):
    search_command: str = ""

    def __init__(self, searchstring: str = "", **kwargs):
        command = self.__class__.search_command.format(searchstring = quote_plus(searchstring))
        super().__init__(text = searchstring, command = command, **kwargs)


class SearchMenu(Menu):
    suggestionItem: Type[SearchItem] = SearchItem
    allow_user_input = True

    async def generate_menu_items(self, meta: MetaStore):
        print("reading suggestions", file = sys.stderr, flush = True)
        suggestions = meta.state_manager.get("suggestion_list", list())
        meta.debug = False
        return [self.__class__.suggestionItem(s) for s in suggestions]

    async def request_suggestions(self, meta: MetaStore):
        return list()

    async def on_user_input(self, meta: MetaStore):
        """request auto complete date from service if available"""
        print("executing on_user_input", file = sys.stderr, flush = True)
        print(meta.user_input, file = sys.stderr)
        if meta.user_input is not None:
            print("fetching suggestions", file = sys.stderr)
            suggestions = await self.request_suggestions(meta)
        else:
            print("no suggestion", file = sys.stderr, flush = True)
            suggestions = list()
        print(suggestions, file = sys.stderr, flush = True)
        if meta.user_input in suggestions:
            suggestions.remove(meta.user_input)
        suggestions.insert(0, meta.user_input)
        meta.state_manager["suggestion_list"] = suggestions
        self.items = await self.build_menu_items(meta)
        print([i.command for i in self.items], file = sys.stderr, flush=True)
        # return Operation.output_menu(await self.handle_render(meta))
        return Operation.refresh_menu()

