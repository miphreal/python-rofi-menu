# Changelog

## 0.4.0

Lots of backward incompatible changes (mostly introduced to fix issues raised here [#2](https://github.com/miphreal/python-rofi-menu/issues/2))

- added ability to store state during rofi session (e.g. to store previously selected menus); added `FileSession` (keeps the state in a `~/.cache/rofi-menu/*.json`)
- changed `def bind()` methods to `async def build()`
- changed props of `meta` object (now it has `raw_script_input`, `selected_id` and `user_input` props)
- introduced new menu methods `propagate_select` and `propagate_user_input`
- added "middlewares" mechanism to enrich "meta" object
