from collections.abc import AsyncGenerator, Awaitable
from functools import cached_property
from ssl import SSLContext
from typing import Any

import httpx
import yarl

from amcrest_api.config import Config

from . import utils
from .const import ApiEndpoints, StreamType
from .event import EventBase, EventMessageData, EventMessageType, parse_event_message


class Camera:
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
        self._auth = httpx.DigestAuth(username=username, password=password)
        self._scheme = scheme
        self._host = host
        self._port = port
        self._verify = verify
        self._cancel_stream: bool = False

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
    def rtsp_url(self, *, channel: int = 1, subtype: int = StreamType.Main):
        return yarl.URL.build(
            scheme="rtsp",
            user=self._auth._username.decode(),
            password=self._auth._password.decode(),
            host=self._host,
            path=ApiEndpoints.RealtimeStream,
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
            filter_events (list[EventMessageTypes]|None): a list of events to listen to, or None for all capabilities
        """  # noqa: E501
        filter_events_param = (
            f"[{",".join(filter_events or await self.async_supported_events)}]"  # type: ignore[arg-type]
        )

        async with (
            self._create_async_client(timeout=heartbeat_seconds * 2) as client,
            client.stream(
                "GET",
                ApiEndpoints.EventManager,
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
        return (
            await self._async_api_request(
                ApiEndpoints.MagicBox, params={"action": "getSerialNo"}
            )
        )["sn"]

    @property
    async def async_general_config(self):
        return await self._async_api_request(
            ApiEndpoints.ConfigManager,
            params={"action": "getConfig", "name": "General"},
        )

    @property
    async def async_network_config(self):
        return await self._async_api_request(
            ApiEndpoints.ConfigManager,
            params={"action": "getConfig", "name": "Network"},
        )

    @property
    async def async_software_version(self):
        return (
            await self._async_api_request(
                ApiEndpoints.MagicBox, params={"action": "getSoftwareVersion"}
            )
        )["version"]

    @property
    async def async_machine_name(self) -> str:
        return (await self.async_general_config)["General"]["MachineName"]

    @property
    async def async_snap_config(self):
        return await self._async_api_request(
            ApiEndpoints.ConfigManager,
            params={"action": "getConfig", "name": "Snap"},
        )

    @property
    async def async_lighting_config(self):
        return await self._async_api_request(
            ApiEndpoints.ConfigManager,
            params={"action": "getConfig", "name": "Lighting"},
        )

    @property
    async def async_encode_capability(self) -> Awaitable[dict[str, Any]]:
        return await self._async_api_request(
            ApiEndpoints.Encode, params={"action": "getCaps"}
        )

    @property
    async def async_supported_events(self) -> list[EventMessageType]:
        response_content = await self._async_api_request(
            ApiEndpoints.EventManager, params={"action": "getExposureEvents"}
        )
        return list(
            map(
                EventMessageType, utils.indexed_dict_to_list(response_content["events"])
            )
        )

    async def async_ptz_get_preset_information(
        self,
        channel: int = 1,
    ):
        response_content = await self._async_api_request(
            ApiEndpoints.Ptz,
            params={"action": "getPresets", "channel": channel},
        )
        return utils.indexed_dict_to_list(response_content["presets"])

    async def async_ptz_move_to_preset(self, preset_number: int, channel: int = 1):
        return await self._async_api_request(
            ApiEndpoints.Ptz,
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
        await self._async_api_request(
            ApiEndpoints.ConfigManager,
            params={"action": "setConfig", "LeLensMask[0].Enable": on},
        )

    async def async_snapshot(self, channel: int = 1, type: int = 0) -> bytes:
        response: bytes = await self._async_api_request(
            ApiEndpoints.Snapshot, params={"channel": channel, "type": type}
        )
        return response

    def _create_async_client(self, **kwargs):
        return httpx.AsyncClient(
            auth=self._auth,
            base_url=f"{self._scheme}://{self._host}:{self._port}",
            verify=self._verify,
            **kwargs,
        )

    async def _async_api_request(
        self, endpoint, method="GET", params: dict[str, Any] | None = None
    ):
        async with self._create_async_client() as client:
            request: httpx.Request = client.build_request(
                method=method, url=endpoint, params=params
            )
            response: httpx.Response = await client.send(request=request)
        response.raise_for_status()
        return utils.parse_response(response)
