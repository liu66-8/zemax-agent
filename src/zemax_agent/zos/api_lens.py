from __future__ import annotations

import logging
from typing import Any

from zemax_agent.zos.connection import ZOSConnection
from zemax_agent.zos.models import LensSummary, SurfaceData, FieldConfig, WavelengthConfig

logger = logging.getLogger(__name__)


def _get_lde(conn: ZOSConnection) -> Any:
    return conn.lens_data_editor


def get_surface_data(conn: ZOSConnection, surface_index: int) -> SurfaceData:
    lde = _get_lde(conn)
    surf = lde.GetSurfaceAt(surface_index)
    return SurfaceData(
        index=surface_index,
        surf_type=str(surf.TypeName),
        comment=str(surf.Comment),
        radius=float(surf.Radius),
        thickness=float(surf.Thickness),
        glass=str(surf.MaterialName),
        semi_diameter=float(surf.SemiDiameter),
        conic=float(surf.Conic),
        coating=str(surf.CoatingName),
        is_stop=bool(surf.IsStop),
        is_reflective=bool(surf.IsReflective),
    )


def set_surface_data(conn: ZOSConnection, surface_index: int, **kwargs: Any) -> SurfaceData:
    lde = _get_lde(conn)
    surf = lde.GetSurfaceAt(surface_index)

    if "surf_type" in kwargs:
        surf.ChangeType(kwargs["surf_type"])
    if "comment" in kwargs:
        surf.Comment = kwargs["comment"]
    if "radius" in kwargs:
        surf.Radius = float(kwargs["radius"])
    if "thickness" in kwargs:
        surf.Thickness = float(kwargs["thickness"])
    if "glass" in kwargs:
        surf.MaterialName = kwargs["glass"]
    if "semi_diameter" in kwargs:
        surf.SemiDiameter = float(kwargs["semi_diameter"])
    if "conic" in kwargs:
        surf.Conic = float(kwargs["conic"])
    if "coating" in kwargs:
        surf.CoatingName = kwargs["coating"]
    if "is_stop" in kwargs and kwargs["is_stop"]:
        surf.MakeSurfaceStop()

    return get_surface_data(conn, surface_index)


def insert_surface(conn: ZOSConnection, after_index: int) -> SurfaceData:
    lde = _get_lde(conn)
    lde.InsertNewSurfaceAt(after_index)
    return get_surface_data(conn, after_index + 1)


def delete_surface(conn: ZOSConnection, surface_index: int) -> None:
    lde = _get_lde(conn)
    lde.DeleteSurfaceAt(surface_index)


def get_surface_count(conn: ZOSConnection) -> int:
    lde = _get_lde(conn)
    return int(lde.NumberOfSurfaces)


def set_radius(conn: ZOSConnection, surface_index: int, radius: float) -> SurfaceData:
    return set_surface_data(conn, surface_index, radius=radius)


def set_thickness(conn: ZOSConnection, surface_index: int, thickness: float) -> SurfaceData:
    return set_surface_data(conn, surface_index, thickness=thickness)


def set_glass(conn: ZOSConnection, surface_index: int, glass_name: str) -> SurfaceData:
    return set_surface_data(conn, surface_index, glass=glass_name)


def set_surface_type(conn: ZOSConnection, surface_index: int, surf_type: str) -> SurfaceData:
    return set_surface_data(conn, surface_index, surf_type=surf_type)


def make_surface_stop(conn: ZOSConnection, surface_index: int) -> SurfaceData:
    return set_surface_data(conn, surface_index, is_stop=True)


def set_aperture(conn: ZOSConnection, aperture_type: str, aperture_value: float) -> None:
    system = conn.system
    system.SystemData.Aperture.ApertureType = _aperture_type_to_enum(conn, aperture_type)
    system.SystemData.Aperture.ApertureValue = aperture_value


def _aperture_type_to_enum(conn: ZOSConnection, apt_type: str) -> Any:
    mapping = {
        "EPD": 0,
        "FNumber": 1,
        "NA": 2,
        "FloatByStopSize": 3,
    }
    val = mapping.get(apt_type, 0)
    return val


def set_fields(conn: ZOSConnection, config: FieldConfig) -> None:
    system = conn.system
    fd = system.SystemData.Fields
    fd.SetFieldCount(config.field_count)
    for i, (hx, hy) in enumerate(config.fields):
        if i < config.field_count:
            f = fd.GetField(i + 1)
            f.X = hx
            f.Y = hy


def get_fields(conn: ZOSConnection) -> FieldConfig:
    system = conn.system
    fd = system.SystemData.Fields
    field_count = int(fd.NumberOfFields)
    fields = []
    for i in range(1, field_count + 1):
        f = fd.GetField(i)
        fields.append((float(f.X), float(f.Y)))
    return FieldConfig(field_count=field_count, field_type=int(fd.GetFieldType()), fields=fields)


def set_wavelengths(conn: ZOSConnection, config: WavelengthConfig) -> None:
    system = conn.system
    wd = system.SystemData.Wavelengths
    wd.SetWavelengthCount(config.wavelength_count)
    for i, wl in enumerate(config.wavelengths):
        if i < config.wavelength_count:
            w = wd.GetWavelength(i + 1)
            w.Wavelength = wl
    wd.PrimaryWavelength = config.primary_wavelength


def get_wavelengths(conn: ZOSConnection) -> WavelengthConfig:
    system = conn.system
    wd = system.SystemData.Wavelengths
    wl_count = int(wd.NumberOfWavelengths)
    wavelengths = [float(wd.GetWavelength(i + 1).Wavelength) for i in range(wl_count)]
    return WavelengthConfig(
        wavelength_count=wl_count,
        wavelengths=wavelengths,
        primary_wavelength=int(wd.PrimaryWavelength),
    )


def get_lens_data_summary(conn: ZOSConnection) -> LensSummary:
    system = conn.system
    lde = _get_lde(conn)
    surface_count = int(lde.NumberOfSurfaces)

    surfaces = [get_surface_data(conn, i) for i in range(1, surface_count)]
    stop_surf = 1
    for s in surfaces:
        if s.is_stop:
            stop_surf = s.index
            break

    return LensSummary(
        surface_count=surface_count,
        stop_surface=stop_surf,
        aperture_type=str(system.SystemData.Aperture.ApertureType),
        aperture_value=float(system.SystemData.Aperture.ApertureValue),
        effective_focal_length=float(system.LDE.GetEffectiveFocalLength(1)),
        f_number=float(system.LDE.GetFNumber(1)),
        image_space_na=float(system.LDE.GetImageSpaceNA()),
        entrance_pupil_diameter=float(system.LDE.GetEntrancePupilDiameter()),
        exit_pupil_diameter=float(system.LDE.GetExitPupilDiameter()),
        total_track=float(system.LDE.GetTotalTrack()),
        surfaces=surfaces,
    )
