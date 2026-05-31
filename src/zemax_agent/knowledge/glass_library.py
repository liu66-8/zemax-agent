from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class GlassMaterial(BaseModel):
    name: str = ""
    manufacturer: str = ""
    refractive_index_nd: float = 1.5
    abbe_number_vd: float = 60.0
    density_g_cm3: Optional[float] = None
    tce_10_6_per_k: Optional[float] = None
    dpgf: Optional[float] = None
    cost_factor: float = 1.0
    transmission_range_nm: str = ""
    chemical_resistance: str = ""
    notes: str = ""


PRESET_GLASS_CATALOG: list[GlassMaterial] = [
    GlassMaterial(name="N-BK7", manufacturer="Schott", refractive_index_nd=1.51680, abbe_number_vd=64.17, density_g_cm3=2.51, tce_10_6_per_k=7.1, dpgf=-0.0009, cost_factor=1.0),
    GlassMaterial(name="N-SK2", manufacturer="Schott", refractive_index_nd=1.60738, abbe_number_vd=56.65, density_g_cm3=3.15, tce_10_6_per_k=6.5, dpgf=-0.0038, cost_factor=1.5),
    GlassMaterial(name="N-SK11", manufacturer="Schott", refractive_index_nd=1.56384, abbe_number_vd=60.80, density_g_cm3=3.05, tce_10_6_per_k=6.8, dpgf=-0.0055, cost_factor=1.6),
    GlassMaterial(name="N-SK14", manufacturer="Schott", refractive_index_nd=1.60311, abbe_number_vd=60.60, density_g_cm3=3.34, tce_10_6_per_k=6.2, dpgf=-0.0061, cost_factor=2.0),
    GlassMaterial(name="N-SK16", manufacturer="Schott", refractive_index_nd=1.62041, abbe_number_vd=60.32, density_g_cm3=3.52, tce_10_6_per_k=6.7, dpgf=-0.0071, cost_factor=2.5),
    GlassMaterial(name="N-FK5", manufacturer="Schott", refractive_index_nd=1.48749, abbe_number_vd=70.41, density_g_cm3=2.45, tce_10_6_per_k=9.2, dpgf=-0.0014, cost_factor=3.0),
    GlassMaterial(name="N-FK51A", manufacturer="Schott", refractive_index_nd=1.48656, abbe_number_vd=84.47, density_g_cm3=3.55, tce_10_6_per_k=12.4, dpgf=-0.0045, cost_factor=5.0),
    GlassMaterial(name="N-K5", manufacturer="Schott", refractive_index_nd=1.52249, abbe_number_vd=59.48, density_g_cm3=2.61, tce_10_6_per_k=8.2, dpgf=-0.0020, cost_factor=0.9),
    GlassMaterial(name="N-KF9", manufacturer="Schott", refractive_index_nd=1.52346, abbe_number_vd=51.49, density_g_cm3=2.68, tce_10_6_per_k=8.4, dpgf=-0.0043, cost_factor=1.1),
    GlassMaterial(name="N-BAK1", manufacturer="Schott", refractive_index_nd=1.57250, abbe_number_vd=57.55, density_g_cm3=3.06, tce_10_6_per_k=7.6, dpgf=0.0010, cost_factor=1.2),
    GlassMaterial(name="N-BAK4", manufacturer="Schott", refractive_index_nd=1.56883, abbe_number_vd=55.98, density_g_cm3=3.00, tce_10_6_per_k=7.0, dpgf=0.0025, cost_factor=1.3),
    GlassMaterial(name="N-BALF5", manufacturer="Schott", refractive_index_nd=1.54739, abbe_number_vd=53.63, density_g_cm3=2.94, tce_10_6_per_k=8.1, dpgf=-0.0026, cost_factor=1.2),
    GlassMaterial(name="N-SF1", manufacturer="Schott", refractive_index_nd=1.71736, abbe_number_vd=29.62, density_g_cm3=4.04, tce_10_6_per_k=8.1, dpgf=0.0027, cost_factor=1.3),
    GlassMaterial(name="N-SF5", manufacturer="Schott", refractive_index_nd=1.67270, abbe_number_vd=32.25, density_g_cm3=3.98, tce_10_6_per_k=8.2, dpgf=0.0053, cost_factor=1.4),
    GlassMaterial(name="N-SF8", manufacturer="Schott", refractive_index_nd=1.68893, abbe_number_vd=31.25, density_g_cm3=4.13, tce_10_6_per_k=8.0, dpgf=0.0086, cost_factor=1.5),
    GlassMaterial(name="N-SF10", manufacturer="Schott", refractive_index_nd=1.72828, abbe_number_vd=28.53, density_g_cm3=4.33, tce_10_6_per_k=7.5, dpgf=0.0133, cost_factor=1.4),
    GlassMaterial(name="N-SF11", manufacturer="Schott", refractive_index_nd=1.78472, abbe_number_vd=25.76, density_g_cm3=4.96, tce_10_6_per_k=6.1, dpgf=0.0226, cost_factor=1.5),
    GlassMaterial(name="N-LAF7", manufacturer="Schott", refractive_index_nd=1.74950, abbe_number_vd=35.04, density_g_cm3=4.47, tce_10_6_per_k=6.5, dpgf=0.0072, cost_factor=2.0),
    GlassMaterial(name="N-LAF2", manufacturer="Schott", refractive_index_nd=1.74397, abbe_number_vd=44.85, density_g_cm3=4.48, tce_10_6_per_k=7.3, dpgf=-0.0014, cost_factor=2.5),
    GlassMaterial(name="N-LASF9", manufacturer="Schott", refractive_index_nd=1.85025, abbe_number_vd=32.17, density_g_cm3=5.30, tce_10_6_per_k=7.4, dpgf=0.0125, cost_factor=3.0),
    GlassMaterial(name="N-LASF44", manufacturer="Schott", refractive_index_nd=1.80420, abbe_number_vd=46.50, density_g_cm3=5.15, tce_10_6_per_k=6.0, dpgf=-0.0036, cost_factor=4.0),
    GlassMaterial(name="N-LAK8", manufacturer="Schott", refractive_index_nd=1.71300, abbe_number_vd=53.83, density_g_cm3=4.08, tce_10_6_per_k=7.5, dpgf=-0.0066, cost_factor=2.5),
    GlassMaterial(name="N-LAK14", manufacturer="Schott", refractive_index_nd=1.69680, abbe_number_vd=55.41, density_g_cm3=3.89, tce_10_6_per_k=7.6, dpgf=-0.0062, cost_factor=2.8),
    GlassMaterial(name="N-SSK2", manufacturer="Schott", refractive_index_nd=1.62286, abbe_number_vd=53.27, density_g_cm3=3.62, tce_10_6_per_k=7.0, dpgf=-0.0030, cost_factor=2.2),
    GlassMaterial(name="N-SSK5", manufacturer="Schott", refractive_index_nd=1.65844, abbe_number_vd=50.88, density_g_cm3=3.88, tce_10_6_per_k=6.4, dpgf=-0.0015, cost_factor=2.5),
    GlassMaterial(name="H-K9L", manufacturer="CDGM", refractive_index_nd=1.51680, abbe_number_vd=64.20, density_g_cm3=2.52, cost_factor=0.6),
    GlassMaterial(name="H-ZK3", manufacturer="CDGM", refractive_index_nd=1.58913, abbe_number_vd=61.25, density_g_cm3=2.94, cost_factor=1.5),
    GlassMaterial(name="H-ZK6", manufacturer="CDGM", refractive_index_nd=1.61269, abbe_number_vd=58.63, density_g_cm3=3.08, cost_factor=1.8),
    GlassMaterial(name="H-ZF2", manufacturer="CDGM", refractive_index_nd=1.67270, abbe_number_vd=32.22, density_g_cm3=3.80, cost_factor=1.2),
    GlassMaterial(name="H-ZF7LA", manufacturer="CDGM", refractive_index_nd=1.80518, abbe_number_vd=25.46, density_g_cm3=4.61, cost_factor=1.8),
    GlassMaterial(name="S-BSL7", manufacturer="Ohara", refractive_index_nd=1.51633, abbe_number_vd=64.14, density_g_cm3=2.51, cost_factor=0.8),
    GlassMaterial(name="S-TIM2", manufacturer="Ohara", refractive_index_nd=1.62004, abbe_number_vd=36.37, density_g_cm3=3.35, cost_factor=1.3),
    GlassMaterial(name="S-TIM8", manufacturer="Ohara", refractive_index_nd=1.59522, abbe_number_vd=39.23, density_g_cm3=2.96, cost_factor=1.4),
    GlassMaterial(name="S-TIM22", manufacturer="Ohara", refractive_index_nd=1.67790, abbe_number_vd=32.11, density_g_cm3=3.55, cost_factor=1.6),
    GlassMaterial(name="S-LAH58", manufacturer="Ohara", refractive_index_nd=1.88300, abbe_number_vd=40.76, density_g_cm3=5.00, cost_factor=3.5),
    GlassMaterial(name="S-LAH79", manufacturer="Ohara", refractive_index_nd=2.00100, abbe_number_vd=29.13, density_g_cm3=5.80, cost_factor=5.0),
    GlassMaterial(name="S-FPL53", manufacturer="Ohara", refractive_index_nd=1.43875, abbe_number_vd=94.94, density_g_cm3=3.66, cost_factor=8.0),
    GlassMaterial(name="S-FPL55", manufacturer="Ohara", refractive_index_nd=1.43875, abbe_number_vd=94.66, density_g_cm3=3.67, cost_factor=7.5),
    GlassMaterial(name="N-SF6", manufacturer="Schott", refractive_index_nd=1.80518, abbe_number_vd=25.39, density_g_cm3=4.85, tce_10_6_per_k=8.5, dpgf=0.0240, cost_factor=1.5),
    GlassMaterial(name="N-SF66", manufacturer="Schott", refractive_index_nd=1.92286, abbe_number_vd=20.88, density_g_cm3=5.20, tce_10_6_per_k=8.2, dpgf=0.0270, cost_factor=2.5),
]


