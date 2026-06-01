from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class SurfaceData(BaseModel):
    index: int
    surf_type: str = "Standard"
    comment: str = ""
    radius: Optional[float] = 0.0
    thickness: Optional[float] = 0.0
    glass: str = ""
    semi_diameter: float = 0.0
    conic: float = 0.0
    coating: str = ""
    is_stop: bool = False
    is_reflective: bool = False


class LensSummary(BaseModel):
    surface_count: int
    stop_surface: int
    aperture_type: str = ""
    aperture_value: float = 0.0
    effective_focal_length: float = 0.0
    f_number: float = 0.0
    image_space_na: float = 0.0
    entrance_pupil_diameter: float = 0.0
    exit_pupil_diameter: float = 0.0
    total_track: float = 0.0
    surfaces: list[SurfaceData] = Field(default_factory=list)


class FieldConfig(BaseModel):
    field_count: int = 3
    field_type: int = 0
    fields: list[tuple[float, float]] = Field(default_factory=lambda: [(0, 0), (0, 0.7), (0, 1.0)])


class WavelengthConfig(BaseModel):
    wavelength_count: int = 3
    wavelengths: list[float] = Field(default_factory=lambda: [0.48613270, 0.58756180, 0.65627250])
    primary_wavelength: int = 2


class MTFData(BaseModel):
    frequency: float = 30.0
    field_count: int = 0
    fields: list[dict[str, Any]] = Field(default_factory=list)
    max_frequency: float = 0.0
    diffraction_limit: Optional[dict[str, Any]] = None


class SpotData(BaseModel):
    field_count: int = 0
    fields: list[dict[str, Any]] = Field(default_factory=list)
    airy_radius: float = 0.0
    wavelengths: list[float] = Field(default_factory=list)


class FieldCurvatureData(BaseModel):
    wavelengths: list[float] = Field(default_factory=list)
    sagittal: list[float] = Field(default_factory=list)
    tangential: list[float] = Field(default_factory=list)
    max_field: float = 0.0


class WavefrontData(BaseModel):
    field_count: int = 0
    fields: list[dict[str, Any]] = Field(default_factory=list)
    rms_wavefront: list[float] = Field(default_factory=list)
    pv_wavefront: list[float] = Field(default_factory=list)


class SeidelData(BaseModel):
    surfaces: list[dict[str, Any]] = Field(default_factory=list)
    sum: dict[str, float] = Field(default_factory=dict)


class RayFanData(BaseModel):
    field_count: int = 0
    fields: list[dict[str, Any]] = Field(default_factory=list)
    scale: float = 50.0


class LayoutData(BaseModel):
    ray_count: int = 3
    fields_shown: list[int] = Field(default_factory=list)
    wavelengths_shown: list[int] = Field(default_factory=list)


class POPData(BaseModel):
    wavelength_index: int = 0
    field_index: int = 0
    beam_type: str = "Gaussian"
    x_width: float = 1.0
    y_width: float = 1.0
    data: list[list[float]] = Field(default_factory=list)


class OptimizationConfig(BaseModel):
    algorithm: str = "DampedLeastSquares"
    cycles: int = 3
    auto_scale: bool = True
    variables: list[tuple[int, int]] = Field(default_factory=list)
    merit_function_operands: list[dict[str, Any]] = Field(default_factory=list)
    convergence_threshold: float = 1e-6


class OptimizationResult(BaseModel):
    initial_mf: float = 0.0
    final_mf: float = 0.0
    cycles_completed: int = 0
    converged: bool = False
    improvement_percent: float = 0.0


class ToleranceConfig(BaseModel):
    default_tolerances: bool = True
    surface_tolerances: dict[str, float] = Field(default_factory=dict)
    element_tolerances: dict[str, float] = Field(default_factory=dict)
    compensators: list[dict[str, Any]] = Field(default_factory=list)
    monte_carlo_samples: int = 500


class ToleranceResult(BaseModel):
    sensitivity_data: list[dict[str, Any]] = Field(default_factory=list)
    monte_carlo_data: dict[str, Any] = Field(default_factory=dict)
    worst_offenders: list[dict[str, Any]] = Field(default_factory=list)
    estimated_yield: float = 0.0


class SystemInfo(BaseModel):
    mode: str = "Sequential"
    aperture_type: str = ""
    aperture_value: float = 0.0
    field_count: int = 0
    wavelength_count: int = 0
    surface_count: int = 0
    is_loaded: bool = False
    file_path: str = ""
