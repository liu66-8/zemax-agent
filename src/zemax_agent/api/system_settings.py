import logging
from typing import Any, Dict, List

from .connection import ZemaxConnection

logger = logging.getLogger(__name__)


class ApertureType:
    ENTRANCE_PUPIL_DIAMETER = "EntrancePupilDiameter"
    IMAGE_SPACE_F_NUMBER = "ImageSpaceFNumber"
    OBJECT_SPACE_NA = "ObjectSpaceNA"
    FLOAT_BY_STOP = "FloatByStopSize"


class FieldType:
    ANGLE = 0
    OBJECT_HEIGHT = 1
    PARAXIAL_IMAGE_HEIGHT = 2


class ZemaxSystemSettings:
    def __init__(self, connection: ZemaxConnection):
        self._conn = connection

    @property
    def _system(self):
        return self._conn.system

    @property
    def _sys_data(self):
        return self._system.SystemData

    def get_aperture(self) -> Dict[str, Any]:
        self._conn.ensure_connected()
        sd = self._sys_data
        return {
            "aperture_type": str(sd.Aperture.ApertureType),
            "aperture_value": float(sd.Aperture.ApertureValue),
            "entrance_pupil_diameter": float(sd.Aperture.EntrancePupilDiameter),
            "image_space_f_number": float(sd.Aperture.ImageSpaceFNumber),
        }

    def set_aperture(self, aperture_type: str, value: float) -> None:
        self._conn.ensure_connected()
        if value <= 0:
            raise ValueError(f"孔径值必须大于0: {value}")
        sd = self._sys_data
        sd.Aperture.ApertureType = getattr(sd.Aperture, aperture_type, sd.Aperture.ApertureType)
        sd.Aperture.ApertureValue = value
        logger.info(f"孔径已设置: {aperture_type}={value}")

    def set_entrance_pupil_diameter(self, diameter: float) -> None:
        self.set_aperture(ApertureType.ENTRANCE_PUPIL_DIAMETER, diameter)

    def set_f_number(self, f_number: float) -> None:
        self.set_aperture(ApertureType.IMAGE_SPACE_F_NUMBER, f_number)

    def set_object_na(self, na: float) -> None:
        self.set_aperture(ApertureType.OBJECT_SPACE_NA, na)

    def get_fields(self) -> List[Dict[str, Any]]:
        self._conn.ensure_connected()
        fields = []
        sd = self._sys_data
        for i in range(1, sd.Fields.NumberOfFields + 1):
            field = sd.Fields.GetField(i)
            fields.append({
                "field_number": i,
                "field_type": int(field.FieldType),
                "x_field": float(field.XField),
                "y_field": float(field.YField),
                "weight": float(field.Weight),
                "vdx": float(field.VDX) if hasattr(field, "VDX") else 0.0,
                "vdy": float(field.VDY) if hasattr(field, "VDY") else 0.0,
            })
        return fields

    def set_field_count(self, count: int) -> None:
        self._conn.ensure_connected()
        if count < 1:
            raise ValueError("视场数量至少为1")
        sd = self._sys_data
        sd.Fields.NumberOfFields = count

    def set_field(
        self,
        field_number: int,
        field_type: int,
        x_field: float,
        y_field: float,
        weight: float = 1.0,
    ) -> None:
        self._conn.ensure_connected()
        sd = self._sys_data
        if field_number < 1 or field_number > sd.Fields.NumberOfFields:
            raise ValueError(f"视场序号 {field_number} 超出范围")

        field = sd.Fields.GetField(field_number)
        field.FieldType = field_type
        field.XField = x_field
        field.YField = y_field
        field.Weight = weight
        logger.info(
            f"视场 {field_number} 已设置: type={field_type}, "
            f"x={x_field}, y={y_field}, weight={weight}"
        )

    def setup_standard_fields(
        self, max_field: float, field_type: int = 0, num_fields: int = 3
    ) -> None:
        self._conn.ensure_connected()
        self.set_field_count(num_fields)
        if num_fields == 1:
            self.set_field(1, field_type, 0.0, max_field)
        elif num_fields == 3:
            self.set_field(1, field_type, 0.0, 0.0)
            self.set_field(2, field_type, 0.0, max_field * 0.707)
            self.set_field(3, field_type, 0.0, max_field)
        elif num_fields == 2:
            self.set_field(1, field_type, 0.0, 0.0)
            self.set_field(2, field_type, 0.0, max_field)
        logger.info(f"标准视场已设置: {num_fields} 个视场, 最大={max_field}")

    def get_wavelengths(self) -> List[Dict[str, Any]]:
        self._conn.ensure_connected()
        wavelengths = []
        sd = self._sys_data
        for i in range(1, sd.Wavelengths.NumberOfWavelengths + 1):
            wl = sd.Wavelengths.GetWavelength(i)
            wavelengths.append({
                "wavelength_number": i,
                "wavelength": float(wl.Wavelength),
                "weight": float(wl.Weight),
            })
        return wavelengths

    def set_wavelength_count(self, count: int) -> None:
        self._conn.ensure_connected()
        if count < 1:
            raise ValueError("波长数量至少为1")
        sd = self._sys_data
        sd.Wavelengths.NumberOfWavelengths = count

    def set_wavelength(
        self, wavelength_number: int, wavelength: float, weight: float = 1.0
    ) -> None:
        self._conn.ensure_connected()
        if wavelength <= 0:
            raise ValueError(f"波长必须大于0: {wavelength}")
        sd = self._sys_data
        if wavelength_number < 1 or wavelength_number > sd.Wavelengths.NumberOfWavelengths:
            raise ValueError(f"波长序号 {wavelength_number} 超出范围")

        wl = sd.Wavelengths.GetWavelength(wavelength_number)
        wl.Wavelength = wavelength
        wl.Weight = weight
        logger.info(f"波长 {wavelength_number} 已设置: {wavelength}μm, weight={weight}")

    def set_primary_wavelength(self, wavelength_number: int) -> None:
        self._conn.ensure_connected()
        sd = self._sys_data
        sd.Wavelengths.PrimaryWavelength = wavelength_number
        logger.info(f"主波长已设置为 波长 {wavelength_number}")

    def setup_visible_wavelengths(self, primary: float = 0.5876) -> None:
        self._conn.ensure_connected()
        self.set_wavelength_count(3)
        self.set_wavelength(1, 0.4861, 1.0)
        self.set_wavelength(2, primary, 1.0)
        self.set_wavelength(3, 0.6563, 1.0)
        self.set_primary_wavelength(2)
        logger.info(f"可见光波长已设置 (F-d-C)，主波长={primary}μm")

    def get_stop_surface(self) -> int:
        self._conn.ensure_connected()
        return self._system.LDE.StopSurface

    def set_stop_surface(self, surface_num: int) -> None:
        self._conn.ensure_connected()
        self._system.LDE.MakeSurfaceStop(surface_num)
        logger.info(f"光阑已设置为面 {surface_num}")