class GlassLibrary:
    def __init__(self, catalog: Optional[list[GlassMaterial]] = None):
        self._glasses: dict[str, GlassMaterial] = {}
        materials = catalog or PRESET_GLASS_CATALOG
        for glass in materials:
            self._glasses[glass.name.upper()] = glass

    def add(self, glass: GlassMaterial) -> None:
        self._glasses[glass.name.upper()] = glass

    def get(self, name: str) -> Optional[GlassMaterial]:
        return self._glasses.get(name.upper())

    def get_all(self) -> list[GlassMaterial]:
        return list(self._glasses.values())

    def query(
        self,
        nd_min: Optional[float] = None,
        nd_max: Optional[float] = None,
        vd_min: Optional[float] = None,
        vd_max: Optional[float] = None,
        manufacturer: Optional[str] = None,
        name_contains: Optional[str] = None,
        max_cost: Optional[float] = None,
    ) -> list[GlassMaterial]:
        results = []
        for glass in self._glasses.values():
            if nd_min is not None and glass.refractive_index_nd < nd_min:
                continue
            if nd_max is not None and glass.refractive_index_nd > nd_max:
                continue
            if vd_min is not None and glass.abbe_number_vd < vd_min:
                continue
            if vd_max is not None and glass.abbe_number_vd > vd_max:
                continue
            if manufacturer is not None and glass.manufacturer.upper() != manufacturer.upper():
                continue
            if name_contains is not None and name_contains.upper() not in glass.name.upper():
                continue
            if max_cost is not None and glass.cost_factor > max_cost:
                continue
            results.append(glass)
        return results

    def search_text(self, query: str) -> list[GlassMaterial]:
        q = query.upper()
        results = []
        for glass in self._glasses.values():
            if q in glass.name.upper() or q in glass.manufacturer.upper():
                results.append(glass)
        return results[:20]

    def get_manufacturers(self) -> list[str]:
        return sorted({g.manufacturer for g in self._glasses.values() if g.manufacturer})

    def get_nd_vd_range(self) -> dict[str, tuple[float, float]]:
        nds = [g.refractive_index_nd for g in self._glasses.values()]
        vds = [g.abbe_number_vd for g in self._glasses.values()]
        return {"nd": (min(nds), max(nds)), "vd": (min(vds), max(vds))}

    def recommend_alternatives(
        self,
        target_glass: str,
        nd_tolerance: float = 0.05,
        vd_tolerance: float = 5.0,
        max_results: int = 5,
    ) -> list[GlassMaterial]:
        target = self.get(target_glass)
        if target is None:
            return []
        candidates = []
        for glass in self._glasses.values():
            if glass.name.upper() == target.name.upper():
                continue
            nd_diff = abs(glass.refractive_index_nd - target.refractive_index_nd)
            vd_diff = abs(glass.abbe_number_vd - target.abbe_number_vd)
            if nd_diff <= nd_tolerance and vd_diff <= vd_tolerance:
                score = nd_diff / nd_tolerance + vd_diff / vd_tolerance
                candidates.append((score, glass))
        candidates.sort(key=lambda x: x[0])
        return [g for _, g in candidates[:max_results]]

    def to_search_texts(self) -> list[str]:
        texts = []
        for glass in self._glasses.values():
            text = (
                f"Glass: {glass.name}, Manufacturer: {glass.manufacturer}, "
                f"nd={glass.refractive_index_nd:.5f}, vd={glass.abbe_number_vd:.2f}, "
                f"density={glass.density_g_cm3 or 'N/A'}, cost_factor={glass.cost_factor}"
            )
            texts.append(text)
        return texts

    def __len__(self) -> int:
        return len(self._glasses)
