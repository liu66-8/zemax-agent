from __future__ import annotations

import logging
import time
from typing import Any, Callable, Dict, List

logger = logging.getLogger(__name__)


class MeritOperand:
    def __init__(
        self,
        operand_type: str,
        target: float,
        weight: float,
        surface1: int = 0,
        surface2: int = 0,
        value1: float = 0.0,
        value2: float = 0.0,
    ):
        self.operand_type = operand_type
        self.target = target
        self.weight = weight
        self.surface1 = surface1
        self.surface2 = surface2
        self.value1 = value1
        self.value2 = value2


class ZemaxOptimizer:
    def __init__(self, connection: Any):
        self._conn = connection
        self._optimizing = False
        self._progress_callbacks: List[Callable[[float], None]] = []

    @property
    def _system(self) -> Any:
        return self._conn.system

    @property
    def _tool(self) -> Any:
        return self._system.Tools

    def clear_merit_function(self) -> None:
        self._conn.ensure_connected()
        mfe = self._system.MFE
        mfe.RemoveOperands(1, mfe.NumberOfOperands)
        logger.info("评价函数已清空")

    def get_merit_function_value(self) -> float:
        self._conn.ensure_connected()
        return float(self._system.MFE.MeritFunctionValue)

    def get_merit_function_operands(self) -> List[Dict[str, Any]]:
        self._conn.ensure_connected()
        mfe = self._system.MFE
        operands = []
        for i in range(1, mfe.NumberOfOperands + 1):
            op = mfe.GetOperandAt(i)
            operands.append(
                {
                    "index": i,
                    "type": str(op.Type),
                    "target": float(op.Target),
                    "weight": float(op.Weight),
                    "value": float(op.Value),
                    "contribution": float(op.Contribution),
                }
            )
        return operands

    def add_operand(
        self,
        operand_type: str,
        target: float,
        weight: float = 1.0,
        surface1: int = 0,
        surface2: int = 0,
        value1: float = 0.0,
        value2: float = 0.0,
    ) -> None:
        self._conn.ensure_connected()
        mfe = self._system.MFE
        num = mfe.NumberOfOperands + 1
        mfe.AddOperand()
        op = mfe.GetOperandAt(num)
        op.ChangeType(operand_type)
        op.Target = target
        op.Weight = weight
        op.Surface = surface1
        op.Surface2 = surface2
        if value1 != 0.0:
            op.Value1 = value1
        if value2 != 0.0:
            op.Value2 = value2
        logger.debug(f"操作数 {operand_type} 已添加 (target={target}, weight={weight})")

    def set_variable(self, surface_num: int, parameter: str) -> None:
        self._conn.ensure_connected()
        surf = self._system.LDE.GetSurfaceAt(surface_num)
        param_map = {
            "radius": surf.RadiusCell,
            "thickness": surf.ThicknessCell,
            "conic": surf.ConicCell if hasattr(surf, "ConicCell") else None,
            "glass": surf.MaterialCell,
        }
        cell = param_map.get(parameter.lower())
        if cell is None:
            raise ValueError(f"不支持变量参数: {parameter}")

        solve = cell.CreateSolveType("Variable")
        cell.SetSolveData(solve)
        logger.info(f"面 {surface_num} 参数 '{parameter}' 已设为变量")

    def remove_variable(self, surface_num: int, parameter: str) -> None:
        self._conn.ensure_connected()
        surf = self._system.LDE.GetSurfaceAt(surface_num)
        param_map = {
            "radius": surf.RadiusCell,
            "thickness": surf.ThicknessCell,
            "conic": surf.ConicCell if hasattr(surf, "ConicCell") else None,
            "glass": surf.MaterialCell,
        }
        cell = param_map.get(parameter.lower())
        if cell is None:
            raise ValueError(f"不支持变量参数: {parameter}")

        solve = cell.CreateSolveType("Fixed")
        cell.SetSolveData(solve)
        logger.info(f"面 {surface_num} 参数 '{parameter}' 变量已移除")

    def remove_all_variables(self) -> None:
        self._conn.ensure_connected()
        self._system.LDE.RemoveVariables()
        logger.info("所有变量已移除")

    def set_variables_by_pattern(self, pattern: str = "radius_thickness") -> List[str]:
        self._conn.ensure_connected()
        variables = []
        surf_count = self._system.LDE.NumberOfSurfaces

        for i in range(1, surf_count):
            surf = self._system.LDE.GetSurfaceAt(i)

            if pattern in ("radius_thickness", "radius", "all"):
                try:
                    solve = surf.RadiusCell.CreateSolveType("Variable")
                    surf.RadiusCell.SetSolveData(solve)
                    variables.append(f"surface_{i}_radius")
                except Exception:
                    pass

            if pattern in ("radius_thickness", "thickness", "all"):
                try:
                    solve = surf.ThicknessCell.CreateSolveType("Variable")
                    surf.ThicknessCell.SetSolveData(solve)
                    variables.append(f"surface_{i}_thickness")
                except Exception:
                    pass

            if pattern == "all":
                try:
                    if hasattr(surf, "ConicCell"):
                        solve = surf.ConicCell.CreateSolveType("Variable")
                        surf.ConicCell.SetSolveData(solve)
                        variables.append(f"surface_{i}_conic")
                except Exception:
                    pass

        logger.info(f"已设置 {len(variables)} 个变量 (模式: {pattern})")
        return variables

    def optimize(
        self, max_cycles: int = 50, algorithm: str = "DLS"
    ) -> Dict[str, Any]:
        self._conn.ensure_connected()
        start_mf = self.get_merit_function_value()
        start_time = time.time()

        logger.info(f"开始优化 (算法={algorithm}, 最大循环={max_cycles})")
        logger.info(f"起始评价函数值: {start_mf:.6f}")

        try:
            opt = self._tool.OpenLocalOptimization()
            opt.Algorithm = algorithm
            opt.NumberOfCores = 8
            opt.Cycles = max_cycles

            self._optimizing = True
            opt.RunAndWaitForCompletion()
            self._optimizing = False

            end_mf = self.get_merit_function_value()
            elapsed = time.time() - start_time

            opt.Close()

            result = {
                "success": True,
                "start_merit": float(start_mf),
                "end_merit": float(end_mf),
                "improvement": float(start_mf - end_mf),
                "cycles": max_cycles,
                "elapsed_seconds": elapsed,
            }

            logger.info(
                f"优化完成: MF {start_mf:.6f} → {end_mf:.6f} "
                f"(改善 {result['improvement']:.6f}, {elapsed:.1f}s)"
            )
            return result

        except Exception as e:
            self._optimizing = False
            logger.error(f"优化失败: {e}")
            raise

    def hammer_optimize(self, max_cycles: int = 10) -> Dict[str, Any]:
        self._conn.ensure_connected()
        start_mf = self.get_merit_function_value()
        start_time = time.time()

        logger.info(f"开始锤形优化 (迭代次数={max_cycles})")
        logger.info(f"起始评价函数值: {start_mf:.6f}")

        try:
            hammer = self._tool.OpenHammerOptimization()
            hammer.NumberOfCores = 8
            hammer.Cycles = max_cycles

            self._optimizing = True
            hammer.RunAndWaitForCompletion()
            self._optimizing = False

            end_mf = self.get_merit_function_value()
            elapsed = time.time() - start_time

            hammer.Close()

            result = {
                "success": True,
                "start_merit": float(start_mf),
                "end_merit": float(end_mf),
                "improvement": float(start_mf - end_mf),
                "cycles": max_cycles,
                "elapsed_seconds": elapsed,
            }

            logger.info(
                f"锤形优化完成: MF {start_mf:.6f} → {end_mf:.6f} "
                f"(改善 {result['improvement']:.6f}, {elapsed:.1f}s)"
            )
            return result

        except Exception as e:
            self._optimizing = False
            logger.error(f"锤形优化失败: {e}")
            raise

    def stop_optimization(self) -> None:
        if self._optimizing:
            try:
                self._tool.EndLocalOptimization()
                self._optimizing = False
                logger.info("优化已手动停止")
            except Exception as e:
                logger.warning(f"停止优化时出现异常: {e}")

    def is_optimizing(self) -> bool:
        return self._optimizing

    def build_default_merit_function(
        self,
        data_type: str = "RMS",
        reference: str = "Centroid",
        pupil_integration: str = "GaussianQuadrature",
        rings: int = 6,
        arms: int = 8,
    ) -> None:
        self._conn.ensure_connected()
        self.clear_merit_function()

        mfe = self._system.MFE
        dmf = mfe.CreateDefaultMeritFunction()
        dmf.DataType = data_type
        dmf.Reference = reference
        dmf.PupilIntegrationMethod = pupil_integration
        dmf.Rings = rings
        dmf.Arms = arms
        dmf.OK()

        logger.info(
            f"默认评价函数已构建 (type={data_type}, rings={rings}, arms={arms})"
        )

    def add_boundary_constraints(
        self,
        min_center_thickness: float = 1.0,
        min_edge_thickness: float = 0.5,
        min_air_gap: float = 0.1,
        max_glass_thickness: float = 20.0,
    ) -> None:
        self._conn.ensure_connected()

        constraints = [
            ("MNCT", min_center_thickness, 1.0),
            ("MNET", min_edge_thickness, 1.0),
            ("MNEA", min_air_gap, 1.0),
            ("MXCT", max_glass_thickness, 0.1),
        ]

        for operand_type, target, weight in constraints:
            self.add_operand(operand_type, target, weight)

        logger.info(
            f"边界条件约束已添加: min_CT={min_center_thickness}, "
            f"min_ET={min_edge_thickness}, min_AG={min_air_gap}"
        )

    def add_focal_length_constraint(
        self, focal_length: float, weight: float = 1.0
    ) -> None:
        self._conn.ensure_connected()
        self.add_operand("EFFL", focal_length, weight)
        logger.info(f"焦距约束已添加: EFFL={focal_length}mm, weight={weight}")

    def add_aberration_operands(self) -> None:
        self._conn.ensure_connected()

        aberrations = [
            ("SPHA", 0.0, 1.0),
            ("COMA", 0.0, 1.0),
            ("ASTI", 0.0, 1.0),
            ("FCUR", 0.0, 1.0),
            ("DIST", 0.0, 1.0),
        ]

        for op_type, target, weight in aberrations:
            self.add_operand(op_type, target, weight)

        logger.info("像差校正操作数已添加")
