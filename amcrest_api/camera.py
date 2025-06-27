"""Amcrest Camera"""

import asyncio
from collections.abc import (  # pylint: disable=import-error
    AsyncGenerator,
    Awaitable,
)
from datetime import datetime, timedelta
from ssl import SSLContext
from typing import Any

from httpx import AsyncClient, DigestAuth, Request, Response
from yarl import URL

from amcrest_api.error import UnsupportedStreamSubtype

from . import utils
from .config import Config
from .const import STREAM_TYPE_DICT, ApiEndpoints, StreamType
from .event import EventBase, EventMessageData, EventMessageType, parse_event_message
from .imaging import ConfigNo, Lighting, VideoDayNight, VideoImageControl
from .ptz import (
    PtzAccuratePosition,
    PtzBasicMove,
    PtzCapabilityData,
    PtzPresetData,
    PtzRelativeMove,
    PtzStatusData,
)
from .storage import StorageDeviceInfo


class Camera:
    """Class for an Amcrest camera implementing the API."""

    _ptz_capabilities: PtzCapabilityData | None = None
    _client: AsyncClient | None = None
    _fixed_config: Config | None = None

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

    async def async_get_fixed_config(self) -> Config:
        """Read a number of properties that should be cached for the API session."""
        if self._fixed_config is None:
            config: dict[str, Any] = {}
            config["device_type"] = await self.async_device_type
            config["hardware_version"] = await self.async_hardware_version
            config["machine_name"] = await self.async_machine_name
            config["max_extra_stream"] = await self.async_max_extra_stream
            config["network"] = (await self.async_network_config)["Network"]
            config["ptz_capabilities"] = await self.async_ptz_capabilities
            config["serial_number"] = await self.async_serial_number
            config["software_version"] = await self.async_software_version
            config["supported_events"] = await self.async_supported_events
            config["supported_streams"] = {
                k: v
                for k, v in STREAM_TYPE_DICT.items()
                if k <= config["max_extra_stream"]
            }
            for _, value in config["network"].items():
                if isinstance(value, dict) and value.get("IPAddress") == self._host:
                    config["session_physical_address"] = value["PhysicalAddress"]
            self._fixed_config = Config(**config)
        return self._fixed_config

    @property
    def url(self) -> URL:
        """Provide the URL for accessing the web interface."""
        return URL.build(scheme=self._scheme, host=self._host, port=self._port)

    async def async_get_rtsp_url(
        self, *, channel: int = 1, subtype: int = StreamType.MAIN
    ) -> URL | None:
        """
        Returns the streaming URL including credentials.
        ***Warning*** this will be in plaintext instead of digest form.
        This is not cached as the RTSP port can be reconfigured during a session.
        """
        if subtype > (
            max_subtream := (await self.async_get_fixed_config()).max_extra_stream
        ):
            raise UnsupportedStreamSubtype(
                f"Camera does not support substream {subtype}, \
                max substream is {max_subtream}"
            )
        rtsp_conf: dict = (
            await self._async_api_request(
                ApiEndpoints.CONFIG_MANAGER,
                params={"action": "getConfig", "name": "RTSP"},
            )
        )["RTSP"]
        if rtsp_conf["Enable"] == "false":
            return None
        return URL.build(
            scheme="rtsp",
            user=self._username,
            password=self._password,
            host=self._host,
            port=int(rtsp_conf["Port"]),
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
        """
        filter_events = filter_events or await self.async_supported_events
        filter_events_param = f"[{','.join(filter_events)}]"  # type: ignore[arg-type]

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
            i = 0
            try:
                async for txt in stream.aiter_text():
                    event_message = EventMessageData(txt)
                    i += 1
                    yield parse_event_message(str(event_message.content))
            finally:
                await stream.aclose()

    @property
    async def async_serial_number(self):
        """Get serial number."""
        return (
            await self._async_api_request(
                ApiEndpoints.MAGIC_BOX, params={"action": "getSerialNo"}
            )
        )["sn"]

    @property
    async def async_device_type(self):
        """Get device type/model name."""
        return (
            await self._async_api_request(
                ApiEndpoints.MAGIC_BOX, params={"action": "getDeviceType"}
            )
        )["type"]

    @property
    async def async_hardware_version(self):
        """Get hardware version."""
        return (
            await self._async_api_request(
                ApiEndpoints.MAGIC_BOX, params={"action": "getHardwareVersion"}
            )
        )["version"]

    @property
    async def async_max_extra_stream(self):
        """Get max extra streams."""
        return int(
            (
                await self._async_api_request(
                    ApiEndpoints.MAGIC_BOX,
                    params={"action": "getProductDefinition", "name": "MaxExtraStream"},
                )
            )["MaxExtraStream"]
        )

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
    async def async_lighting_config(self) -> list[list[list[Lighting]]]:
        """Get lighting config."""
        return Lighting.create_from_response(
            await self._async_api_request(
                ApiEndpoints.CONFIG_MANAGER,
                params={"action": "getConfig", "name": "Lighting_V2"},
            )
        )

    async def async_set_lighting_config(
        self, config_no, light: Lighting, index: int = 0, channel: int = 1
    ) -> None:
        """Set lighting config."""
        params: dict[str, Any] = {"action": "setConfig"}
        if light.middle_light:
            params[
                f"Lighting_V2[{channel - 1}][{config_no}][{index}].MiddleLight[0].Light"
            ] = light.middle_light.light
            params[
                f"Lighting_V2[{channel - 1}][{config_no}][{index}].MiddleLight[0].Angle"
            ] = light.middle_light.angle
        if light.correction:
            params[f"Lighting_V2[{channel - 1}][{config_no}][{index}].Correction"] = (
                light.correction
            )
        if light.mode:
            params[f"Lighting_V2[{channel - 1}][{config_no}][{index}].Mode"] = (
                light.mode
            )
        if light.sensitivity:
            params[f"Lighting_V2[{channel - 1}][{config_no}][{index}].Sensitive"] = (
                light.sensitivity
            )
        await self._async_api_request(ApiEndpoints.CONFIG_MANAGER, params=params)

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

    async def async_set_ptz_preset(
        self, preset: PtzPresetData, channel: int = 1
    ) -> None:
        """Asynchronously save the current position as a preset."""
        await self._async_api_request(
            ApiEndpoints.PTZ,
            params={
                "action": "start",
                "code": "SetPreset",
                "channel": channel,
                "arg1": 0,
                "arg2": preset.index,
                "arg3": 0,
            },
        )
        await self._async_api_request(
            ApiEndpoints.PTZ,
            params={
                "action": "setPreset",
                "channel": channel,
                "arg1": preset.index,
                "arg2": preset.name,
            },
        )

    async def async_clear_ptz_preset(
        self, preset: PtzPresetData | int, channel: int = 1
    ) -> None:
        """Asynchronously delete a preset."""
        index = preset.index if isinstance(preset, PtzPresetData) else preset
        await self._async_api_request(
            ApiEndpoints.PTZ,
            params={
                "action": "start",
                "code": "ClearPreset",
                "channel": channel,
                "arg1": 0,
                "arg2": index,
                "arg3": 0,
            },
        )

    async def async_ptz_move_to_preset(
        self, preset_number: int, channel: int = 1
    ) -> None:
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

    async def async_ptz_move_relative(self, relative_move: PtzRelativeMove) -> None:
        """Move the PTZ control relatively."""
        if relative_move.caps is None:
            relative_move.caps = await self.async_ptz_capabilities
        await self._async_api_request(
            ApiEndpoints.PTZ, params=relative_move.get_query_dict()
        )

    async def async_ptz_move_absolute(self, absolute_move: PtzAccuratePosition) -> None:
        """Move the PTZ control to absolute position."""
        if absolute_move.caps is None:
            absolute_move.caps = await self.async_ptz_capabilities
        await self._async_api_request(
            ApiEndpoints.PTZ, params=absolute_move.get_query_dict()
        )

    async def async_ptz_move(
        self, continuous_move: PtzBasicMove, delay_till_stop: timedelta | None = None
    ) -> None:
        """Begin PTZ Move."""
        if continuous_move.caps is None:
            continuous_move.caps = await self.async_ptz_capabilities
        await self._async_api_request(
            ApiEndpoints.PTZ, params=continuous_move.get_start_query_dict()
        )
        if delay_till_stop is not None:
            await asyncio.sleep(delay_till_stop.total_seconds())
            await self.async_ptz_stop(continuous_move)

    async def async_ptz_stop(self, continuous_move: PtzBasicMove) -> None:
        """Stop PTZ Move."""
        if continuous_move.caps is None:
            continuous_move.caps = await self.async_ptz_capabilities
        await self._async_api_request(
            ApiEndpoints.PTZ, params=continuous_move.get_stop_query_dict()
        )

    @property
    async def async_ptz_capabilities(self, channel: int = 1) -> PtzCapabilityData:
        """Get PTZ capabilities."""
        self._ptz_capabilities = (
            self._ptz_capabilities
            or PtzCapabilityData.create_from_response(
                await self._async_api_request(
                    ApiEndpoints.PTZ,
                    params={"action": "getCurrentProtocolCaps", "channel": channel},
                )
            )
        )
        return self._ptz_capabilities

    @property
    async def async_ptz_status(self, channel: int = 1) -> PtzStatusData:
        """Get PTZ status."""
        return PtzStatusData.create_from_response(
            await self._async_api_request(
                ApiEndpoints.PTZ, params={"action": "getStatus", "channel": channel}
            )
        )

    @property
    async def async_storage_info(self) -> list[StorageDeviceInfo]:
        """Get storage device info."""
        return StorageDeviceInfo.create_from_response(
            await self._async_api_request(
                ApiEndpoints.STORAGE_DEVICE,
                params={
                    "action": "getDeviceAllInfo",
                },
            )
        )

    @property
    async def async_video_image_control(self) -> list[VideoImageControl]:
        """Get flip, mirror, and rotate settings."""
        return VideoImageControl.create_from_response(
            await self._async_api_request(
                ApiEndpoints.CONFIG_MANAGER,
                params={"action": "getConfig", "name": "VideoImageControl"},
            )
        )

    async def async_set_video_image_control(
        self, video_image_control: VideoImageControl, channel: int = 1
    ) -> None:
        """Set image control settings."""
        await self._async_api_request(
            ApiEndpoints.CONFIG_MANAGER,
            params={
                "action": "setConfig",
                f"VideoImageControl[{channel - 1}].Flip": video_image_control.flip,
                f"VideoImageControl[{channel - 1}].Mirror": video_image_control.mirror,
                f"VideoImageControl[{channel - 1}].Rotate90": video_image_control.rotate_90,  # noqa: E501
            },
        )

    async def async_get_video_in_day_night(
        self,
    ) -> list[list[VideoDayNight]]:
        """Video input day/night settings."""
        return VideoDayNight.create_from_response(
            await self._async_api_request(
                ApiEndpoints.CONFIG_MANAGER,
                params={"action": "getConfig", "name": "VideoInDayNight"},
            )
        )

    async def async_set_video_in_day_night(
        self,
        video_day_night: VideoDayNight,
        config_no: ConfigNo,
        channel: int = 1,
    ) -> None:
        """Set video input day/night settings for a config and channel."""
        await self._async_api_request(
            ApiEndpoints.CONFIG_MANAGER,
            params={
                "action": "setConfig",
                f"VideoInDayNight[{channel - 1}][{config_no}].Type": video_day_night.type,  # noqa: E501
                f"VideoInDayNight[{channel - 1}][{config_no}].Mode": video_day_night.mode,  # noqa: E501
                f"VideoInDayNight[{channel - 1}][{config_no}].Sensitivity": video_day_night.sensitivity,  # noqa: E501
                f"VideoInDayNight[{channel - 1}][{config_no}].Delay": video_day_night.delay_seconds,  # noqa: E501
            },
        )

    async def async_set_privacy_mode_on(self, on: bool, channel: int = 1) -> None:
        """Set privacy mode on or off."""
        await self._async_api_request(
            ApiEndpoints.CONFIG_MANAGER,
            params={"action": "setConfig", f"LeLensMask[{channel - 1}].Enable": on},
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

    async def async_set_smart_track_on(self, on: bool) -> None:
        """Set smart tracking mode on or off."""
        await self._async_api_request(
            ApiEndpoints.CONFIG_MANAGER,
            params={"action": "setConfig", "LeSmartTrack[0].Enable": on},
        )

    async def async_get_smart_track_on(self) -> bool:
        """Get privacy mode state."""
        response = await self._async_api_request(
            ApiEndpoints.CONFIG_MANAGER,
            params={"action": "getConfig", "name": "LeSmartTrack"},
        )
        if (enabled := response["LeSmartTrack"][0]["Enable"].lower()) in [
            "true",
            "false",
        ]:
            return enabled == "true"
        raise ValueError("Unexpected response reading smart track status")

    async def async_snapshot(self, channel: int = 1, subtype: int = 0) -> bytes:
        """Get a still frame from the camera."""
        response: bytes = await self._async_api_request(
            ApiEndpoints.SNAPSHOT, params={"channel": channel, "type": subtype}
        )
        return response

    async def async_get_current_time(self) -> datetime:
        """Get the current time from the camera."""
        response = await self._async_api_request(
            ApiEndpoints.GLOBAL, params={"action": "getCurrentTime"}
        )
        return datetime.strptime(response["result"], "%Y-%m-%d %H:%M:%S")

    async def async_set_current_time(self, set_time: datetime | None = None) -> None:
        """
        Set the current time for the camera.
        If set_time is not specified, use current time from system.
        """
        if set_time is None:
            set_time = datetime.now()
        set_time_str: str = set_time.strftime("%Y-%m-%d %H:%M:%S")
        await self._async_api_request(
            ApiEndpoints.GLOBAL,
            params={"action": "setCurrentTime", "time": set_time_str},
        )

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
            base_url=str(self.url),
            verify=self._verify,
            **kwargs,
        )

    async def _async_api_request(
        self, endpoint, *, method="GET", params: dict[str, Any] | None = None
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
