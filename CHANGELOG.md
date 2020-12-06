# Changelog

## 0.5.0

- Added support for rofi 1.6 (handle correctly ROFI_RETV, ROFI_INFO)
- Fix #3 (meta data for menu items was shown on the screen)
- Added `rofi_version` param to the `run` function (it can be `"1.5"` or `"1.6"` -- default)
- Added `debug` param to the `run` function
- Added option to disable accepting user input for menu (`allow_user_input` param)
- Supported nonselectable items and searchable hidden text

By default, the code assumes rofi >= 1.6. If you run under 1.5, you need to pass `rofi_version="1.5"` to the `run` command explicitly.

## 0.4.0

Lots of backward incompatible changes (mostly introduced to fix issues raised here [#2](https://github.com/miphreal/python-rofi-menu/issues/2))

- added ability to store state during rofi session (e.g. to store previously selected menus); added `FileSession` (keeps the state in a `~/.cache/rofi-menu/*.json`)
- changed `def bind()` methods to `async def build()`
- changed props of `meta` object (now it has `raw_script_input`, `selected_id` and `user_input` props)
- introduced new menu methods `propagate_select` and `propagate_user_input`
- added "middlewares" mechanism to enrich "meta" object
