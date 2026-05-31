from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from zemax_agent.api.optimization import MeritOperand, ZemaxOptimizer


def _create_mock_connection() -> MagicMock:
    conn = MagicMock()
    conn.ensure_connected = MagicMock()

    mfe = MagicMock()
    mfe.NumberOfOperands = 3
    mfe.MeritFunctionValue = 0.5

    mock_operand = MagicMock()
    mock_operand.Type = "EFFL"
    mock_operand.Target = 100.0
    mock_operand.Weight = 1.0
    mock_operand.Value = 100.5
    mock_operand.Contribution = 0.25
    mfe.GetOperandAt = MagicMock(return_value=mock_operand)

    lde = MagicMock()
    lde.NumberOfSurfaces = 5

    mock_surf = MagicMock()
    mock_surf.RadiusCell = MagicMock()
    mock_surf.ThicknessCell = MagicMock()
    mock_surf.MaterialCell = MagicMock()

    radius_solve = MagicMock()
    mock_surf.RadiusCell.CreateSolveType = MagicMock(return_value=radius_solve)
    thickness_solve = MagicMock()
    mock_surf.ThicknessCell.CreateSolveType = MagicMock(return_value=thickness_solve)
    material_solve = MagicMock()
    mock_surf.MaterialCell.CreateSolveType = MagicMock(return_value=material_solve)

    lde.GetSurfaceAt = MagicMock(return_value=mock_surf)

    local_opt = MagicMock()
    hammer_opt = MagicMock()
    tools = MagicMock()
    tools.OpenLocalOptimization = MagicMock(return_value=local_opt)
    tools.OpenHammerOptimization = MagicMock(return_value=hammer_opt)

    system = MagicMock()
    system.MFE = mfe
    system.LDE = lde
    system.Tools = tools

    conn.system = system
    return conn


class TestMeritOperand:
    def test_default_values(self) -> None:
        op = MeritOperand("EFFL", 100.0, 1.0)
        assert op.operand_type == "EFFL"
        assert op.target == 100.0
        assert op.weight == 1.0
        assert op.surface1 == 0
        assert op.surface2 == 0
        assert op.value1 == 0.0
        assert op.value2 == 0.0

    def test_full_values(self) -> None:
        op = MeritOperand("SPHA", 0.0, 2.0, surface1=1, surface2=2, value1=0.5, value2=1.5)
        assert op.operand_type == "SPHA"
        assert op.target == 0.0
        assert op.weight == 2.0
        assert op.surface1 == 1
        assert op.surface2 == 2
        assert op.value1 == 0.5
        assert op.value2 == 1.5


class TestZemaxOptimizerInit:
    def test_initial_state(self) -> None:
        conn = _create_mock_connection()
        optimizer = ZemaxOptimizer(conn)
        assert optimizer._conn is conn
        assert optimizer._optimizing is False
        assert optimizer._progress_callbacks == []

    def test_is_optimizing_default_false(self) -> None:
        conn = _create_mock_connection()
        optimizer = ZemaxOptimizer(conn)
        assert optimizer.is_optimizing() is False


class TestSetVariable:
    def test_set_variable_unsupported_parameter_raises_value_error(self) -> None:
        conn = _create_mock_connection()
        optimizer = ZemaxOptimizer(conn)
        with pytest.raises(ValueError, match="不支持变量参数"):
            optimizer.set_variable(1, "invalid_param")

    def test_set_variable_normal_call(self) -> None:
        conn = _create_mock_connection()
        optimizer = ZemaxOptimizer(conn)
        optimizer.set_variable(2, "radius")
        conn.ensure_connected.assert_called_once()
        surf = conn.system.LDE.GetSurfaceAt(2)
        surf.RadiusCell.CreateSolveType.assert_called_once_with("Variable")
        surf.RadiusCell.SetSolveData.assert_called_once()

    def test_set_variable_thickness(self) -> None:
        conn = _create_mock_connection()
        optimizer = ZemaxOptimizer(conn)
        optimizer.set_variable(3, "thickness")
        conn.ensure_connected.assert_called_once()
        surf = conn.system.LDE.GetSurfaceAt(3)
        surf.ThicknessCell.CreateSolveType.assert_called_once_with("Variable")

    def test_set_variable_case_insensitive(self) -> None:
        conn = _create_mock_connection()
        optimizer = ZemaxOptimizer(conn)
        optimizer.set_variable(1, "RADIUS")
        conn.ensure_connected.assert_called_once()
        surf = conn.system.LDE.GetSurfaceAt(1)
        surf.RadiusCell.CreateSolveType.assert_called_once_with("Variable")


