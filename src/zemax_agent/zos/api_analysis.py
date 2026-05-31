from __future__ import annotations

import logging
from typing import Any

from zemax_agent.zos.connection import ZOSConnection
from zemax_agent.zos.models import MTFData, SpotData, WavefrontData, SeidelData, RayFanData, LayoutData, POPData, FieldCurvatureData

logger = logging.getLogger(__name__)


def _run_analysis(conn: ZOSConnection, analysis_type: str, settings: Any = None) -> Any:
    analyses = conn.analyses
    new_win = analyses.New_Analysis(analysis_type)
    if settings is not None:
        new_win.ApplySettings(settings)
    new_win.ApplyAndWaitForCompletion()
    results = new_win.GetResults()
    new_win.Close()
    return results


def _unescaped_save(conn: ZOSConnection, analysis_type: str, settings: Any, file_path: str) -> None:
    analyses = conn.analyses
    new_win = analyses.New_Analysis(analysis_type)
    if settings is not None:
        new_win.ApplySettings(settings)
    new_win.ApplyAndWaitForCompletion()
    new_win.GetResults().GetTextFile(file_path)
    new_win.Close()


def get_mtf(conn: ZOSConnection, frequency: float = 30.0, max_frequency: float = 100.0) -> MTFData:
    settings = conn.analyses.New_AnalysisSettings()
    settings.ModifiedSettings.MTF.SampleFrequency = 2
    settings.ModifiedSettings.MTF.MaximumFrequency = max_frequency

    results = _run_analysis(conn, "MTF", settings)
    mtf_data = results.Data
    if hasattr(mtf_data, "Cells"):
        mtf_data = mtf_data.Cells

    field_count = min(5, getattr(getattr(settings, "ModifiedSettings", None), "MTF", None) and 5 or 5)
    return MTFData(
        frequency=frequency,
        max_frequency=max_frequency,
        field_count=field_count,
        fields=[],
    )


def get_spot(conn: ZOSConnection) -> SpotData:
    settings = conn.analyses.New_AnalysisSettings()
    results = _run_analysis(conn, "Spot", settings)
    airy = float(conn.system.LDE.GetAiryRadius())
    return SpotData(airy_radius=airy)


def get_field_curvature(conn: ZOSConnection) -> FieldCurvatureData:
    settings = conn.analyses.New_AnalysisSettings()
    results = _run_analysis(conn, "FieldCurv", settings)
    return FieldCurvatureData()


def get_wavefront(conn: ZOSConnection) -> WavefrontData:
    settings = conn.analyses.New_AnalysisSettings()
    results = _run_analysis(conn, "Wavefront", settings)
    return WavefrontData()


def get_seidel(conn: ZOSConnection) -> SeidelData:
    settings = conn.analyses.New_AnalysisSettings()
    results = _run_analysis(conn, "Seidel", settings)
    return SeidelData()


def get_ray_fan(conn: ZOSConnection) -> RayFanData:
    settings = conn.analyses.New_AnalysisSettings()
    results = _run_analysis(conn, "RayFan", settings)
    return RayFanData()


def get_layout(conn: ZOSConnection, ray_count: int = 3) -> LayoutData:
    settings = conn.analyses.New_AnalysisSettings()
    settings.ModifiedSettings.Layout.NumberOfRays = ray_count
    results = _run_analysis(conn, "Layout", settings)
    return LayoutData(ray_count=ray_count)


def get_pop(
    conn: ZOSConnection,
    wavelength_index: int = 0,
    field_index: int = 0,
    beam_type: str = "Gaussian",
    x_width: float = 1.0,
    y_width: float = 1.0,
) -> POPData:
    settings = conn.analyses.New_AnalysisSettings()
    pop_settings = settings.ModifiedSettings.POP

    pop_settings.Wavelength = wavelength_index + 1
    pop_settings.Field = field_index + 1
    pop_settings.BeamType = 0 if beam_type == "Gaussian" else 1
    pop_settings.X_Sampling = 256
    pop_settings.Y_Sampling = 256
    pop_settings.X_Width = x_width
    pop_settings.Y_Width = y_width

    results = _run_analysis(conn, "POP", settings)
    return POPData(
        wavelength_index=wavelength_index,
        field_index=field_index,
        beam_type=beam_type,
        x_width=x_width,
        y_width=y_width,
    )
