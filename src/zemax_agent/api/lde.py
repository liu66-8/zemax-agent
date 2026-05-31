from __future__ import annotations

import logging
from typing import Any, Dict, List

from .connection import ZemaxConnection

logger = logging.getLogger(__name__)


class SurfaceType:
    STANDARD = "Standard"
    EVEN_ASPHERE = "EvenAsphere"
    PARAXIAL = "Paraxial"
    COORDINATE_BREAK = "CoordinateBreak"


class GlassCatalog:
    AIR = ""
    BK7 = "N-BK7"
    F2 = "N-F2"
    SF2 = "N-SF2"


class ZemaxLDE:
    """Zemax 镜头数据编辑器（LDE）操作接口"""

    def __init__(self, connection: ZemaxConnection) -> None:
        self._conn = connection

    @property
    def _lde(self) -> Any:
        return self._conn.system.LDE

    @property
    def surface_count(self) -> int:
        self._conn.ensure_connected()
        return self._lde.NumberOfSurfaces

    def get_surface_data(self, surface_num: int) -> Dict[str, Any]:
        self._conn.ensure_connected()
        if surface_num < 1 or surface_num > self.surface_count:
            raise ValueError(
                f"面序号 {surface_num} 超出范围 [1, {self.surface_count}]"
            )
        surf = self._lde.GetSurfaceAt(surface_num)
        return {
            "surface_number": surface_num,
            "surface_type": str(surf.Type),
            "comment": str(surf.Comment),
            "radius": float(surf.Radius),
            "thickness": float(surf.Thickness),
            "glass": str(surf.Material),
            "semi_diameter": float(surf.SemiDiameter),
            "conic": float(surf.Conic) if hasattr(surf, "Conic") else 0.0,
        }

    def get_all_surfaces(self) -> List[Dict[str, Any]]:
        self._conn.ensure_connected()
        return [self.get_surface_data(i) for i in range(1, self.surface_count + 1)]

    def set_surface_type(self, surface_num: int, surface_type: str) -> None:
        self._conn.ensure_connected()
        surf = self._lde.GetSurfaceAt(surface_num)
        surf.ChangeType(surface_type)
        logger.info("面 %d 类型已设置为 %s", surface_num, surface_type)

    def set_radius(self, surface_num: int, radius: float) -> None:
        self._conn.ensure_connected()
        surf = self._lde.GetSurfaceAt(surface_num)
        surf.Radius = radius
        logger.info("面 %d 曲率半径已设置为 %s", surface_num, radius)

    def set_thickness(self, surface_num: int, thickness: float) -> None:
        self._conn.ensure_connected()
        if thickness < 0:
            raise ValueError(f"厚度不能为负: {thickness}")
        surf = self._lde.GetSurfaceAt(surface_num)
        surf.Thickness = thickness
        logger.info("面 %d 厚度已设置为 %s", surface_num, thickness)

    def set_glass(self, surface_num: int, glass_name: str) -> None:
        self._conn.ensure_connected()
        surf = self._lde.GetSurfaceAt(surface_num)
        surf.Material = glass_name
        logger.info("面 %d 材料已设置为 %s", surface_num, glass_name)

    def set_semi_diameter(self, surface_num: int, semi_diameter: float) -> None:
        self._conn.ensure_connected()
        if semi_diameter < 0:
            raise ValueError(f"半口径不能为负: {semi_diameter}")
        surf = self._lde.GetSurfaceAt(surface_num)
        surf.SemiDiameter = semi_diameter
        logger.info("面 %d 半口径已设置为 %s", surface_num, semi_diameter)

    def set_conic(self, surface_num: int, conic: float) -> None:
        self._conn.ensure_connected()
        surf = self._lde.GetSurfaceAt(surface_num)
        if hasattr(surf, "Conic"):
            surf.Conic = conic
            logger.info("面 %d 圆锥系数已设置为 %s", surface_num, conic)
        else:
            raise ValueError(f"面型 {surf.Type} 不支持圆锥系数")

    def insert_surface(self, surface_num: int) -> None:
        self._conn.ensure_connected()
        self._lde.InsertNewSurfaceAt(surface_num)
        logger.info("已在面 %d 后插入新面", surface_num)

    def delete_surface(self, surface_num: int) -> None:
        self._conn.ensure_connected()
        count = self.surface_count
        if count <= 2:
            raise ValueError("不能删除唯一的表面（至少保留物面和像面）")
        self._lde.RemoveSurfaceAt(surface_num)
        logger.info("面 %d 已删除", surface_num)

    def set_stop(self, surface_num: int) -> None:
        self._conn.ensure_connected()
        self._lde.MakeSurfaceStop(surface_num)
        logger.info("面 %d 已设为光阑面", surface_num)

    def get_stop_surface(self) -> int:
        self._conn.ensure_connected()
        return self._lde.StopSurface

    def get_glass_catalog_list(self) -> List[str]:
        self._conn.ensure_connected()
        try:
            catalog = self._conn.system.Tools.Catalogs.GetGlassCatalogs()
            glasses: List[str] = []
            for cat in catalog:
                glasses.extend([str(g) for g in cat.GetGlassNames()])
            return glasses
        except Exception:
            return []

    def quick_focus(self) -> None:
        self._conn.ensure_connected()
        self._conn.system.Tools.QuickFocus()
        logger.info("快速对焦完成")

    def get_focal_length(self) -> float:
        self._conn.ensure_connected()
        return self._conn.system.LDE.GetEffectiveFocalLength()
