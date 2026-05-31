"""Tests for ZemaxAnalysis optical analysis interface.

Uses MagicMock to simulate the ZOS-API analysis interfaces, covering
normal execution paths and exception handling for all analysis methods.
"""

from __future__ import annotations

from unittest.mock import MagicMock, PropertyMock

import numpy as np
import pytest

from zemax_agent.api.analysis import ZemaxAnalysis
from zemax_agent.api.connection import ZemaxConnection


def _make_data_grid(values, number_of_points=None, **extra_attrs):
    grid = MagicMock()
    grid.Values = values
    grid.NumberOfPoints = number_of_points or len(values)
    for attr, val in extra_attrs.items():
        setattr(grid, attr, val)
    return grid


def _make_analysis(analysis_name, data_grids=None, text_output=None):
    analysis = MagicMock()
    analysis.Settings = MagicMock()
    analysis.Settings.Field = MagicMock()
    analysis.Settings.Wavelength = MagicMock()

    results = MagicMock()
    if data_grids is not None:
        results.DataGrids = data_grids
    else:
        results.DataGrids = [_make_data_grid([], 0)]
    if text_output is not None:
        results.GetTextOutput.return_value = text_output
    else:
        results.GetTextOutput.return_value = None

    analysis.GetResults.return_value = results
    analysis.ApplyAndWaitForCompletion.return_value = None
    return analysis


def _make_connection():
    conn = MagicMock(spec=ZemaxConnection)
    conn.ensure_connected.return_value = None

    system = MagicMock()
    system.Analyses = MagicMock()
    system.Analyses.New_Analysis = MagicMock()
    type(conn).system = PropertyMock(return_value=system)

    return conn


class TestZemaxAnalysisInit:
    def test_init_stores_connection(self):
        conn = _make_connection()
        analysis = ZemaxAnalysis(conn)
        assert analysis._conn is conn

    def test_system_property_delegates_to_connection(self):
        conn = _make_connection()
        analysis = ZemaxAnalysis(conn)
        assert analysis._system is conn.system

    def test_analyses_property_delegates_to_system(self):
        conn = _make_connection()
        analysis = ZemaxAnalysis(conn)
        assert analysis._analyses is conn.system.Analyses

    def test_ensure_connected_called_on_each_analysis(self):
        conn = _make_connection()
        mock_analysis = _make_analysis("Mtf")
        conn.system.Analyses.New_Analysis.return_value = mock_analysis
        analysis = ZemaxAnalysis(conn)
        analysis.get_mtf(max_frequency=30.0)
        conn.ensure_connected.assert_called_once()


class TestGetMTF:
    def test_normal_call_returns_valid_data(self):
        conn = _make_connection()
        values = [0.1, 0.2, 0.3, 0.4, 0.5]
        grid = _make_data_grid(values, number_of_points=5)
        mock_analysis = _make_analysis("Mtf", data_grids=[grid])
        conn.system.Analyses.New_Analysis.return_value = mock_analysis

        analysis = ZemaxAnalysis(conn)
        result = analysis.get_mtf(max_frequency=50.0)

        conn.system.Analyses.New_Analysis.assert_called_once_with("Mtf")
        mock_analysis.ApplyAndWaitForCompletion.assert_called_once()
        mock_analysis.GetResults.assert_called_once()
        mock_analysis.Close.assert_called_once()
        assert result["max_frequency"] == 50.0
        assert result["number_of_points"] == 5
        assert result["values"] == values
        assert "frequency" in result
        assert "tangential_mtf" in result
        assert "sagittal_mtf" in result
        assert "diffraction_limit" in result

    def test_max_frequency_set_on_settings(self):
        conn = _make_connection()
        grid = _make_data_grid([0.0], 1)
        mock_analysis = _make_analysis("Mtf", data_grids=[grid])
        conn.system.Analyses.New_Analysis.return_value = mock_analysis

        analysis = ZemaxAnalysis(conn)
        analysis.get_mtf(max_frequency=75.0)

        assert mock_analysis.Settings.MaximumFrequency == 75.0

    def test_exception_propagates_on_failure(self):
        conn = _make_connection()
        conn.system.Analyses.New_Analysis.side_effect = RuntimeError("ZOS API error")

        analysis = ZemaxAnalysis(conn)
        with pytest.raises(RuntimeError, match="ZOS API error"):
            analysis.get_mtf()

    def test_default_max_frequency(self):
        conn = _make_connection()
        grid = _make_data_grid([1.0], 1)
        mock_analysis = _make_analysis("Mtf", data_grids=[grid])
        conn.system.Analyses.New_Analysis.return_value = mock_analysis

        analysis = ZemaxAnalysis(conn)
        result = analysis.get_mtf()
        assert result["max_frequency"] == 50.0

    def test_none_data_grid_is_handled(self):
        conn = _make_connection()
        mock_analysis = _make_analysis("Mtf", data_grids=[None])
        conn.system.Analyses.New_Analysis.return_value = mock_analysis

        analysis = ZemaxAnalysis(conn)
        result = analysis.get_mtf()
        assert result["number_of_points"] == 0
        assert "values" not in result


