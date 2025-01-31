"""Main"""

import asyncio
from enum import Enum
from functools import cached_property
from pprint import pprint

import typer
from rich.console import Console
from sshkeyboard import listen_keyboard

from . import version
from .camera import Camera
from .ptz import PtzPresetData, PtzRelativeMove


class Color(str, Enum):
    white = "white"
    red = "red"
    cyan = "cyan"
    magenta = "magenta"
    yellow = "yellow"
    green = "green"


app = typer.Typer(
    name="amcrest-api",
    help="API Wrapper for Amcrest V3.26",
    add_completion=False,
)
console = Console()

POSSIBLE_ACTIONS = [
    attr
    for attr, value in vars(Camera).items()
    if isinstance(value, (cached_property, property))
]


def version_callback(print_version: bool) -> None:
    """Print the version of the package."""
    if print_version:
        print(version)
        raise typer.Exit()


@app.command(name="")
def main(
    print_version: bool = typer.Option(
        None,
        "-v",
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Prints the version of the amcrest-api package.",
    ),
    username: str = typer.Option(
        ...,
        "-u",
        "--username",
        envvar="AMC_USERNAME",
        case_sensitive=True,
        help="User name for Amcrest Camera",
    ),
    password: str = typer.Option(
        ...,
        "-p",
        "--password",
        envvar="AMC_PASSWORD",
        case_sensitive=True,
        help="Password for Amcrest Camera",
    ),
    host: str = typer.Option(
        ...,
        "-h",
        "--host",
        envvar="AMC_HOST",
        case_sensitive=False,
        help="Host name or IP Address for Amcrest Camera",
    ),
) -> None:
    """Print a greeting with a giving name."""

    cam = Camera(host=host, username=username, password=password)

    async def print_config(cam: Camera):
        pprint(await cam.async_get_fixed_config())

    asyncio.run(print_config(cam))

    print("Listening for keypresses...")

    async def on_press(key):
        try:
            if key == "up":
                await cam.async_ptz_move_relative(PtzRelativeMove(vertical=0.1))
            elif key == "down":
                await cam.async_ptz_move_relative(PtzRelativeMove(vertical=-0.1))
            elif key == "left":
                await cam.async_ptz_move_relative(PtzRelativeMove(horizontal=-0.05))
            elif key == "right":
                await cam.async_ptz_move_relative(PtzRelativeMove(horizontal=0.05))

            SET_PRESET_MAP = {
                "!": "1",
                "@": "2",
                "#": "3",
                "$": "4",
                "%": "5",
                "^": "6",
                "&": "7",
                "*": "8",
            }
            if key in SET_PRESET_MAP.values():
                await cam.async_ptz_move_to_preset(int(key))

            if key in SET_PRESET_MAP:
                preset = PtzPresetData(
                    SET_PRESET_MAP[key], f"MyCustomPreset{SET_PRESET_MAP[key]}"
                )
                await cam.async_set_ptz_preset(preset)
                print(f"saved prest: {preset}")

            if key in "x":
                for preset in await cam.async_ptz_preset_info:
                    await cam.async_clear_ptz_preset(preset)
                    print(f"cleared preset: {preset}")

            if key == "r":
                pprint(await cam.async_ptz_preset_info)

            if key == "space":
                pm = await cam.async_get_privacy_mode_on()
                await cam.async_set_privacy_mode_on(not pm)

            if key == "l":
                lights = await cam.async_lighting_config
                pprint(lights)

            if key == "c":
                pprint(await cam.async_get_fixed_config())

            if key == "#":
                pprint(f"Extra Streams: {await cam.async_max_extra_stream}")

            if key == "m":
                try:
                    async for event in cam.async_listen_events():
                        print(event)
                except KeyboardInterrupt:
                    pass
        except Exception as e:
            print(e)

    listen_keyboard(on_press=on_press)


if __name__ == "__main__":
    app()
