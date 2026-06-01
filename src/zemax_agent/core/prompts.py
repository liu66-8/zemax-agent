from __future__ import annotations

from typing import Any

from jinja2 import Template

from zemax_agent.core.project import DesignPhase


PROMPT_TEMPLATES = {
    "requirement_analysis": Template("""\
You are an optical engineering expert. Analyze the following design requirements and produce a structured plan.

Project Context:
- Project: {{ project_name }}
- System Type: {{ system_type }}
- Current Phase: {{ phase }}

Requirements:
{{ requirements }}

{% if lens_summary %}
Current Lens State:
{{ lens_summary }}
{% endif %}

Provide:
1. Key optical specifications to verify
2. Initial structure approach recommendation
3. Critical constraints and trade-offs to consider
"""),

    "initial_structure": Template("""\
You are an optical design expert. Create an initial lens structure based on the requirements.

Project: {{ project_name }}
System Type: {{ system_type }}
Phase: {{ phase }}

Specifications:
- Focal Length: {{ focal_length or 'TBD' }} mm
- F-number: {{ f_number or 'TBD' }}
- Field of View: {{ field_of_view or 'TBD' }} deg
- Wavelength Range: {{ wavelength_range or 'Visible' }}

{% if knowledge_context %}
Reference Knowledge:
{{ knowledge_context }}
{% endif %}

Recommend:
1. Number of elements and basic layout
2. Glass material selection strategy
3. Initial surface radii and thickness estimates
4. Stop position recommendation
"""),

    "optimization": Template("""\
You are an optical optimization expert. Analyze the current design state and suggest optimization strategy.

Project: {{ project_name }}
Phase: {{ phase }}

Current Performance:
{% if performance %}
{{ performance }}
{% endif %}

{% if seidel_data %}
Seidel Aberrations:
{{ seidel_data }}
{% endif %}

Recommend:
1. Variables to add/remove/modify
2. Merit function operand adjustments
3. Optimization algorithm preference
4. Convergence criteria
"""),

    "diagnosis": Template("""\
You are an optical diagnosis expert. Analyze the current lens performance and identify issues.

Project: {{ project_name }}

Performance Data:
- MTF: {{ mtf_summary or 'N/A' }}
- Spot Diagram: {{ spot_summary or 'N/A' }}
- Wavefront RMS: {{ wavefront_summary or 'N/A' }}
- Distortion: {{ distortion_summary or 'N/A' }}

{% if aberration_data %}
Aberration Analysis:
{{ aberration_data }}
{% endif %}

Identify:
1. Dominant aberrations and their sources
2. Performance bottlenecks
3. Specific surface-level corrections needed
"""),

    "report": Template("""\
Generate a comprehensive optical design report.

Project: {{ project_name }}
System Type: {{ system_type }}

Design Process:
{{ design_process }}

Final Performance:
{{ final_performance }}

{% if optimization_history %}
Optimization History:
{{ optimization_history }}
{% endif %}

{% if aberration_report %}
Aberration Report:
{{ aberration_report }}
{% endif %}

Generate sections:
1. Executive Summary
2. Design Specifications
3. Optical Layout Description
4. Performance Analysis
5. Optimization Process
6. Conclusions and Recommendations
"""),
}


def get_prompt(phase: DesignPhase | str, **kwargs: Any) -> str:
    phase_key = phase.value if isinstance(phase, DesignPhase) else phase
    template = PROMPT_TEMPLATES.get(phase_key)
    if template is None:
        return f"You are an optical engineering assistant. Current phase: {phase_key}. Please help with the design task."
    return template.render(**kwargs)


def get_system_prompt(phase: DesignPhase | str, **kwargs: Any) -> str:
    phase_key = phase.value if isinstance(phase, DesignPhase) else phase
    base = get_prompt(phase_key, **kwargs)
    return base + "\n\nAlways respond with actionable, specific optical engineering guidance."