class TestGetSpotDiagram:
    def test_normal_call_returns_field_data(self):
        conn = _make_connection()
        values = [1.0, 2.5, 4.0, 0.0, 2.0, 3.0, 5.5, 0.0]
        grid = _make_data_grid(values, number_of_points=8, AiryDiameter=10.0)
        mock_analysis = _make_analysis("SpotDiagram", data_grids=[grid])
        conn.system.Analyses.New_Analysis.return_value = mock_analysis

        analysis = ZemaxAnalysis(conn)
        result = analysis.get_spot_diagram()

        conn.system.Analyses.New_Analysis.assert_called_once_with("SpotDiagram")
        assert result["fields"] == [1, 2]
        assert result["rms_radius"] == [2.5, 3.0]
        assert result["geo_radius"] == [4.0, 5.5]
        assert result["airy_radius"] == 5.0

    def test_no_airy_diameter_returns_none(self):
        conn = _make_connection()
        values = [1.0, 2.0, 3.0, 0.0]
        grid = _make_data_grid(values, number_of_points=4)
        del grid.AiryDiameter
        mock_analysis = _make_analysis("SpotDiagram", data_grids=[grid])
        conn.system.Analyses.New_Analysis.return_value = mock_analysis

        analysis = ZemaxAnalysis(conn)
        result = analysis.get_spot_diagram()
        assert result["airy_radius"] is None

    def test_incomplete_field_is_skipped(self):
        conn = _make_connection()
        values = [1.0, 2.0, 3.0]
        grid = _make_data_grid(values, number_of_points=3)
        mock_analysis = _make_analysis("SpotDiagram", data_grids=[grid])
        conn.system.Analyses.New_Analysis.return_value = mock_analysis

        analysis = ZemaxAnalysis(conn)
        result = analysis.get_spot_diagram()
        assert result["fields"] == []

    def test_exception_propagates(self):
        conn = _make_connection()
        conn.system.Analyses.New_Analysis.side_effect = RuntimeError("SPOT error")
        analysis = ZemaxAnalysis(conn)
        with pytest.raises(RuntimeError, match="SPOT error"):
            analysis.get_spot_diagram()


class TestGetFieldCurvatureDistortion:
    def test_normal_call_returns_both_curves(self):
        conn = _make_connection()
        fc_values = [0.1, -0.05, 0.0, 0.05, 0.1]
        dist_values = [0.0, 0.5, 1.0, 1.5, 2.0]
        fc_grid = _make_data_grid(fc_values, 5)
        dist_grid = _make_data_grid(dist_values, 5)
        mock_analysis = _make_analysis(
            "FieldCurvatureDistortion", data_grids=[fc_grid, dist_grid]
        )
        conn.system.Analyses.New_Analysis.return_value = mock_analysis

        analysis = ZemaxAnalysis(conn)
        result = analysis.get_field_curvature_distortion()

        assert result["field_curvature"]["values"] == fc_values
        assert result["field_curvature"]["number_of_points"] == 5
        assert result["distortion"]["values"] == dist_values
        assert result["distortion"]["number_of_points"] == 5
        mock_analysis.Close.assert_called_once()

    def test_handles_none_grids(self):
        conn = _make_connection()
        mock_analysis = _make_analysis(
            "FieldCurvatureDistortion", data_grids=[None, None]
        )
        conn.system.Analyses.New_Analysis.return_value = mock_analysis

        analysis = ZemaxAnalysis(conn)
        result = analysis.get_field_curvature_distortion()
        assert result["field_curvature"] == {}
        assert result["distortion"] == {}

    def test_exception_propagates(self):
        conn = _make_connection()
        conn.system.Analyses.New_Analysis.side_effect = RuntimeError("FCD error")
        analysis = ZemaxAnalysis(conn)
        with pytest.raises(RuntimeError, match="FCD error"):
            analysis.get_field_curvature_distortion()


