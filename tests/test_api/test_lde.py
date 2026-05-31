"""Tests for Zemax Lens Data Editor (LDE) operation interface."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from zemax_agent.api.connection import ZemaxConnection
from zemax_agent.api.lde import GlassCatalog, SurfaceType, ZemaxLDE


def _make_mock_connection() -> ZemaxConnection:
    conn = ZemaxConnection()
    conn.ensure_connected = MagicMock()
    conn._connected = True
    conn._zosapi_app = object()
    conn._the_system = MagicMock()
    return conn


def _make_mock_surface(**kwargs) -> MagicMock:
    surf = MagicMock()
    surf.Type = kwargs.get("Type", "Standard")
    surf.Comment = kwargs.get("Comment", "")
    surf.Radius = kwargs.get("Radius", 1e18)
    surf.Thickness = kwargs.get("Thickness", 10.0)
    surf.Material = kwargs.get("Material", "")
    surf.SemiDiameter = kwargs.get("SemiDiameter", 12.5)
    if "has_conic" not in kwargs or kwargs["has_conic"]:
        surf.Conic = kwargs.get("Conic", 0.0)
    else:
        del surf.Conic
    return surf


class TestZemaxLDEInit:
    def test_initialization_stores_connection(self):
        conn = _make_mock_connection()
        lde = ZemaxLDE(conn)
        assert lde._conn is conn

    def test_initialization_with_different_connections(self):
        conn1 = _make_mock_connection()
        conn2 = _make_mock_connection()
        lde1 = ZemaxLDE(conn1)
        lde2 = ZemaxLDE(conn2)
        assert lde1._conn is conn1
        assert lde2._conn is conn2
        assert lde1._conn is not lde2._conn


class TestSurfaceCount:
    def test_surface_count_returns_number_of_surfaces(self):
        conn = _make_mock_connection()
        conn.system.LDE.NumberOfSurfaces = 5
        lde = ZemaxLDE(conn)
        assert lde.surface_count == 5

    def test_surface_count_calls_ensure_connected(self):
        conn = _make_mock_connection()
        lde = ZemaxLDE(conn)
        lde.surface_count
        conn.ensure_connected.assert_called_once()


class TestGetSurfaceData:
    def test_returns_complete_surface_data(self):
        conn = _make_mock_connection()
        conn.system.LDE.NumberOfSurfaces = 3
        mock_surf = _make_mock_surface(
            Type="Standard",
            Comment="Objective",
            Radius=100.0,
            Thickness=10.0,
            Material="N-BK7",
            SemiDiameter=12.5,
            Conic=-0.5,
        )
        conn.system.LDE.GetSurfaceAt.return_value = mock_surf

        lde = ZemaxLDE(conn)
        data = lde.get_surface_data(1)

        assert data["surface_number"] == 1
        assert data["surface_type"] == "Standard"
        assert data["comment"] == "Objective"
        assert data["radius"] == 100.0
        assert data["thickness"] == 10.0
        assert data["glass"] == "N-BK7"
        assert data["semi_diameter"] == 12.5
        assert data["conic"] == -0.5

    def test_conic_defaults_to_zero_when_not_present(self):
        conn = _make_mock_connection()
        conn.system.LDE.NumberOfSurfaces = 3
        mock_surf = _make_mock_surface(has_conic=False)
        conn.system.LDE.GetSurfaceAt.return_value = mock_surf

        lde = ZemaxLDE(conn)
        data = lde.get_surface_data(1)

        assert data["conic"] == 0.0

    def test_raises_value_error_when_surface_num_too_low(self):
        conn = _make_mock_connection()
        conn.system.LDE.NumberOfSurfaces = 5
        lde = ZemaxLDE(conn)

        with pytest.raises(ValueError, match="面序号 0 超出范围"):
            lde.get_surface_data(0)

    def test_raises_value_error_when_surface_num_too_high(self):
        conn = _make_mock_connection()
        conn.system.LDE.NumberOfSurfaces = 5
        lde = ZemaxLDE(conn)

        with pytest.raises(ValueError, match="面序号 7 超出范围"):
            lde.get_surface_data(7)

    def test_boundary_surface_num_one_is_valid(self):
        conn = _make_mock_connection()
        conn.system.LDE.NumberOfSurfaces = 5
        mock_surf = _make_mock_surface()
        conn.system.LDE.GetSurfaceAt.return_value = mock_surf

        lde = ZemaxLDE(conn)
        data = lde.get_surface_data(1)

        assert data["surface_number"] == 1

    def test_boundary_surface_num_last_is_valid(self):
        conn = _make_mock_connection()
        conn.system.LDE.NumberOfSurfaces = 5
        mock_surf = _make_mock_surface()
        conn.system.LDE.GetSurfaceAt.return_value = mock_surf

        lde = ZemaxLDE(conn)
        data = lde.get_surface_data(5)

        assert data["surface_number"] == 5


class TestGetAllSurfaces:
    def test_returns_all_surfaces_in_order(self):
        conn = _make_mock_connection()
        conn.system.LDE.NumberOfSurfaces = 3

        def make_surf(num):
            s = _make_mock_surface(Comment=f"S{num}")
            return s

        conn.system.LDE.GetSurfaceAt.side_effect = [
            make_surf(1),
            make_surf(2),
            make_surf(3),
        ]

        lde = ZemaxLDE(conn)
        result = lde.get_all_surfaces()

        assert len(result) == 3
        assert result[0]["surface_number"] == 1
        assert result[0]["comment"] == "S1"
        assert result[1]["surface_number"] == 2
        assert result[2]["surface_number"] == 3


class TestSetThickness:
    def test_sets_thickness_on_valid_value(self):
        conn = _make_mock_connection()
        mock_surf = MagicMock()
        conn.system.LDE.GetSurfaceAt.return_value = mock_surf
        lde = ZemaxLDE(conn)

        lde.set_thickness(1, 15.0)

        assert mock_surf.Thickness == 15.0

    def test_raises_value_error_on_negative_thickness(self):
        conn = _make_mock_connection()
        lde = ZemaxLDE(conn)

        with pytest.raises(ValueError, match="厚度不能为负"):
            lde.set_thickness(1, -1.0)

    def test_zero_thickness_is_valid(self):
        conn = _make_mock_connection()
        mock_surf = MagicMock()
        conn.system.LDE.GetSurfaceAt.return_value = mock_surf
        lde = ZemaxLDE(conn)

        lde.set_thickness(1, 0.0)

        assert mock_surf.Thickness == 0.0


class TestSetSemiDiameter:
    def test_raises_value_error_on_negative_semi_diameter(self):
        conn = _make_mock_connection()
        lde = ZemaxLDE(conn)

        with pytest.raises(ValueError, match="半口径不能为负"):
            lde.set_semi_diameter(1, -0.1)

    def test_sets_semi_diameter_on_valid_value(self):
        conn = _make_mock_connection()
        mock_surf = MagicMock()
        conn.system.LDE.GetSurfaceAt.return_value = mock_surf
        lde = ZemaxLDE(conn)

        lde.set_semi_diameter(1, 25.0)

        assert mock_surf.SemiDiameter == 25.0

    def test_zero_semi_diameter_is_valid(self):
        conn = _make_mock_connection()
        mock_surf = MagicMock()
        conn.system.LDE.GetSurfaceAt.return_value = mock_surf
        lde = ZemaxLDE(conn)

        lde.set_semi_diameter(1, 0.0)

        assert mock_surf.SemiDiameter == 0.0


class TestDeleteSurface:
    def test_raises_value_error_when_only_two_surfaces(self):
        conn = _make_mock_connection()
        conn.system.LDE.NumberOfSurfaces = 2
        lde = ZemaxLDE(conn)

        with pytest.raises(ValueError, match="至少保留物面和像面"):
            lde.delete_surface(1)

    def test_raises_value_error_when_only_one_surface(self):
        conn = _make_mock_connection()
        conn.system.LDE.NumberOfSurfaces = 1
        lde = ZemaxLDE(conn)

        with pytest.raises(ValueError, match="至少保留物面和像面"):
            lde.delete_surface(1)

    def test_allows_delete_when_more_than_two_surfaces(self):
        conn = _make_mock_connection()
        conn.system.LDE.NumberOfSurfaces = 5
        lde = ZemaxLDE(conn)

        lde.delete_surface(2)

        conn.system.LDE.RemoveSurfaceAt.assert_called_once_with(2)


class TestSetConic:
    def test_raises_value_error_when_surface_type_does_not_support_conic(self):
        conn = _make_mock_connection()
        mock_surf = _make_mock_surface(has_conic=False, Type="Paraxial")
        conn.system.LDE.GetSurfaceAt.return_value = mock_surf
        lde = ZemaxLDE(conn)

        with pytest.raises(ValueError, match="不支持圆锥系数"):
            lde.set_conic(1, -0.5)

    def test_sets_conic_when_surface_type_supports_it(self):
        conn = _make_mock_connection()
        mock_surf = _make_mock_surface(Conic=0.0)
        conn.system.LDE.GetSurfaceAt.return_value = mock_surf
        lde = ZemaxLDE(conn)

        lde.set_conic(1, -1.5)

        assert mock_surf.Conic == -1.5


class TestGetStopSurface:
    def test_returns_stop_surface_number(self):
        conn = _make_mock_connection()
        conn.system.LDE.StopSurface = 3
        lde = ZemaxLDE(conn)

        result = lde.get_stop_surface()

        assert result == 3

    def test_calls_ensure_connected_before_getting_stop(self):
        conn = _make_mock_connection()
        conn.system.LDE.StopSurface = 2
        lde = ZemaxLDE(conn)

        lde.get_stop_surface()

        conn.ensure_connected.assert_called_once()


class TestSetStop:
    def test_makes_surface_stop(self):
        conn = _make_mock_connection()
        lde = ZemaxLDE(conn)

        lde.set_stop(3)

        conn.system.LDE.MakeSurfaceStop.assert_called_once_with(3)


class TestSurfaceTypeConstants:
    def test_standard_value(self):
        assert SurfaceType.STANDARD == "Standard"

    def test_even_asphere_value(self):
        assert SurfaceType.EVEN_ASPHERE == "EvenAsphere"

    def test_paraxial_value(self):
        assert SurfaceType.PARAXIAL == "Paraxial"

    def test_coordinate_break_value(self):
        assert SurfaceType.COORDINATE_BREAK == "CoordinateBreak"


class TestGlassCatalogConstants:
    def test_air_is_empty_string(self):
        assert GlassCatalog.AIR == ""

    def test_bk7_value(self):
        assert GlassCatalog.BK7 == "N-BK7"

    def test_f2_value(self):
        assert GlassCatalog.F2 == "N-F2"

    def test_sf2_value(self):
        assert GlassCatalog.SF2 == "N-SF2"
