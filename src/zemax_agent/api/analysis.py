import logging
from typing import Any, Dict

import numpy as np

from .connection import ZemaxConnection

logger = logging.getLogger(__name__)


class ZemaxAnalysis:
    """Zemax 光学分析接口"""

    def __init__(self, connection: ZemaxConnection):
        self._conn = connection

    @property
    def _system(self):
        return self._conn.system

    @property
    def _analyses(self):
        return self._system.Analyses

    def get_mtf(self, max_frequency: float = 50.0) -> Dict[str, Any]:
        """获取 MTF 数据

        Args:
            max_frequency: 最大空间频率 (lp/mm)
        Returns:
            包含频率和MTF值的字典
        """
        self._conn.ensure_connected()
        try:
            mtf = self._analyses.New_Analysis("Mtf")
            mtf.Settings.MaximumFrequency = max_frequency
            mtf.ApplyAndWaitForCompletion()
            results = mtf.GetResults()

            data: Dict[str, Any] = {
                "frequency": [],
                "tangential_mtf": [],
                "sagittal_mtf": [],
                "diffraction_limit": [],
                "max_frequency": max_frequency,
            }

            data_grid = results.DataGrids[0]
            if data_grid is not None:
                values = np.array(list(data_grid.Values), dtype=float)
                data["values"] = values.tolist()
                data["number_of_points"] = data_grid.NumberOfPoints
            else:
                data["number_of_points"] = 0

            mtf.Close()
            logger.info(f"MTF 分析完成 (max_freq={max_frequency} lp/mm)")
            return data
        except Exception as e:
            logger.error(f"MTF 分析失败: {e}")
            raise

    def get_spot_diagram(self) -> Dict[str, Any]:
        """获取点列图数据

        Returns:
            包含各视场 RMS/GEO 半径和 Airy 斑半径的字典
        """
        self._conn.ensure_connected()
        try:
            spot = self._analyses.New_Analysis("SpotDiagram")
            spot.ApplyAndWaitForCompletion()
            results = spot.GetResults()

            data: Dict[str, Any] = {
                "fields": [],
                "rms_radius": [],
                "geo_radius": [],
                "airy_radius": None,
            }

            data_grid = results.DataGrids[0]
            if data_grid is not None:
                values = np.array(list(data_grid.Values), dtype=float)
                n_points = data_grid.NumberOfPoints
                n_fields = n_points // 4 if n_points % 4 == 0 else 0
                for i in range(n_fields):
                    idx = i * 4
                    if idx + 3 < n_points:
                        data["fields"].append(i + 1)
                        data["rms_radius"].append(float(values[idx + 1]))
                        data["geo_radius"].append(float(values[idx + 2]))
                if hasattr(data_grid, "AiryDiameter"):
                    data["airy_radius"] = float(data_grid.AiryDiameter) / 2.0

            spot.Close()
            logger.info("点列图分析完成")
            return data
        except Exception as e:
            logger.error(f"点列图分析失败: {e}")
            raise

    def get_field_curvature_distortion(self) -> Dict[str, Any]:
        """获取场曲和畸变数据

        Returns:
            包含场曲曲线和畸变曲线数据的字典
        """
        self._conn.ensure_connected()
        try:
            fcd = self._analyses.New_Analysis("FieldCurvatureDistortion")
            fcd.ApplyAndWaitForCompletion()
            results = fcd.GetResults()

            data: Dict[str, Any] = {"field_curvature": {}, "distortion": {}}

            for i, grid in enumerate(results.DataGrids):
                if grid is not None:
                    values = np.array(list(grid.Values), dtype=float)
                    name = "field_curvature" if i == 0 else "distortion"
                    data[name] = {
                        "values": values.tolist(),
                        "number_of_points": grid.NumberOfPoints,
                    }

            fcd.Close()
            logger.info("场曲畸变分析完成")
            return data
        except Exception as e:
            logger.error(f"场曲畸变分析失败: {e}")
            raise

    def get_wavefront(
        self, field_number: int = 1, wavelength_number: int = 1
    ) -> Dict[str, Any]:
        """获取波前分析数据

        Args:
            field_number: 视场序号
            wavelength_number: 波长序号
        Returns:
            包含波前 RMS 和 PV 值的字典
        """
        self._conn.ensure_connected()
        try:
            wf = self._analyses.New_Analysis("WavefrontMap")
            wf.Settings.Field.SetFieldNumber(field_number)
            wf.Settings.Wavelength.SetWavelengthNumber(wavelength_number)
            wf.ApplyAndWaitForCompletion()
            results = wf.GetResults()

            data: Dict[str, Any] = {
                "rms_wavefront": 0.0,
                "pv_wavefront": 0.0,
                "field_number": field_number,
                "wavelength_number": wavelength_number,
            }

            data_grid = results.DataGrids[0]
            if data_grid is not None:
                values = np.array(list(data_grid.Values), dtype=float)
                data["values"] = values.tolist()
                if values.size > 0:
                    data["rms_wavefront"] = float(np.sqrt(np.mean(values**2)))
                    data["pv_wavefront"] = float(np.max(values) - np.min(values))

            wf.Close()
            logger.info(f"波前分析完成 (field={field_number}, wl={wavelength_number})")
            return data
        except Exception as e:
            logger.error(f"波前分析失败: {e}")
            raise

    def get_zernike_coefficients(
        self,
        field_number: int = 1,
        wavelength_number: int = 1,
        max_term: int = 37,
    ) -> Dict[str, Any]:
        """获取 Zernike 系数

        Args:
            field_number: 视场序号
            wavelength_number: 波长序号
            max_term: 最大 Zernike 项数（默认37）
        Returns:
            包含 Zernike 系数的字典
        """
        self._conn.ensure_connected()
        try:
            zern = self._analyses.New_Analysis("ZernikeStandardCoefficients")
            zern.Settings.Field.SetFieldNumber(field_number)
            zern.Settings.Wavelength.SetWavelengthNumber(wavelength_number)
            zern.Settings.MaximumTerm = max_term
            zern.ApplyAndWaitForCompletion()
            results = zern.GetResults()

            data: Dict[str, Any] = {"zernike_terms": [], "max_term": max_term}

            data_grid = results.DataGrids[0]
            if data_grid is not None:
                values = np.array(list(data_grid.Values), dtype=float)
                for i, val in enumerate(values):
                    if i < max_term:
                        data["zernike_terms"].append(
                            {
                                "term": i + 1,
                                "coefficient": float(val),
                            }
                        )

            zern.Close()
            logger.info(f"Zernike 系数分析完成 (max_term={max_term})")
            return data
        except Exception as e:
            logger.error(f"Zernike 系数分析失败: {e}")
            raise

    def get_seidel_coefficients(self) -> Dict[str, Any]:
        """获取赛德尔像差系数

        Returns:
            包含各赛德尔像差系数的字典
        """
        self._conn.ensure_connected()
        try:
            seidel = self._analyses.New_Analysis("SeidelCoefficients")
            seidel.ApplyAndWaitForCompletion()
            results = seidel.GetResults()

            data: Dict[str, Any] = {"raw_values": []}
            for grid in results.DataGrids:
                if grid is not None:
                    values = np.array(list(grid.Values), dtype=float)
                    data["raw_values"].extend(values.tolist())

            seidel.Close()
            logger.info("赛德尔系数分析完成")
            return data
        except Exception as e:
            logger.error(f"赛德尔系数分析失败: {e}")
            raise

    def get_ray_fan(
        self, field_number: int = 1, wavelength_number: int = 1
    ) -> Dict[str, Any]:
        """获取光线扇图数据

        Args:
            field_number: 视场序号
            wavelength_number: 波长序号
        Returns:
            包含光线扇数据的字典
        """
        self._conn.ensure_connected()
        try:
            rf = self._analyses.New_Analysis("RayFan")
            rf.Settings.Field.SetFieldNumber(field_number)
            rf.Settings.Wavelength.SetWavelengthNumber(wavelength_number)
            rf.ApplyAndWaitForCompletion()
            results = rf.GetResults()

            data: Dict[str, Any] = {
                "field_number": field_number,
                "wavelength_number": wavelength_number,
            }

            for i, grid in enumerate(results.DataGrids):
                if grid is not None:
                    values = np.array(list(grid.Values), dtype=float)
                    key = "py_ey" if i == 0 else "px_ex"
                    data[key] = values.tolist()

            rf.Close()
            logger.info(
                f"光线扇图分析完成 (field={field_number}, wl={wavelength_number})"
            )
            return data
        except Exception as e:
            logger.error(f"光线扇图分析失败: {e}")
            raise

    def get_system_report(self) -> Dict[str, Any]:
        """获取系统综合报告（处方数据）"""
        self._conn.ensure_connected()
        try:
            pres = self._analyses.New_Analysis("PrescriptionData")
            pres.ApplyAndWaitForCompletion()
            results = pres.GetResults()

            data: Dict[str, Any] = {"prescription_text": ""}
            text_output = results.GetTextOutput()
            if text_output is not None:
                data["prescription_text"] = str(text_output)

            pres.Close()
            logger.info("系统处方报告生成完成")
            return data
        except Exception as e:
            logger.error(f"系统报告获取失败: {e}")
            raise

    def get_axial_color(self) -> Dict[str, Any]:
        """获取纵向色差数据"""
        self._conn.ensure_connected()
        try:
            ac = self._analyses.New_Analysis("AxialColor")
            ac.ApplyAndWaitForCompletion()
            results = ac.GetResults()

            data: Dict[str, Any] = {}
            for i, grid in enumerate(results.DataGrids):
                if grid is not None:
                    values = np.array(list(grid.Values), dtype=float)
                    data[f"grid_{i}"] = values.tolist()

            ac.Close()
            logger.info("纵向色差分析完成")
            return data
        except Exception as e:
            logger.error(f"纵向色差分析失败: {e}")
            raise

    def get_lateral_color(self) -> Dict[str, Any]:
        """获取横向色差数据"""
        self._conn.ensure_connected()
        try:
            lc = self._analyses.New_Analysis("LateralColor")
            lc.ApplyAndWaitForCompletion()
            results = lc.GetResults()

            data: Dict[str, Any] = {}
            for i, grid in enumerate(results.DataGrids):
                if grid is not None:
                    values = np.array(list(grid.Values), dtype=float)
                    data[f"grid_{i}"] = values.tolist()

            lc.Close()
            logger.info("横向色差分析完成")
            return data
        except Exception as e:
            logger.error(f"横向色差分析失败: {e}")
            raise

    def get_layout(self, layout_type: str = "2D") -> str:
        """获取光路布局图信息

        Args:
            layout_type: "2D" 或 "3D"
        Returns:
            布局描述文本
        """
        self._conn.ensure_connected()
        anal_name = f"{layout_type}DLayout"
        try:
            layout = self._analyses.New_Analysis(anal_name)
            layout.ApplyAndWaitForCompletion()
            text = str(layout.GetResults().GetTextOutput() or "")
            layout.Close()
            logger.info(f"{layout_type} 光路布局获取完成")
            return text
        except Exception as e:
            logger.error(f"光路布局获取失败: {e}")
            raise
