"""Utilities."""

import re
from typing import Any

import httpx


def parse_response(response: httpx.Response) -> bytes | dict:
    content_type: str = response.headers["content-type"]
    if "image/jpeg" in content_type:
        return response.content
    elif "text/plain" in content_type:
        return parse_key_value_response(response)
    elif "application/json" in content_type:
        return response.json()
    raise ValueError(f"Response does not contain supported content: {content_type}")


def parse_key_value_response(response: httpx.Response) -> dict[int | str, Any]:
    ret: dict[int | str, Any] = {}
    # The API can simply reply with OK too
    if response.text.strip() == "OK":
        return ret
    for line in response.iter_lines():
        keystr, val = line.split("=")
        keysraw = keystr.split(".")
        if keysraw[0] == "table":
            keysraw = keysraw[1:]
        keys: list[list[int | str]] = []
        for keyraw in keysraw:
            mainkey = keyraw.split("[")[0]  # get the key without indices
            indices = [int(x) for x in re.findall(r"\[(\d+)\]", keyraw)]
            keys.append([mainkey] + indices)
        # flatten the keys
        keysflat: list[int | str] = [x for xx in keys for x in xx]
        current = ret
        for keyflat in keysflat[:-1]:
            current = current.setdefault(keyflat, {})
        current[keysflat[-1]] = val

    return ret


def indexed_dict_to_list(indexed_dict: dict[int, Any]) -> list[Any]:
    """Converts a dict that could be a list, into a list."""
    return [indexed_dict[i] for i, key in enumerate(sorted(indexed_dict.keys()))]
