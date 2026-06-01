from __future__ import annotations

import logging
import os
import sys
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

_ZOS_ROOT = r"C:\Program Files\ANSYS Inc\Ansys Zemax OpticStudio 2024 R1.00"


def _ensure_zos_paths() -> None:
    """Ensure ZOSAPI DLL directories are in sys.path BEFORE clr is used."""
    import sys
    for d in (_ZOS_ROOT, os.path.join(_ZOS_ROOT, "ZOS-API", "Libraries")):
        if os.path.isdir(d) and d not in sys.path:
            sys.path.insert(0, d)


# Initialize paths at module load time
_ensure_zos_paths()


def _load_assembly(name: str) -> Any:
    """Load a ZOSAPI assembly by name."""
    import clr
    old_dir = os.getcwd()
    try:
        for d in (_ZOS_ROOT, os.path.join(_ZOS_ROOT, "ZOS-API", "Libraries")):
            path = os.path.join(d, name)
            if os.path.exists(path):
                os.chdir(d)
                try:
                    clr.AddReference(name)
                    return
                except Exception:
                    pass
                name_no_ext = name.replace(".dll", "")
                try:
                    clr.AddReference(name_no_ext)
                    return
                except Exception:
                    pass
        raise ZOSConnectionError(f"Cannot load {name}: file not found in Zemax directories")
    finally:
        os.chdir(old_dir)


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
            _load_assembly(ZOSAPI_INTERFACES_DLL)
            _load_assembly(ZOSAPI_DLL)

            import ZOSAPI
            self._zosapi = ZOSAPI

            # Create application via ZOSAPI_Connection (Zemax 2024 R1 API)
            conn = ZOSAPI.ZOSAPI_Connection()
            conn.ConnectionTimeoutSeconds = int(max(timeout, 10))
            self._app = conn.CreateNewApplication()
            if self._app is None:
                raise ZOSConnectionError("Failed to create Zemax OpticStudio application")

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
        return self._zosapi

    @property
    def zosapi(self) -> Any:
        return self._zosapi
