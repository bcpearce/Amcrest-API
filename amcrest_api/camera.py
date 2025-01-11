"""Amcrest Camera"""

from collections.abc import AsyncGenerator, Awaitable
from functools import cached_property
from ssl import SSLContext
from typing import Any

import yarl
from httpx import AsyncClient, DigestAuth, Request, Response

from . import utils
from .config import Config
from .const import ApiEndpoints, StreamType
from .data import PtzPresetData
from .event import EventBase, EventMessageData, EventMessageType, parse_event_message


class Camera:
    """Class for an Amcrest camera implementing the API."""

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        *,
        port: int = 80,
        scheme: str = "http",
        verify: bool | SSLContext = True,
    ) -> None:
        self._username = username
        self._password = password
        self._scheme = scheme
        self._host = host
        self._port = port
        self._verify = verify
        self._cancel_stream: bool = False
        self._client: AsyncClient | None = None

    async def async_read_physical_config(self) -> Config:
        """Read a number of properties that should be cached for the API session."""
        config: dict[str, Any] = {}
        config["serial_number"] = await self.async_serial_number
        config["supported_events"] = await self.async_supported_events
        config["machine_name"] = await self.async_machine_name
        config["network"] = (await self.async_network_config)["Network"]
        config["software_version"] = await self.async_software_version
        for _, value in config["network"].items():
            if isinstance(value, dict) and value.get("IPAddress") == self._host:
                config["session_physical_address"] = value["PhysicalAddress"]
        return Config(**config)

    @property
    def rtsp_url(self, *, channel: int = 1, subtype: int = StreamType.MAIN):
        """
        Returns the streaming URL including credentials.
        ***Warning*** this will be in plaintext instead of digest form.
        """
        return yarl.URL.build(
            scheme="rtsp",
            user=self._username,
            password=self._password,
            host=self._host,
            path=ApiEndpoints.REALTIME_STREAM,
            query={"channel": channel, "subtype": subtype},
        )

    async def async_listen_events(
        self,
        *,
        heartbeat_seconds: int = 10,
        filter_events: list[EventMessageType] | None = None,
    ) -> AsyncGenerator[EventBase | None]:
        """
        Asynchronously listen to events.

        Args:
            heartbeat_seconds (int):
                an interval to request heartbeats to keep the connection alive
            filter_events (list[EventMessageTypes]|None):
                a list of events to listen to, or None for all capabilities
        """  # noqa: E501
        filter_events = filter_events or await self.async_supported_events
        filter_events_param = f"[{",".join(filter_events)}]"  # type: ignore[arg-type]

        async with (
            self._create_async_client(timeout=heartbeat_seconds * 2) as client,
            client.stream(
                "GET",
                ApiEndpoints.EVENT_MANAGER,
                params={
                    "action": "attach",
                    "codes": filter_events_param,
                    "heartbeat": heartbeat_seconds,
                },  # noqa: E501
            ) as stream,
        ):
            self._cancel_stream = False
            i = 0
            try:
                async for txt in stream.aiter_text():
                    event_message = EventMessageData(txt)
                    i += 1
                    yield parse_event_message(str(event_message.content))
                    if self._cancel_stream:
                        return
            finally:
                await stream.aclose()

    @cached_property
    async def async_serial_number(self):
        """Get serial number."""
        return (
            await self._async_api_request(
                ApiEndpoints.MAGIC_BOX, params={"action": "getSerialNo"}
            )
        )["sn"]

    @property
    async def async_general_config(self):
        """Get general config."""
        return await self._async_api_request(
            ApiEndpoints.CONFIG_MANAGER,
            params={"action": "getConfig", "name": "General"},
        )

    @property
    async def async_network_config(self):
        """Get network config."""
        return await self._async_api_request(
            ApiEndpoints.CONFIG_MANAGER,
            params={"action": "getConfig", "name": "Network"},
        )

    @property
    async def async_software_version(self):
        """Get software version."""
        return (
            await self._async_api_request(
                ApiEndpoints.MAGIC_BOX, params={"action": "getSoftwareVersion"}
            )
        )["version"]

    @property
    async def async_machine_name(self) -> str:
        """Get machine name."""
        return (await self.async_general_config)["General"]["MachineName"]

    @property
    async def async_snap_config(self):
        """Get snap config."""
        return await self._async_api_request(
            ApiEndpoints.CONFIG_MANAGER,
            params={"action": "getConfig", "name": "Snap"},
        )

    @property
    async def async_lighting_config(self):
        """Get lighting config."""
        return await self._async_api_request(
            ApiEndpoints.CONFIG_MANAGER,
            params={"action": "getConfig", "name": "Lighting"},
        )

    @property
    async def async_encode_capability(self) -> Awaitable[dict[str, Any]]:
        """Get encoding capabilities."""
        return await self._async_api_request(
            ApiEndpoints.ENCODE, params={"action": "getCaps"}
        )

    @property
    async def async_supported_events(self) -> list[EventMessageType]:
        """Get a list of supported events."""
        response_content = await self._async_api_request(
            ApiEndpoints.EVENT_MANAGER, params={"action": "getExposureEvents"}
        )
        return list(
            map(
                EventMessageType, utils.indexed_dict_to_list(response_content["events"])
            )
        )

    @property
    async def async_ptz_preset_info(
        self,
        channel: int = 1,
    ) -> list[PtzPresetData]:
        """Asynchronously get the preset information."""
        response_content = await self._async_api_request(
            ApiEndpoints.PTZ,
            params={"action": "getPresets", "channel": channel},
        )
        return [
            PtzPresetData(index=preset["Index"], name=preset["Name"])
            for preset in utils.indexed_dict_to_list(response_content["presets"])
        ]

    async def async_ptz_move_to_preset(self, preset_number: int, channel: int = 1):
        """Asynchronously move to a preset."""
        return await self._async_api_request(
            ApiEndpoints.PTZ,
            params={
                "action": "start",
                "code": "GotoPreset",
                "channel": channel,
                "arg1": 0,
                "arg2": preset_number,
                "arg3": 0,
            },
        )

    async def async_set_privacy_mode_on(self, on: bool) -> None:
        """Set privacy mode on or off."""
        await self._async_api_request(
            ApiEndpoints.CONFIG_MANAGER,
            params={"action": "setConfig", "LeLensMask[0].Enable": on},
        )

    async def async_get_privacy_mode_on(self) -> bool:
        """Get privacy mode state."""
        response = await self._async_api_request(
            ApiEndpoints.CONFIG_MANAGER,
            params={"action": "getConfig", "name": "LeLensMask"},
        )
        if (enabled := response["LeLensMask"][0]["Enable"].lower()) in [
            "true",
            "false",
        ]:
            return enabled == "true"
        raise ValueError("Unexpected response reading privacy mode status")

    async def async_snapshot(self, channel: int = 1, subtype: int = 0) -> bytes:
        """Get a still frame from the camera."""
        response: bytes = await self._async_api_request(
            ApiEndpoints.SNAPSHOT, params={"channel": channel, "type": subtype}
        )
        return response

    async def aclose_client(self) -> None:
        """
        Close the client.

        Always call this when wrapping up use of the class
        or use the asynchronous context manager.
        """
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    def _create_async_client(self, **kwargs):
        return AsyncClient(
            auth=DigestAuth(self._username, self._password),
            base_url=f"{self._scheme}://{self._host}:{self._port}",
            verify=self._verify,
            **kwargs,
        )

    async def _async_api_request(
        self, endpoint, method="GET", params: dict[str, Any] | None = None
    ):
        # build the client lazily if it does not exist
        self._client = self._client or self._create_async_client()
        request: Request = self._client.build_request(
            method=method, url=endpoint, params=params
        )
        response: Response = await self._client.send(request=request)
        response.raise_for_status()
        return utils.parse_response(response)

    async def __aenter__(self):
        self._client = self._create_async_client()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.aclose_client()
