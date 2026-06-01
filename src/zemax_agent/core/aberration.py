from __future__ import annotations

import logging
from typing import Any, Optional

from pydantic import BaseModel, Field

from zemax_agent.core.simulation_reader import SimulationData, MTFData, SpotData, WavefrontData, SeidelData

logger = logging.getLogger(__name__)


class MetricScore(BaseModel):
    value: float = 0.0
    score: float = 0.0
    threshold: float = 0.0
    passed: bool = False
    comment: str = ""


class PerformanceEvaluation(BaseModel):
    mtf_score: Optional[MetricScore] = None
    spot_score: Optional[MetricScore] = None
    wavefront_score: Optional[MetricScore] = None
    distortion_score: Optional[MetricScore] = None
    overall_score: float = 0.0
    overall_rating: str = "Unknown"
    problem_list: list[str] = Field(default_factory=list)


class AberrationDiagnosis(BaseModel):
    dominant_aberration: str = ""
    aberration_type: str = ""
    severity: str = "low"
    affected_surfaces: list[int] = Field(default_factory=list)
    root_cause: str = ""
    correction_suggestions: list[str] = Field(default_factory=list)


class ImagingQualityEvaluator:
    def evaluate(self, sim: SimulationData) -> PerformanceEvaluation:
        problems: list[str] = []
        scores: list[float] = []

        eval_data = PerformanceEvaluation()

        if sim.mtf:
            mtf_score = self._evaluate_mtf(sim.mtf)
            eval_data.mtf_score = mtf_score
            scores.append(mtf_score.score)
            if not mtf_score.passed:
                problems.append(f"MTF below threshold at {sim.mtf.frequency} lp/mm (avg: {mtf_score.value:.3f})")

        if sim.spot:
            spot_score = self._evaluate_spot(sim.spot)
            eval_data.spot_score = spot_score
            scores.append(spot_score.score)
            if not spot_score.passed:
                problems.append(f"Spot size exceeds Airy disk (RMS: {spot_score.value:.1f} um)")

        if sim.wavefront:
            wf_score = self._evaluate_wavefront(sim.wavefront)
            eval_data.wavefront_score = wf_score
            scores.append(wf_score.score)
            if not wf_score.passed:
                problems.append(f"Wavefront error exceeds λ/4 (RMS: {wf_score.value:.3f} λ)")

        if sim.seidel:
            dist_max = max(
                abs(sim.seidel.distortion.get(0, 0)),
                abs(sim.seidel.field_curvature.get(0, 0)),
            )
            d_score = self._evaluate_distortion(dist_max)
            eval_data.distortion_score = MetricScore(
                value=dist_max,
                score=d_score,
                threshold=2.0,
                passed=d_score >= 60.0,
                comment=f"Max distortion: {dist_max:.2f}%",
            )
            scores.append(d_score)
            if d_score < 60.0:
                problems.append(f"Distortion exceeds limit ({dist_max:.2f}%)")

        avg = sum(scores) / len(scores) if scores else 0
        eval_data.overall_score = avg
        eval_data.overall_rating = self._rating(avg)
        eval_data.problem_list = problems

        return eval_data

    def _evaluate_mtf(self, mtf: MTFData) -> MetricScore:
        tan_values = list(mtf.tangential.values()) + list(mtf.sagittal.values())
        if not tan_values:
            return MetricScore(value=0, score=0, threshold=0.3, passed=False, comment="No MTF data")

        avg_mtf = sum(tan_values) / len(tan_values)
        threshold = 0.3

        if mtf.diffraction_limit:
            relative = avg_mtf / max(mtf.diffraction_limit, 1e-6)
            score = min(100.0, relative * 100)
        else:
            score = min(100.0, (avg_mtf / 0.8) * 100)

        return MetricScore(
            value=round(avg_mtf, 4),
            score=round(score, 1),
            threshold=threshold,
            passed=avg_mtf >= threshold,
            comment=f"Avg MTF at {mtf.frequency} lp/mm: {avg_mtf:.3f} (diff limit: {mtf.diffraction_limit or 'N/A'})",
        )

    def _evaluate_spot(self, spot: SpotData) -> MetricScore:
        rms_values = list(spot.rms_radius.values())
        if not rms_values:
            return MetricScore(value=0, score=0, threshold=spot.airy_radius, passed=False, comment="No spot data")

        avg_rms = sum(rms_values) / len(rms_values)
        airy = max(spot.airy_radius, 1e-6)
        ratio = airy / max(avg_rms, 1e-6)

        score = min(100.0, ratio * 50)
        return MetricScore(
            value=round(avg_rms, 2),
            score=round(score, 1),
            threshold=airy,
            passed=avg_rms <= airy,
            comment=f"RMS spot: {avg_rms:.2f} um (Airy: {airy:.2f} um)",
        )

    def _evaluate_wavefront(self, wf: WavefrontData) -> MetricScore:
        rms_values = list(wf.rms.values())
        if not rms_values:
            return MetricScore(value=0, score=0, threshold=0.25, passed=False, comment="No wavefront data")

        avg_rms = sum(rms_values) / len(rms_values)
        threshold = 0.25

        score = max(0.0, 100.0 - (avg_rms / threshold) * 50)
        return MetricScore(
            value=round(avg_rms, 4),
            score=round(score, 1),
            threshold=threshold,
            passed=avg_rms <= threshold,
            comment=f"RMS wavefront: {avg_rms:.3f} λ (Marechal: ≤{threshold})",
        )

    def _evaluate_distortion(self, distortion_max: float) -> float:
        if distortion_max <= 1.0:
            return 95.0
        elif distortion_max <= 2.0:
            return 80.0
        elif distortion_max <= 5.0:
            return 50.0
        else:
            return max(0.0, 50.0 - (distortion_max - 5.0) * 10)

    @staticmethod
    def _rating(score: float) -> str:
        if score >= 90:
            return "Excellent"
        elif score >= 75:
            return "Good"
        elif score >= 60:
            return "Fair"
        elif score >= 40:
            return "Poor"
        else:
            return "Critical"


