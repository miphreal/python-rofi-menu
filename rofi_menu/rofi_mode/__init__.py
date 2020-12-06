def get_rofi_mode(version: str):
    ver = tuple(int(part) for part in version.split("."))

    if ver < (1, 6):
        from . import rofi_mode_15

        return rofi_mode_15

    if ver >= (1, 6):
        from . import rofi_mode_16

        return rofi_mode_16

    raise RuntimeError("Wrong version configuration")
