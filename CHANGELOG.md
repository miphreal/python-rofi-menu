# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
- Added e2e tests
- Supported debug mode with proper stderr output
- Supported rofi 1.7

## [0.6.0] - 2021-04-23
- Added `contrib/desktop.py` to generate application menu from `*.desktop` files
- Fixed #6: os.getlogin() is not reliable on some platforms (thanks @dnalor for reporting the issue)

## [0.5.1] - 2020-12-06
- Fixed enabling/disabling handling input for nested menus

## [0.5.0] - 2020-12-06
- Added support for rofi 1.6 (handle correctly ROFI_RETV, ROFI_INFO)
- Fix #3 (meta data for menu items was shown on the screen)
- Added `rofi_version` param to the `run` function (it can be `"1.5"` or `"1.6"` -- default)
- Added `debug` param to the `run` function
- Added option to disable accepting user input for menu (`allow_user_input` param)
- Supported nonselectable items and searchable hidden text

By default, the code assumes rofi >= 1.6. If you run under 1.5, you need to pass `rofi_version="1.5"` to the `run` command explicitly.

## [0.4.0] - 2020-08-04
Lots of backward incompatible changes (mostly introduced to fix issues raised here [#2](https://github.com/miphreal/python-rofi-menu/issues/2))

- added ability to store state during rofi session (e.g. to store previously selected menus); added `FileSession` (keeps the state in a `~/.cache/rofi-menu/*.json`)
- changed `def bind()` methods to `async def build()`
- changed props of `meta` object (now it has `raw_script_input`, `selected_id` and `user_input` props)
- introduced new menu methods `propagate_select` and `propagate_user_input`
- added "middlewares" mechanism to enrich "meta" object


[Unreleased]: https://github.com/miphreal/python-rofi-menu/compare/0.6.0...HEAD
[0.6.0]: https://github.com/miphreal/python-rofi-menu/compare/0.5.1...0.6.0
[0.5.1]: https://github.com/miphreal/python-rofi-menu/compare/0.5.0...0.5.1
[0.5.0]: https://github.com/miphreal/python-rofi-menu/compare/0.4.0...0.5.0
[0.4.0]: https://github.com/miphreal/python-rofi-menu/releases/tag/0.4.0
