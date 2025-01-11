import asyncio
from enum import Enum
from functools import cached_property
from pprint import pprint

import typer
from rich.console import Console

from amcrest_api import version
from amcrest_api.camera import Camera


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
        console.print(f"[yellow]amcrest-api[/] version: [bold blue]{version}[/]")
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

    async def async_ops():
        async with Camera(host=host, username=username, password=password) as cam:
            print(f"Connecting to {host}")
            pprint(cam.rtsp_url)

            delay = 500
            listen_events = True
            await cam.async_set_privacy_mode_on(True)
            pprint(await cam.async_read_physical_config())
            pprint(await cam.async_network_config)
            pprint(await cam.async_get_privacy_mode_on())
            pprint(await cam.async_ptz_preset_info)
            await cam.async_set_privacy_mode_on(False)
            await asyncio.sleep(2.0)
            if listen_events:
                print("===============")
                print(f"Listening for {delay} seconds")
                print("===============")
                async with asyncio.timeout(delay):
                    async for event in cam.async_listen_events():
                        print(event)
                print("===============")

    asyncio.run(async_ops())


if __name__ == "__main__":
    app()
