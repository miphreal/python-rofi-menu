from rofi_menu.menu import NestedMenu, Menu
from .shell import ShellItem


class SecondMonitorMenu(Menu):
    prompt = "Second monitor"
    secod_monitor_options = [
        {
            "text": '<span background="green"><b>Off</b></span>',
            "command": "xrandr --output {mon1} --auto --output {mon2} --off",
        },
        {
            "text": '<span background="blue"><b>Mirror</b></span>',
            "command": "xrandr --output {mon1} --auto --output {mon2} --auto --same-as {mon1}",
        },
        {
            "text": '<span background="gray"><b>Above</b></span>',
            "command": "xrandr --output {mon1} --auto --output {mon2} --auto --above {mon1}",
        },
        {
            "text": '<span background="gray"><b>Left</b></span>',
            "command": "xrandr --output {mon1} --auto --output {mon2} --auto --left-of {mon1}",
        },
        {
            "text": '<span background="gray"><b>Right</b></span>',
            "command": "xrandr --output {mon1} --auto --output {mon2} --auto --right-of {mon1}",
        },
        {
            "text": '<span background="gray"><b>Below</b></span>',
            "command": "xrandr --output {mon1} --auto --output {mon2} --auto --below {mon1}",
        },
    ]

    def __init__(
        self,
        prompt="Second monitor",
        primary_monitor="eDP1",
        secondary_monitor="HDMI1",
    ):
        items = [
            ShellItem(
                text=option["text"].format(
                    mon1=primary_monitor, mon2=secondary_monitor
                ),
                command=option["command"].format(
                    mon1=primary_monitor, mon2=secondary_monitor
                ),
            )
            for option in self.secod_monitor_options
        ]
        super().__init__(prompt=prompt, items=items)
