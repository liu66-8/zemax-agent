from __future__ import annotations

import logging
from typing import Any, Optional

from zemax_agent.zos.connection import ZOSConnection
from zemax_agent.zos.models import OptimizationConfig, OptimizationResult

logger = logging.getLogger(__name__)


def build_merit_function(conn: ZOSConnection, operands: list[dict[str, Any]], clear_existing: bool = True) -> None:
    mfe = conn.mode_editor
    if clear_existing:
        mfe.RemoveOperands(1, mfe.NumberOfOperands)

    for i, op in enumerate(operands):
        op_type = op.get("type", "BLNK")
        op_row = mfe.AddOperand()
        mfe.GetOperandAt(op_row).ChangeType(op_type)

        if "target" in op:
            mfe.GetOperandAt(op_row).Target = float(op["target"])
        if "weight" in op:
            mfe.GetOperandAt(op_row).Weight = float(op["weight"])

        for param_idx, param_key in enumerate(["int1", "int2", "int3", "int4"]):
            if param_key in op:
                mfe.GetOperandAt(op_row).GetOperandCell(param_idx + 1).IntegerValue = int(op[param_key])


def set_variables(conn: ZOSConnection, variables: list[tuple[int, int]]) -> None:
    lde = conn.lens_data_editor
    for surf, param_code in variables:
        lde.GetSurfaceAt(surf).GetCellAt(param_code).MakeSolveVariable()


def clear_variables(conn: ZOSConnection, surface_indices: Optional[list[int]] = None) -> None:
    lde = conn.lens_data_editor
    if surface_indices is None:
        surface_indices = list(range(1, int(lde.NumberOfSurfaces)))
    for surf_idx in surface_indices:
        surf = lde.GetSurfaceAt(surf_idx)
        for param in [2, 3, 5, 6, 8, 9, 10, 11, 12, 13, 14]:
            try:
                surf.GetCellAt(param).MakeSolveFixed()
            except Exception:
                pass


def _do_optimize(conn: ZOSConnection, config: OptimizationConfig) -> tuple[bool, int]:
    tools = conn.tools
    opt = tools.OpenLocalOptimization()

    if config.algorithm == "OrthogonalDescent":
        opt.Algorithm = 1

    opt.Cycles = config.cycles
    opt.AutoScale = config.auto_scale
    opt.NumberOfCores = 4

    initial_mf = float(conn.mode_editor.GetMeritFunctionValue())
    opt.RunAndWaitForCompletion()
    final_mf = float(conn.mode_editor.GetMeritFunctionValue())

    opt.Close()
    converged = abs(final_mf - initial_mf) < config.convergence_threshold
    return converged, 0


def run_optimization(conn: ZOSConnection, config: OptimizationConfig) -> OptimizationResult:
    initial_mf = float(conn.mode_editor.GetMeritFunctionValue())
    converged, cycles = _do_optimize(conn, config)
    final_mf = float(conn.mode_editor.GetMeritFunctionValue())
    improvement = ((initial_mf - final_mf) / max(abs(initial_mf), 1e-10)) * 100

    return OptimizationResult(
        initial_mf=initial_mf,
        final_mf=final_mf,
        cycles_completed=config.cycles,
        converged=converged,
        improvement_percent=improvement,
    )


def run_hammer(conn: ZOSConnection) -> OptimizationResult:
    initial_mf = float(conn.mode_editor.GetMeritFunctionValue())
    tools = conn.tools
    hammer = tools.OpenGlobalSearch()
    hammer.RunAndWaitForCompletion()
    hammer.Close()
    final_mf = float(conn.mode_editor.GetMeritFunctionValue())
    improvement = ((initial_mf - final_mf) / max(abs(initial_mf), 1e-10)) * 100

    return OptimizationResult(
        initial_mf=initial_mf,
        final_mf=final_mf,
        converged=True,
        improvement_percent=improvement,
    )


def get_optimization_status(conn: ZOSConnection) -> dict[str, Any]:
    return {
        "merit_function": float(conn.mode_editor.GetMeritFunctionValue()),
        "operand_count": int(conn.mode_editor.NumberOfOperands),
    }
