"""Utilities to assist testing."""

import json
import os
from pathlib import Path

from httpx import Response


def save_response_as_fixture(
    response: Response,
    fixture_file_name: str,
    *,
    fixture_dir_path: Path = Path("tests/fixtures/mock_responses"),  #
    force: bool = False,
) -> None:
    """
    Saves the response from a live session as a
    JSON fixture file to be used in testing.
    """
    file_path = fixture_dir_path / fixture_file_name
    if os.path.exists(file_path) and not force:
        raise FileExistsError("File already exists, use 'force=True' to overwrite")
    with open(fixture_dir_path / fixture_file_name, "w", encoding="utf-8") as f:
        json.dump(
            {
                "content": response.content.decode(),
                "raw_path": response.url.raw_path.decode(),
            },
            f,
            sort_keys=True,
            indent=2,
        )
