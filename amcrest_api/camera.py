from collections.abc import Iterable
from functools import cached_property
from typing import Any

import httpx

from . import utils
from .const import ApiEndpoints, EventMessageTypes


class Camera:
    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        port: int = 80,
        schema: str = "http",
    ) -> None:
        self._auth = httpx.DigestAuth(username=username, password=password)
        self._schema = schema
        self._host = host

    def _create_client(self):
        return httpx.Client(
            auth=self._auth,
            base_url=f"{self._schema}://{self._host}",
            headers={"Content-Type": "application/json"},
        )

    def _api_request(
        self, endpoint, method="GET", params: dict[str, Any] | None = None
    ):
        with self._create_client() as client:
            request: httpx.Request = client.build_request(
                method=method, url=endpoint, params=params
            )
            response: httpx.Response = client.send(request=request)
        response.raise_for_status()
        return utils.parse_response(response)

    def _create_async_client(self):
        return httpx.AsyncClient(
            auth=self._auth,
            base_url=f"{self._schema}://{self._host}",
            headers={"Content-Type": "application/json"},
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

    @cached_property
    def serial_number(self):
        return self._api_request(
            ApiEndpoints.MagicBox, params={"action": "getSerialNo"}
        )["sn"]

    @property
    def general_config(self):
        return self._api_request(
            ApiEndpoints.ConfigManager,
            params={"action": "getConfig", "name": "General"},
        )

    @property
    def snap_config(self):
        return self._api_request(
            ApiEndpoints.ConfigManager,
            params={"action": "getConfig", "name": "Snap"},
        )

    @property
    def lighting_config(self):
        return self._api_request(
            ApiEndpoints.ConfigManager,
            params={"action": "getConfig", "name": "Lighting"},
        )

    @property
    def encode_capability(self):
        return self._api_request("/cgi-bin/encode.cgi", params={"action": "getCaps"})

    @cached_property
    def supported_events(self):
        return self._api_request(
            ApiEndpoints.EventManager, params={"action": "getExposureEvents"}
        )

    async def async_listen_events(
        self, filter_events: Iterable[EventMessageTypes] | None = None
    ):
        """
        Asynchronously listen to events.

        Args:
            filter_events (list[EventMessageTypes]|None): a list of events to listen to, or None for all capabilities
        """  # noqa: E501
        if filter_events is None:
            filter_events = utils.indexed_dict_to_list(
                (await self.async_supported_events)["events"]
            )
        filter_events_param = f"[{",".join(filter_events)}]"
        async with self._create_async_client() as client, client.stream(
            "GET",
            ApiEndpoints.EventManager,
            params={"action": "attach", "codes": filter_events_param, "heartbeat": 2},
        ) as stream:
            i = 1
            async for txt in stream.aiter_raw():
                # TODO test and make usable in HASS
                print(f"Received {i} async message(s).")
                print(txt)
                i += 1

    @cached_property
    async def async_serial_number(self):
        if self.serial_number:
            return self.serial_number
        return (
            await self._async_api_request(
                ApiEndpoints.MagicBox, params={"action": "getSerialNo"}
            )
        )["sn"]

    @property
    async def async_snap_config(self):
        return await self._async_api_request(
            ApiEndpoints.ConfigManager,
            params={"action": "getConfig", "name": "Snap"},
        )

    @property
    async def async_lighting_config(self):
        return self._async_api_request(
            ApiEndpoints.ConfigManager,
            params={"action": "getConfig", "name": "Lighting"},
        )

    @property
    async def async_encode_capability(self):
        return await self._async_api_request(
            ApiEndpoints.Encode, params={"action": "getCaps"}
        )

    @cached_property
    async def async_supported_events(self):
        return self._api_request(
            ApiEndpoints.EventManager, params={"action": "getExposureEvents"}
        )