class TestRemoveVariable:
    def test_remove_variable_normal_call(self) -> None:
        conn = _create_mock_connection()
        optimizer = ZemaxOptimizer(conn)
        optimizer.remove_variable(2, "radius")
        conn.ensure_connected.assert_called_once()
        surf = conn.system.LDE.GetSurfaceAt(2)
        surf.RadiusCell.CreateSolveType.assert_called_once_with("Fixed")
        surf.RadiusCell.SetSolveData.assert_called_once()

    def test_remove_variable_unsupported_parameter_raises_value_error(self) -> None:
        conn = _create_mock_connection()
        optimizer = ZemaxOptimizer(conn)
        with pytest.raises(ValueError, match="不支持变量参数"):
            optimizer.remove_variable(1, "bad_param")

    def test_remove_all_variables(self) -> None:
        conn = _create_mock_connection()
        optimizer = ZemaxOptimizer(conn)
        optimizer.remove_all_variables()
        conn.ensure_connected.assert_called_once()
        conn.system.LDE.RemoveVariables.assert_called_once()


class TestOptimize:
    def test_optimize_normal_call_and_result_structure(self) -> None:
        conn = _create_mock_connection()
        optimizer = ZemaxOptimizer(conn)
        result = optimizer.optimize(max_cycles=20, algorithm="DLS")

        conn.ensure_connected.assert_called()
        tools = conn.system.Tools
        tools.OpenLocalOptimization.assert_called_once()

        assert isinstance(result, dict)
        assert result["success"] is True
        assert "start_merit" in result
        assert "end_merit" in result
        assert "improvement" in result
        assert "cycles" in result
        assert result["cycles"] == 20
        assert "elapsed_seconds" in result
        assert isinstance(result["elapsed_seconds"], float)

    def test_optimize_resets_optimizing_flag_on_exception(self) -> None:
        conn = _create_mock_connection()
        tools = conn.system.Tools
        opt_mock = MagicMock()
        opt_mock.RunAndWaitForCompletion = MagicMock(side_effect=RuntimeError("opt failed"))
        tools.OpenLocalOptimization = MagicMock(return_value=opt_mock)

        optimizer = ZemaxOptimizer(conn)
        with pytest.raises(RuntimeError, match="opt failed"):
            optimizer.optimize()
        assert optimizer._optimizing is False


class TestHammerOptimize:
    def test_hammer_optimize_normal_call_and_result_structure(self) -> None:
        conn = _create_mock_connection()
        optimizer = ZemaxOptimizer(conn)
        result = optimizer.hammer_optimize(max_cycles=5)

        conn.ensure_connected.assert_called()
        tools = conn.system.Tools
        tools.OpenHammerOptimization.assert_called_once()

        assert isinstance(result, dict)
        assert result["success"] is True
        assert "start_merit" in result
        assert "end_merit" in result
        assert "improvement" in result
        assert "cycles" in result
        assert result["cycles"] == 5
        assert "elapsed_seconds" in result


class TestBuildDefaultMeritFunction:
    def test_build_default_merit_function_normal_call(self) -> None:
        conn = _create_mock_connection()
        optimizer = ZemaxOptimizer(conn)
        optimizer.build_default_merit_function(
            data_type="PTV",
            reference="ChiefRay",
            rings=8,
            arms=10,
        )

        conn.ensure_connected.assert_called()
        mfe = conn.system.MFE

        mfe.RemoveOperands.assert_called_once_with(1, 3)

        dmf = mfe.CreateDefaultMeritFunction.return_value
        assert dmf.DataType == "PTV"
        assert dmf.Reference == "ChiefRay"
        assert dmf.PupilIntegrationMethod == "GaussianQuadrature"
        assert dmf.Rings == 8
        assert dmf.Arms == 10
        dmf.OK.assert_called_once()


class TestAddAberrationOperands:
    def test_add_aberration_operands_normal_call(self) -> None:
        conn = _create_mock_connection()
        optimizer = ZemaxOptimizer(conn)

        optimizer.add_aberration_operands()

        mfe = conn.system.MFE
        assert mfe.AddOperand.call_count == 5
        assert mfe.GetOperandAt.return_value.ChangeType.call_count == 5

    def test_add_aberration_operands_adds_correct_types(self) -> None:
        conn = _create_mock_connection()
        optimizer = ZemaxOptimizer(conn)

        optimizer.add_aberration_operands()

        change_type_calls = []
        for call_args in conn.system.MFE.GetOperandAt.return_value.ChangeType.call_args_list:
            change_type_calls.append(call_args[0][0])

        assert "SPHA" in change_type_calls
        assert "COMA" in change_type_calls
        assert "ASTI" in change_type_calls
        assert "FCUR" in change_type_calls
        assert "DIST" in change_type_calls
