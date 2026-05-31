from __future__ import annotations

import logging
from typing import Any

from zemax_agent.zos.connection import ZOSConnection
from zemax_agent.zos.models import ToleranceConfig, ToleranceResult

logger = logging.getLogger(__name__)


def set_default_tolerances(conn: ZOSConnection) -> None:
    tol = conn.tolerancing
    tol.SetDefaultTolerances()


def set_tolerance_operand(conn: ZOSConnection, operand_type: str, surface: int = 0, value: float = 0.0) -> None:
    tol = conn.tolerancing
    tol_data = tol.GetToleranceData()
    op = tol_data.AddOperand()
    op.ChangeType(operand_type)
    if surface > 0:
        try:
            op.SurfaceNumber = surface
        except Exception:
            pass
    if value != 0.0:
        try:
            op.Value = value
        except Exception:
            pass


def run_sensitivity(conn: ZOSConnection) -> ToleranceResult:
    tol = conn.tolerancing
    tol.RunSensitivityAnalysis()
    return ToleranceResult()


def run_monte_carlo(conn: ZOSConnection, sample_count: int = 500) -> ToleranceResult:
    tol = conn.tolerancing
    tol.MonteCarlo.SampleCount = sample_count
    tol.MonteCarlo.RunAndWaitForCompletion()
    return ToleranceResult()


def get_tolerance_results(conn: ZOSConnection) -> ToleranceResult:
    tol = conn.tolerancing
    try:
        tol_data = tol.GetToleranceData()
    except Exception:
        return ToleranceResult()
    return ToleranceResult()
