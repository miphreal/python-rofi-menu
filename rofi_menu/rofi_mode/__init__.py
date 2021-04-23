from .rofi_mode import RofiMode


def get_rofi_mode(version: str) -> RofiMode:
    ver = tuple(int(part) for part in version.split("."))

    if ver < (1, 6):
        from . import rofi_mode_15

        return rofi_mode_15.RofiMode()

    if ver >= (1, 6):
        from . import rofi_mode_16

        return rofi_mode_16.RofiMode()

    raise RuntimeError("Wrong version configuration")
