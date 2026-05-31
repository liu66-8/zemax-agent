from __future__ import annotations

import logging
import time
from typing import Any, Optional

import clr

from zemax_agent.zos.exceptions import (
    ZOSConnectionError,
    ZOSError,
    ZOSNotConnectedError,
)

logger = logging.getLogger(__name__)

STANDALONE_PROG_ID = "ZOSAPI.ZOSAPIApplication"
EXTENSION_APPLICATION_NAME = "ZOSAPI_Application"

ZOSAPI_INTERFACES_DLL = "ZOSAPI_Interfaces.dll"
ZOSAPI_DLL = "ZOSAPI.dll"


class ZOSConnection:
    def __init__(self, mode: str = "standalone"):
        self._mode = mode
        self._zosapi_interface = None
        self._zosapi = None
        self._app: Any = None
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected

    def connect(self, timeout: float = 30.0) -> None:
        if self._connected:
            return

        try:
            clr.AddReference(ZOSAPI_INTERFACES_DLL)
            clr.AddReference(ZOSAPI_DLL)

            import ZOSAPI_Interfaces as ZOSAPI_Intf
            import ZOSAPI as ZOSAPI_Impl

            self._zosapi_interface = ZOSAPI_Intf
            self._zosapi = ZOSAPI_Impl

            if self._mode == "standalone":
                self._app = ZOSAPI_Impl.ZOSAPI_Initializer.CreateInitializer()
                start_time = time.time()
                while time.time() - start_time < timeout:
                    try:
                        self._app = self._app.CreateNewApplication()
                        if self._app is not None and self._app.IsValidLicenseForAPI:
                            break
                    except Exception:
                        time.sleep(1.0)
                else:
                    raise ZOSConnectionError("Timeout waiting for Zemax OpticStudio to start")

                if not self._app.IsValidLicenseForAPI:
                    raise ZOSConnectionError("No valid Zemax OpticStudio license for API")
            else:
                self._app = ZOSAPI_Impl.ZOSAPI_Initializer.CreateInitializer()
                self._app = self._app.ConnectAsExtension(EXTENSION_APPLICATION_NAME)

            self._connected = True
            logger.info("ZOS-API connected (mode=%s)", self._mode)

        except ZOSConnectionError:
            raise
        except Exception as e:
            raise ZOSConnectionError(f"Failed to connect to Zemax OpticStudio: {e}") from e

    def disconnect(self) -> None:
        if not self._connected:
            return
        try:
            if self._app is not None:
                self._app.CloseApplication()
        except Exception:
            pass
        self._app = None
        self._connected = False
        logger.info("ZOS-API disconnected")

    @property
    def app(self) -> Any:
        if not self._connected:
            raise ZOSNotConnectedError("Not connected to Zemax OpticStudio")
        return self._app

    @property
    def system(self) -> Any:
        return self.app.PrimarySystem

    @property
    def lens_data_editor(self) -> Any:
        return self.system.LDE

    @property
    def mode_editor(self) -> Any:
        return self.system.MFE

    @property
    def tools(self) -> Any:
        return self.system.Tools

    @property
    def analyses(self) -> Any:
        return self.system.Analyses

    @property
    def tolerancing(self) -> Any:
        return self.system.Tolerancing

    def ensure_sequential_mode(self) -> None:
        if not self.system.Mode == 0:
            self.system.MakeSequential()

    @property
    def zosapi_interface(self) -> Any:
        return self._zosapi_interface

    @property
    def zosapi(self) -> Any:
        return self._zosapi
