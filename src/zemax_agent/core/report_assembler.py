from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field

from zemax_agent.core.simulation_reader import SimulationData
from zemax_agent.core.aberration import PerformanceEvaluation, AberrationDiagnosis
from zemax_agent.core.optimization_strategy import StrategyRecord

logger = logging.getLogger(__name__)


class ReportSection(BaseModel):
    title: str
    content: str
    order: int


class DesignReport(BaseModel):
    title: str = ""
    project_name: str = ""
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    sections: list[ReportSection] = Field(default_factory=list)


class ReportAssembler:
    def assemble(
        self,
        project_name: str = "",
        requirements: Optional[dict[str, Any]] = None,
        lens_summary: Optional[dict[str, Any]] = None,
        evaluation: Optional[PerformanceEvaluation] = None,
        diagnosis: Optional[AberrationDiagnosis] = None,
        optimization_history: Optional[list[StrategyRecord]] = None,
        conclusions: str = "",
    ) -> DesignReport:
        report = DesignReport(
            title=f"Optical Design Report — {project_name}" if project_name else "Optical Design Report",
            project_name=project_name,
        )

        sections: list[ReportSection] = []

        if requirements:
            sections.append(self._requirements_section(requirements))

        if lens_summary:
            sections.append(self._lens_section(lens_summary))

        if evaluation:
            sections.append(self._performance_section(evaluation))

        if diagnosis:
            sections.append(self._aberration_section(diagnosis))

        if optimization_history:
            sections.append(self._optimization_section(optimization_history))

        sections.append(self._conclusions_section(conclusions, evaluation))

        report.sections = sorted(sections, key=lambda s: s.order)
        return report

    def to_html(self, report: DesignReport) -> str:
        parts = [
            '<html><head><meta charset="utf-8"><title>', report.title, '</title>',
            '<style>',
            'body{font-family:system-ui,sans-serif;max-width:900px;margin:0 auto;padding:20px;color:#333}',
            'h1{color:#1a365d;border-bottom:3px solid #2b6cb0;padding-bottom:10px}',
            'h2{color:#2b6cb0;margin-top:30px}',
            'h3{color:#4a5568}',
            'table{border-collapse:collapse;width:100%;margin:15px 0}',
            'th,td{border:1px solid #e2e8f0;padding:8px 12px;text-align:left}',
            'th{background:#edf2f7;font-weight:600}',
            '.good{color:#38a169}.fair{color:#d69e2e}.poor{color:#e53e3e}',
            '.footer{margin-top:40px;padding-top:20px;border-top:1px solid #e2e8f0;color:#a0aec0;font-size:0.9em}',
            '</style></head><body>',
            '<h1>', report.title, '</h1>',
            '<p>Project: ', report.project_name, ' | Generated: ', report.generated_at[:19], '</p>',
        ]

        for section in report.sections:
            parts.append(f'<h2>{section.title}</h2>')
            parts.append(f'<div>{section.content}</div>')

        parts.append(f'<div class="footer">Zemax Agent — Optical Engineering Workspace</div>')
        parts.append('</body></html>')
        return ''.join(parts)

    def to_markdown(self, report: DesignReport) -> str:
        lines = [
            f"# {report.title}",
            "",
            f"**Project:** {report.project_name}",
            f"**Generated:** {report.generated_at[:19]}",
            "",
        ]
        for section in report.sections:
            lines.append(f"## {section.title}")
            lines.append("")
            lines.append(section.content)
            lines.append("")
        return "\n".join(lines)

    def _requirements_section(self, reqs: dict[str, Any]) -> ReportSection:
        items = [f"- **{k.replace('_', ' ').title()}:** {v}" for k, v in reqs.items() if v]
        content = "<ul>" + "".join(f"<li>{item[2:]}</li>" for item in items) + "</ul>"
        return ReportSection(title="1. Design Requirements", content=content, order=1)

    def _lens_section(self, summary: dict[str, Any]) -> ReportSection:
        rows = [
            ("Effective Focal Length", summary.get("effective_focal_length", "N/A"), "mm"),
            ("F-Number", summary.get("f_number", "N/A"), ""),
            ("Image Space NA", summary.get("image_space_na", "N/A"), ""),
            ("Total Track", summary.get("total_track", "N/A"), "mm"),
            ("Surface Count", summary.get("surface_count", "N/A"), ""),
        ]
        table = '<table><tr><th>Parameter</th><th>Value</th><th>Unit</th></tr>'
        table += ''.join(f'<tr><td>{p}</td><td>{v}</td><td>{u}</td></tr>' for p, v, u in rows)
        table += '</table>'
        return ReportSection(title="2. Optical Layout", content=table, order=2)

    def _performance_section(self, eval_data: PerformanceEvaluation) -> ReportSection:
        rating_class = {
            "Excellent": "good", "Good": "good",
            "Fair": "fair", "Poor": "poor", "Critical": "poor",
        }
        cls = rating_class.get(eval_data.overall_rating, "poor")

        parts = [
            f'<p>Overall Rating: <strong class="{cls}">{eval_data.overall_rating}</strong> '
            f'(Score: {eval_data.overall_score:.1f}/100)</p>',
        ]

        metrics = [
            ("MTF", eval_data.mtf_score),
            ("Spot Diagram", eval_data.spot_score),
            ("Wavefront", eval_data.wavefront_score),
            ("Distortion", eval_data.distortion_score),
        ]

        table = '<table><tr><th>Metric</th><th>Value</th><th>Threshold</th><th>Status</th></tr>'
        for name, score in metrics:
            if score is None:
                continue
            status = "✓ Pass" if score.passed else "✗ Fail"
            status_cls = "good" if score.passed else "poor"
            table += f'<tr><td>{name}</td><td>{score.value}</td>'
            table += f'<td>{score.threshold}</td>'
            table += f'<td class="{status_cls}">{status}</td></tr>'
        table += '</table>'
        parts.append(table)

        if eval_data.problem_list:
            parts.append('<h3>Issues Identified</h3><ul>')
            for p in eval_data.problem_list:
                parts.append(f'<li>{p}</li>')
            parts.append('</ul>')

        return ReportSection(title="3. Performance Analysis", content=''.join(parts), order=3)

    def _aberration_section(self, diagnosis: AberrationDiagnosis) -> ReportSection:
        parts = [
            f'<p><strong>Dominant Aberration:</strong> {diagnosis.dominant_aberration}</p>',
            f'<p><strong>Severity:</strong> {diagnosis.severity}</p>',
            f'<p><strong>Root Cause:</strong> {diagnosis.root_cause}</p>',
            f'<p><strong>Likely Affected Surfaces:</strong> {", ".join(f"Surface {s}" for s in diagnosis.affected_surfaces)}</p>',
            '<h3>Correction Suggestions</h3><ul>',
        ]
        for s in diagnosis.correction_suggestions:
            parts.append(f'<li>{s}</li>')
        parts.append('</ul>')
        return ReportSection(title="4. Aberration Diagnosis", content=''.join(parts), order=4)

    def _optimization_section(self, history: list[StrategyRecord]) -> ReportSection:
        parts = ['<table><tr><th>#</th><th>Strategy</th><th>MF Before</th><th>MF After</th><th>Improvement</th><th>Result</th></tr>']
        for i, r in enumerate(history, 1):
            cls = "good" if r.successful else "poor"
            status = "✓" if r.successful else "✗"
            parts.append(f'<tr><td>{i}</td>')
            parts.append(f'<td>{r.strategy.reasoning[:80]}</td>')
            parts.append(f'<td>{r.mf_before:.6f}</td>')
            parts.append(f'<td>{r.mf_after or "N/A"}</td>')
            parts.append(f'<td>{r.improvement_pct or 0:.1f}%</td>')
            parts.append(f'<td class="{cls}">{status}</td></tr>')
        parts.append('</table>')
        return ReportSection(title="5. Optimization History", content=''.join(parts), order=5)

    def _conclusions_section(self, conclusions: str, evaluation: Optional[PerformanceEvaluation]) -> ReportSection:
        rating = evaluation.overall_rating if evaluation else "Unknown"
        content = f'<p>Overall design quality: <strong>{rating}</strong></p><p>{conclusions or "Design process completed."}</p>'
        return ReportSection(title="6. Conclusions", content=content, order=6)