class TestGetWavefront:
    def test_normal_call_returns_wavefront_data(self):
        conn = _make_connection()
        values = [0.01, -0.02, 0.015, -0.005, 0.008]
        grid = _make_data_grid(values, 5)
        mock_analysis = _make_analysis("WavefrontMap", data_grids=[grid])
        conn.system.Analyses.New_Analysis.return_value = mock_analysis

        analysis = ZemaxAnalysis(conn)
        result = analysis.get_wavefront(field_number=2, wavelength_number=3)

        conn.system.Analyses.New_Analysis.assert_called_once_with("WavefrontMap")
        mock_analysis.Settings.Field.SetFieldNumber.assert_called_once_with(2)
        mock_analysis.Settings.Wavelength.SetWavelengthNumber.assert_called_once_with(3)
        assert result["field_number"] == 2
        assert result["wavelength_number"] == 3
        assert result["values"] == values
        rms = float(np.sqrt(np.mean(np.array(values, dtype=float) ** 2)))
        pv = float(np.max(values) - np.min(values))
        assert result["rms_wavefront"] == pytest.approx(rms)
        assert result["pv_wavefront"] == pytest.approx(pv)

    def test_default_parameters(self):
        conn = _make_connection()
        grid = _make_data_grid([0.0], 1)
        mock_analysis = _make_analysis("WavefrontMap", data_grids=[grid])
        conn.system.Analyses.New_Analysis.return_value = mock_analysis

        analysis = ZemaxAnalysis(conn)
        result = analysis.get_wavefront()
        mock_analysis.Settings.Field.SetFieldNumber.assert_called_once_with(1)
        mock_analysis.Settings.Wavelength.SetWavelengthNumber.assert_called_once_with(1)
        assert result["field_number"] == 1
        assert result["wavelength_number"] == 1

    def test_exception_propagates(self):
        conn = _make_connection()
        conn.system.Analyses.New_Analysis.side_effect = RuntimeError("WF error")
        analysis = ZemaxAnalysis(conn)
        with pytest.raises(RuntimeError, match="WF error"):
            analysis.get_wavefront()

    def test_empty_data_yields_zero_rms_pv(self):
        conn = _make_connection()
        grid = _make_data_grid([], 0)
        mock_analysis = _make_analysis("WavefrontMap", data_grids=[grid])
        conn.system.Analyses.New_Analysis.return_value = mock_analysis

        analysis = ZemaxAnalysis(conn)
        result = analysis.get_wavefront()
        assert result["rms_wavefront"] == 0.0
        assert result["pv_wavefront"] == 0.0


class TestGetSeidelCoefficients:
    def test_normal_call_returns_raw_values(self):
        conn = _make_connection()
        values = [0.001, -0.003, 0.002, -0.001, 0.0005]
        grid = _make_data_grid(values, 5)
        mock_analysis = _make_analysis("SeidelCoefficients", data_grids=[grid])
        conn.system.Analyses.New_Analysis.return_value = mock_analysis

        analysis = ZemaxAnalysis(conn)
        result = analysis.get_seidel_coefficients()

        conn.system.Analyses.New_Analysis.assert_called_once_with("SeidelCoefficients")
        assert result["raw_values"] == values
        mock_analysis.Close.assert_called_once()

    def test_multiple_grids_are_all_processed(self):
        conn = _make_connection()
        grid0 = _make_data_grid([1.0, 2.0], 2)
        grid1 = _make_data_grid([3.0, 4.0], 2)
        mock_analysis = _make_analysis(
            "SeidelCoefficients", data_grids=[grid0, grid1]
        )
        conn.system.Analyses.New_Analysis.return_value = mock_analysis

        analysis = ZemaxAnalysis(conn)
        result = analysis.get_seidel_coefficients()
        assert result["raw_values"] == [1.0, 2.0, 3.0, 4.0]

    def test_exception_propagates(self):
        conn = _make_connection()
        conn.system.Analyses.New_Analysis.side_effect = RuntimeError("SEIDEL error")
        analysis = ZemaxAnalysis(conn)
        with pytest.raises(RuntimeError, match="SEIDEL error"):
            analysis.get_seidel_coefficients()


class TestGetZernikeCoefficients:
    def test_normal_call_returns_coefficients(self):
        conn = _make_connection()
        values = list(range(1, 38))
        grid = _make_data_grid(values, 37)
        mock_analysis = _make_analysis(
            "ZernikeStandardCoefficients", data_grids=[grid]
        )
        conn.system.Analyses.New_Analysis.return_value = mock_analysis

        analysis = ZemaxAnalysis(conn)
        result = analysis.get_zernike_coefficients(max_term=10)

        conn.system.Analyses.New_Analysis.assert_called_once_with(
            "ZernikeStandardCoefficients"
        )
        assert result["max_term"] == 10
        assert len(result["zernike_terms"]) == 10
        assert result["zernike_terms"][0] == {"term": 1, "coefficient": 1.0}
        assert result["zernike_terms"][9] == {"term": 10, "coefficient": 10.0}

    def test_truncates_to_max_term(self):
        conn = _make_connection()
        values = list(range(1, 50))
        grid = _make_data_grid(values, 49)
        mock_analysis = _make_analysis(
            "ZernikeStandardCoefficients", data_grids=[grid]
        )
        conn.system.Analyses.New_Analysis.return_value = mock_analysis

        analysis = ZemaxAnalysis(conn)
        result = analysis.get_zernike_coefficients(max_term=5)
        assert len(result["zernike_terms"]) == 5


