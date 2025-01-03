from functools import cached_property
from typing import Any

import httpx

from . import utils


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

    def _api_request(
        self, endpoint, method="GET", params: dict[str, Any] | None = None
    ):
        with httpx.Client(
            auth=self._auth,
            base_url=f"{self._schema}://{self._host}",
            headers={"Content-Type": "application/json"},
        ) as client:
            request: httpx.Request = client.build_request(
                method=method, url=endpoint, params=params
            )
            response: httpx.Response = client.send(request=request)
        response.raise_for_status()
        return utils.parse_response(response)

    async def _async_api_request(
        self, endpoint, method="GET", params: dict[str, Any] | None = None
    ):
        async with httpx.AsyncClient(
            auth=self._auth,
            base_url=f"{self._schema}://{self._host}",
            headers={"Content-Type": "application/json"},
        ) as client:
            request: httpx.Request = client.build_request(
                method=method, url=endpoint, params=params
            )
            response: httpx.Response = await client.send(request=request)
        response.raise_for_status()
        return utils.parse_response(response)

    @cached_property
    def serial_number(self):
        return self._api_request(
            "/cgi-bin/magicBox.cgi", params={"action": "getSerialNo"}
        )["sn"]

    @property
    def general_config(self):
        return self._api_request(
            "/cgi-bin/configManager.cgi",
            params={"action": "getConfig", "name": "General"},
        )

    @property
    def snap_config(self):
        return self._api_request(
            "/cgi-bin/configManager.cgi",
            params={"action": "getConfig", "name": "Snap"},
        )

    @property
    def encode_capability(self):
        return self._api_request("/cgi-bin/encode.cgi", params={"action": "getCaps"})

    @cached_property
    def supported_events(self):
        return self._api_request(
            "/cgi-bin/eventManager.cgi", params={"action": "getExposureEvents"}
        )

    def listen_events(self):
        return self._api_request("/cgi-bin/et")

    @property
    async def async_serial_number(self):
        return (
            await self._async_api_request(
                "/cgi-bin/magicBox.cgi", params={"action": "getSerialNo"}
            )
        )["sn"]

    @property
    async def async_snap_config(self):
        return await self._async_api_request(
            "/cgi-bin/configManager.cgi",
            params={"action": "getConfig", "name": "Snap"},
        )

    @property
    async def async_encode_capability(self):
        return await self._async_api_request(
            "/cgi-bin/encode.cgi", params={"action": "getCaps"}
        )
