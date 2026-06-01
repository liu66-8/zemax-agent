from __future__ import annotations

import logging
from typing import Any, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class MTFData(BaseModel):
    frequency: float = 30.0
    max_frequency: float = 100.0
    tangential: dict[str, float] = Field(default_factory=dict)
    sagittal: dict[str, float] = Field(default_factory=dict)
    diffraction_limit: Optional[float] = None


class SpotData(BaseModel):
    rms_radius: dict[str, float] = Field(default_factory=dict)
    geo_radius: dict[str, float] = Field(default_factory=dict)
    airy_radius: float = 0.0
    scale: float = 100.0


class FieldCurvatureData(BaseModel):
    sagittal: list[float] = Field(default_factory=list)
    tangential: list[float] = Field(default_factory=list)
    max_field: float = 0.0
    distortion: list[float] = Field(default_factory=list)


class WavefrontData(BaseModel):
    rms: dict[str, float] = Field(default_factory=dict)
    pv: dict[str, float] = Field(default_factory=dict)
    zernike_coefficients: dict[int, float] = Field(default_factory=dict)


class SeidelData(BaseModel):
    spherical: dict[int, float] = Field(default_factory=dict)
    coma: dict[int, float] = Field(default_factory=dict)
    astigmatism: dict[int, float] = Field(default_factory=dict)
    field_curvature: dict[int, float] = Field(default_factory=dict)
    distortion: dict[int, float] = Field(default_factory=dict)
    axial_color: dict[int, float] = Field(default_factory=dict)
    lateral_color: dict[int, float] = Field(default_factory=dict)


class ChromaticData(BaseModel):
    axial_color: float = 0.0
    lateral_color: float = 0.0
    secondary_spectrum: float = 0.0


class SimulationData(BaseModel):
    mtf: Optional[MTFData] = None
    spot: Optional[SpotData] = None
    field_curvature: Optional[FieldCurvatureData] = None
    wavefront: Optional[WavefrontData] = None
    seidel: Optional[SeidelData] = None
    chromatic: Optional[ChromaticData] = None


class SimulationDataReader:
    def read_mtf(self, raw_mtf: dict[str, Any]) -> MTFData:
        return MTFData(
            frequency=raw_mtf.get("frequency", 30.0),
            max_frequency=raw_mtf.get("max_frequency", 100.0),
            tangential=raw_mtf.get("tangential", {}),
            sagittal=raw_mtf.get("sagittal", {}),
            diffraction_limit=raw_mtf.get("diffraction_limit"),
        )

    def read_spot(self, raw_spot: dict[str, Any]) -> SpotData:
        return SpotData(
            rms_radius=raw_spot.get("rms_radius", {}),
            geo_radius=raw_spot.get("geo_radius", {}),
            airy_radius=raw_spot.get("airy_radius", 0.0),
            scale=raw_spot.get("scale", 100.0),
        )

    def read_field_curvature(self, raw_fc: dict[str, Any]) -> FieldCurvatureData:
        return FieldCurvatureData(
            sagittal=raw_fc.get("sagittal", []),
            tangential=raw_fc.get("tangential", []),
            max_field=raw_fc.get("max_field", 0.0),
            distortion=raw_fc.get("distortion", []),
        )

    def read_wavefront(self, raw_wf: dict[str, Any]) -> WavefrontData:
        return WavefrontData(
            rms=raw_wf.get("rms", {}),
            pv=raw_wf.get("pv", {}),
            zernike_coefficients=raw_wf.get("zernike_coefficients", {}),
        )

    def read_seidel(self, raw_seidel: dict[str, Any]) -> SeidelData:
        surfaces = raw_seidel.get("surfaces", [])
        last = surfaces[-1] if surfaces else {}
        return SeidelData(
            spherical={0: last.get("spherical", 0.0)},
            coma={0: last.get("coma", 0.0)},
            astigmatism={0: last.get("astigmatism", 0.0)},
            field_curvature={0: last.get("field_curvature", 0.0)},
            distortion={0: last.get("distortion", 0.0)},
            axial_color={0: last.get("axial_color", 0.0)},
            lateral_color={0: last.get("lateral_color", 0.0)},
        )

    def read_chromatic(self, raw_chromatic: dict[str, Any]) -> ChromaticData:
        return ChromaticData(
            axial_color=raw_chromatic.get("axial_color", 0.0),
            lateral_color=raw_chromatic.get("lateral_color", 0.0),
            secondary_spectrum=raw_chromatic.get("secondary_spectrum", 0.0),
        )

    def read_all(self, raw_data: dict[str, Any]) -> SimulationData:
        return SimulationData(
            mtf=self.read_mtf(raw_data.get("mtf", {})) if raw_data.get("mtf") else None,
            spot=self.read_spot(raw_data.get("spot", {})) if raw_data.get("spot") else None,
            field_curvature=self.read_field_curvature(raw_data.get("field_curvature", {})) if raw_data.get("field_curvature") else None,
            wavefront=self.read_wavefront(raw_data.get("wavefront", {})) if raw_data.get("wavefront") else None,
            seidel=self.read_seidel(raw_data.get("seidel", {})) if raw_data.get("seidel") else None,
            chromatic=self.read_chromatic(raw_data.get("chromatic", {})) if raw_data.get("chromatic") else None,
        )