class TestGetRayFan:
    def test_normal_call_returns_ray_fan_data(self):
        conn = _make_connection()
        py_ey = [0.01, 0.02, -0.01]
        px_ex = [0.005, -0.003, 0.0]
        grid0 = _make_data_grid(py_ey, 3)
        grid1 = _make_data_grid(px_ex, 3)
        mock_analysis = _make_analysis("RayFan", data_grids=[grid0, grid1])
        conn.system.Analyses.New_Analysis.return_value = mock_analysis

        analysis = ZemaxAnalysis(conn)
        result = analysis.get_ray_fan(field_number=1, wavelength_number=2)

        assert result["field_number"] == 1
        assert result["wavelength_number"] == 2
        assert result["py_ey"] == py_ey
        assert result["px_ex"] == px_ex


class TestGetSystemReport:
    def test_normal_call_returns_prescription_text(self):
        conn = _make_connection()
        mock_analysis = _make_analysis(
            "PrescriptionData",
            data_grids=[],
            text_output="System Prescription Data\nEFL: 100mm",
        )
        conn.system.Analyses.New_Analysis.return_value = mock_analysis

        analysis = ZemaxAnalysis(conn)
        result = analysis.get_system_report()

        assert result["prescription_text"] == "System Prescription Data\nEFL: 100mm"

    def test_none_text_output_returns_empty_string(self):
        conn = _make_connection()
        mock_analysis = _make_analysis(
            "PrescriptionData", data_grids=[], text_output=None
        )
        conn.system.Analyses.New_Analysis.return_value = mock_analysis

        analysis = ZemaxAnalysis(conn)
        result = analysis.get_system_report()
        assert result["prescription_text"] == ""


class TestGetAxialColor:
    def test_normal_call_returns_color_data(self):
        conn = _make_connection()
        grid = _make_data_grid([0.1, 0.2, 0.3], 3)
        mock_analysis = _make_analysis("AxialColor", data_grids=[grid])
        conn.system.Analyses.New_Analysis.return_value = mock_analysis

        analysis = ZemaxAnalysis(conn)
        result = analysis.get_axial_color()

        assert result["grid_0"] == [0.1, 0.2, 0.3]


class TestGetLateralColor:
    def test_normal_call_returns_color_data(self):
        conn = _make_connection()
        grid = _make_data_grid([0.01, 0.02], 2)
        mock_analysis = _make_analysis("LateralColor", data_grids=[grid])
        conn.system.Analyses.New_Analysis.return_value = mock_analysis

        analysis = ZemaxAnalysis(conn)
        result = analysis.get_lateral_color()

        assert result["grid_0"] == [0.01, 0.02]


class TestGetLayout:
    def test_2d_layout_returns_text(self):
        conn = _make_connection()
        mock_analysis = _make_analysis(
            "2DDLayout", data_grids=[], text_output="2D Layout"
        )
        conn.system.Analyses.New_Analysis.return_value = mock_analysis

        analysis = ZemaxAnalysis(conn)
        result = analysis.get_layout(layout_type="2D")

        conn.system.Analyses.New_Analysis.assert_called_once_with("2DDLayout")
        assert result == "2D Layout"

    def test_3d_layout_returns_text(self):
        conn = _make_connection()
        mock_analysis = _make_analysis(
            "3DDLayout", data_grids=[], text_output="3D Layout"
        )
        conn.system.Analyses.New_Analysis.return_value = mock_analysis

        analysis = ZemaxAnalysis(conn)
        result = analysis.get_layout(layout_type="3D")

        conn.system.Analyses.New_Analysis.assert_called_once_with("3DDLayout")
        assert result == "3D Layout"

    def test_default_layout_is_2d(self):
        conn = _make_connection()
        mock_analysis = _make_analysis(
            "2DDLayout", data_grids=[], text_output="Layout"
        )
        conn.system.Analyses.New_Analysis.return_value = mock_analysis

        analysis = ZemaxAnalysis(conn)
        analysis.get_layout()
        conn.system.Analyses.New_Analysis.assert_called_once_with("2DDLayout")
