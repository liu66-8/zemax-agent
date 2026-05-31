"""Tests for Zemax system settings operation interface."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from zemax_agent.api.system_settings import ApertureType, FieldType, ZemaxSystemSettings


class TestApertureValidation:
    def test_set_aperture_raises_on_non_positive_value(self):
        conn = MagicMock()
        settings = ZemaxSystemSettings(conn)

        with pytest.raises(ValueError, match="孔径值必须大于0"):
            settings.set_aperture(ApertureType.ENTRANCE_PUPIL_DIAMETER, -1.0)

        with pytest.raises(ValueError, match="孔径值必须大于0"):
            settings.set_aperture(ApertureType.IMAGE_SPACE_F_NUMBER, 0.0)

    def test_set_aperture_normal_call(self):
        conn = MagicMock()
        settings = ZemaxSystemSettings(conn)

        settings.set_aperture(ApertureType.ENTRANCE_PUPIL_DIAMETER, 25.0)

        conn.ensure_connected.assert_called_once()
        sd = settings._sys_data
        sd.Aperture.ApertureValue = 25.0
        assert sd.Aperture.ApertureValue == 25.0


class TestFieldValidation:
    def test_set_field_count_at_least_1(self):
        conn = MagicMock()
        settings = ZemaxSystemSettings(conn)

        with pytest.raises(ValueError, match="视场数量至少为1"):
            settings.set_field_count(0)

        with pytest.raises(ValueError, match="视场数量至少为1"):
            settings.set_field_count(-1)

    def test_set_field_number_range_validation(self):
        conn = MagicMock()
        settings = ZemaxSystemSettings(conn)
        settings._sys_data.Fields.NumberOfFields = 3

        with pytest.raises(ValueError, match="视场序号 0 超出范围"):
            settings.set_field(0, FieldType.ANGLE, 0.0, 0.0)

        with pytest.raises(ValueError, match="视场序号 5 超出范围"):
            settings.set_field(5, FieldType.ANGLE, 0.0, 10.0)


class TestWavelengthValidation:
    def test_set_wavelength_positive_validation(self):
        conn = MagicMock()
        settings = ZemaxSystemSettings(conn)

        with pytest.raises(ValueError, match="波长必须大于0"):
            settings.set_wavelength(1, -0.5, 1.0)

        with pytest.raises(ValueError, match="波长必须大于0"):
            settings.set_wavelength(1, 0.0, 1.0)

    def test_set_wavelength_number_range_validation(self):
        conn = MagicMock()
        settings = ZemaxSystemSettings(conn)
        settings._sys_data.Wavelengths.NumberOfWavelengths = 2

        with pytest.raises(ValueError, match="波长序号 0 超出范围"):
            settings.set_wavelength(0, 0.55, 1.0)

        with pytest.raises(ValueError, match="波长序号 3 超出范围"):
            settings.set_wavelength(3, 0.55, 1.0)


class TestStandardFields:
    def test_setup_standard_fields_3_fields_parameters_correct(self):
        conn = MagicMock()
        settings = ZemaxSystemSettings(conn)

        field_mocks = [MagicMock() for _ in range(3)]
        settings._sys_data.Fields.GetField.side_effect = field_mocks

        settings.setup_standard_fields(max_field=10.0, field_type=FieldType.ANGLE, num_fields=3)

        assert settings._sys_data.Fields.NumberOfFields == 3

        assert field_mocks[0].FieldType == FieldType.ANGLE
        assert field_mocks[0].XField == 0.0
        assert field_mocks[0].YField == 0.0

        assert field_mocks[1].FieldType == FieldType.ANGLE
        assert field_mocks[1].XField == 0.0
        assert field_mocks[1].YField == pytest.approx(7.07, abs=0.01)

        assert field_mocks[2].FieldType == FieldType.ANGLE
        assert field_mocks[2].XField == 0.0
        assert field_mocks[2].YField == 10.0


class TestVisibleWavelengths:
    def test_setup_visible_wavelengths_count_is_3(self):
        conn = MagicMock()
        settings = ZemaxSystemSettings(conn)

        wl_mocks = [MagicMock() for _ in range(3)]
        settings._sys_data.Wavelengths.GetWavelength.side_effect = wl_mocks

        settings.setup_visible_wavelengths()

        assert settings._sys_data.Wavelengths.NumberOfWavelengths == 3

        assert wl_mocks[0].Wavelength == 0.4861
        assert wl_mocks[0].Weight == 1.0

        assert wl_mocks[1].Wavelength == 0.5876
        assert wl_mocks[1].Weight == 1.0

        assert wl_mocks[2].Wavelength == 0.6563
        assert wl_mocks[2].Weight == 1.0

        assert settings._sys_data.Wavelengths.PrimaryWavelength == 2

    def test_setup_visible_wavelengths_custom_primary(self):
        conn = MagicMock()
        settings = ZemaxSystemSettings(conn)

        wl_mocks = [MagicMock() for _ in range(3)]
        settings._sys_data.Wavelengths.GetWavelength.side_effect = wl_mocks

        settings.setup_visible_wavelengths(primary=0.55)

        assert wl_mocks[1].Wavelength == 0.55

    def test_set_wavelength_count_validation(self):
        conn = MagicMock()
        settings = ZemaxSystemSettings(conn)

        with pytest.raises(ValueError, match="波长数量至少为1"):
            settings.set_wavelength_count(0)

    def test_get_aperture_returns_expected_keys(self):
        conn = MagicMock()
        settings = ZemaxSystemSettings(conn)

        result = settings.get_aperture()

        assert "aperture_type" in result
        assert "aperture_value" in result
        assert "entrance_pupil_diameter" in result
        assert "image_space_f_number" in result

    def test_set_aperture_convenience_methods(self):
        conn = MagicMock()
        settings = ZemaxSystemSettings(conn)

        settings.set_entrance_pupil_diameter(50.0)
        settings.set_f_number(4.0)
        settings.set_object_na(0.3)

        conn.ensure_connected.call_count == 3
