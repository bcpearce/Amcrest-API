"""Storage helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .utils import indexed_dict_to_list


@dataclass(frozen=True, kw_only=True)
class StorageDeviceInfo:
    """Storage device info dataclass."""

    is_error: bool
    path: str
    type: str
    cant_hot_plug: bool
    total_bytes: int
    used_bytes: int
    life_percent: float
    state: str
    sd_encrypt_flag: int
    health_data_flag: int
    name: str

    @staticmethod
    def create_from_response(response: dict[str, Any]) -> list[StorageDeviceInfo]:
        """Create from a PTZ capabilities response."""
        infos: list[dict[str, Any]] = indexed_dict_to_list(response["list"]["info"])

        ret: list[StorageDeviceInfo] = []

        for i, info in enumerate(infos):
            detail = info["Detail"][i]
            ret.append(
                StorageDeviceInfo(
                    is_error=detail["IsError"] == "true",
                    path=detail["Path"],
                    type=detail["Type"],
                    cant_hot_plug=info.get("CantHotPlug", "false") == "true",
                    total_bytes=round(float(detail["TotalBytes"])),
                    used_bytes=round(float(detail["UsedBytes"])),
                    life_percent=float(info["LifePercent"]),
                    state=info["State"],
                    sd_encrypt_flag=int(info["SDEncryptFlag"]),
                    health_data_flag=int(info["HealthDataFlag"]),
                    name=info["Name"],
                )
            )

        return ret
