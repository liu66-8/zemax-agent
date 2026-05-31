from __future__ import annotations

import logging
import os
from typing import Any

from zemax_agent.zos.connection import ZOSConnection
from zemax_agent.zos.models import SystemInfo

logger = logging.getLogger(__name__)


def load_zmx(conn: ZOSConnection, file_path: str) -> SystemInfo:
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"ZMX file not found: {file_path}")

    conn.system.LoadFile(file_path, False)
    logger.info("Loaded ZMX: %s", file_path)
    return get_system_info(conn)


def save_zmx(conn: ZOSConnection, file_path: str) -> None:
    os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)
    conn.system.SaveAs(file_path)
    logger.info("Saved ZMX: %s", file_path)


def get_system_info(conn: ZOSConnection) -> SystemInfo:
    system = conn.system
    return SystemInfo(
        mode="Sequential" if system.Mode == 0 else "NonSequential",
        aperture_type=str(system.SystemData.Aperture.ApertureType),
        aperture_value=float(system.SystemData.Aperture.ApertureValue),
        field_count=int(system.SystemData.Fields.NumberOfFields),
        wavelength_count=int(system.SystemData.Wavelengths.NumberOfWavelengths),
        surface_count=int(system.LDE.NumberOfSurfaces),
        is_loaded=True,
        file_path=str(system.SystemFile),
    )


def make_sequential(conn: ZOSConnection) -> None:
    if conn.system.Mode != 0:
        conn.system.MakeSequential()
        logger.info("Switched to sequential mode")