class AberrationAnalyzer:
    def diagnose(self, seidel: SeidelData) -> AberrationDiagnosis:
        aberrations = {
            "spherical": abs(seidel.spherical.get(0, 0)),
            "coma": abs(seidel.coma.get(0, 0)),
            "astigmatism": abs(seidel.astigmatism.get(0, 0)),
            "field_curvature": abs(seidel.field_curvature.get(0, 0)),
            "distortion": abs(seidel.distortion.get(0, 0)),
            "axial_color": abs(seidel.axial_color.get(0, 0)),
            "lateral_color": abs(seidel.lateral_color.get(0, 0)),
        }

        if not aberrations or max(aberrations.values()) < 0.01:
            return AberrationDiagnosis(
                dominant_aberration="None significant",
                aberration_type="none",
                severity="low",
                correction_suggestions=["Performance is well corrected."],
            )

        sorted_aberrations = sorted(aberrations.items(), key=lambda x: x[1], reverse=True)
        dominant_name, dominant_value = sorted_aberrations[0]

        severity = "low"
        if dominant_value > 0.5:
            severity = "high"
        elif dominant_value > 0.1:
            severity = "medium"

        suggestions = self._get_correction_suggestions(dominant_name, severity)
        affected = self._estimate_affected_surfaces(dominant_name)

        return AberrationDiagnosis(
            dominant_aberration=dominant_name,
            aberration_type=dominant_name,
            severity=severity,
            affected_surfaces=affected,
            root_cause=f"Dominant {dominant_name} aberration (magnitude: {dominant_value:.4f})",
            correction_suggestions=suggestions,
        )

    def _get_correction_suggestions(self, aberration: str, severity: str) -> list[str]:
        suggestions: dict[str, list[str]] = {
            "spherical": [
                "Bend elements to reduce spherical aberration",
                "Consider using an aspheric surface near the stop",
                "Split high-power positive elements into multiple weaker elements",
            ],
            "coma": [
                "Adjust stop position to satisfy Abbe sine condition",
                "Check symmetry of elements around the stop",
                "Bend elements to reduce coma contributions",
            ],
            "astigmatism": [
                "Adjust stop position relative to elements",
                "Increase separation between positive and negative elements",
                "Consider anastigmatic lens configurations",
            ],
            "field_curvature": [
                "Use higher refractive index materials for positive elements",
                "Add field flattener lens near image plane",
                "Consider Petzval sum correction through material choice",
            ],
            "distortion": [
                "Apply stop symmetry to cancel distortion",
                "Use aspheric surfaces for distortion control",
                "Consider telecentric design for low distortion",
            ],
            "axial_color": [
                "Replace with lower dispersion glass materials",
                "Introduce flint element in doublet to cancel chromatic",
                "Consider diffractive optical element for color correction",
            ],
            "lateral_color": [
                "Improve symmetry around the stop",
                "Use same glass type for elements on both sides of stop",
                "Increase stop-to-element distances to reduce lateral color",
            ],
        }

        return suggestions.get(aberration, ["Analyze surface contributions to identify correction strategy."])

    def _estimate_affected_surfaces(self, aberration: str) -> list[int]:
        mapping = {
            "spherical": [1, 2],
            "coma": [2, 3],
            "astigmatism": [2, 3, 4],
            "field_curvature": [1, 2, 3],
            "distortion": [1],
            "axial_color": [1, 2],
            "lateral_color": [2, 3],
        }
        return mapping.get(aberration, [1])
