import asyncio
from enum import Enum
from pprint import pprint

import httpx
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
    cam = Camera(host=host, username=username, password=password)
    try:
        pprint("Testing Sync Methods")
        pprint(cam.general_config)
        pprint(cam.serial_number)
        pprint(cam.snap_config)
        pprint(cam.encode_capability)
        pprint(cam.supported_events)
        print("Testing Async Methods")

        async def async_props():
            pprint(await cam.async_serial_number)
            pprint(await cam.async_snap_config)
            pprint(await cam.async_encode_capability)

        asyncio.run(async_props())
    except httpx.HTTPStatusError as e:
        print(
            f"Error response {e.response.status_code} while requesting {e.request.url}"  # noqa: E501
        )


if __name__ == "__main__":
    app()
