from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class TemplateParameter(BaseModel):
    name: str
    description: str = ""
    default_value: Any = None
    param_type: str = "float"
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    unit: str = ""


class DesignTemplate(BaseModel):
    name: str
    system_type: str
    description: str = ""
    category: str = ""
    parameters: list[TemplateParameter] = Field(default_factory=list)
    lens_description: str = ""
    reference: str = ""


PRESET_TEMPLATES: list[DesignTemplate] = [
    DesignTemplate(
        name="Cooke Triplet",
        system_type="Triplet",
        description="Classic three-element Cooke triplet design. Good correction for spherical, coma, and astigmatism.",
        category="prime_lens",
        parameters=[
            TemplateParameter(name="focal_length", description="Effective focal length", default_value=100.0, param_type="float", min_value=10.0, max_value=1000.0, unit="mm"),
            TemplateParameter(name="f_number", description="F-number", default_value=4.0, param_type="float", min_value=1.4, max_value=16.0, unit=""),
            TemplateParameter(name="field_angle", description="Half field of view", default_value=20.0, param_type="float", min_value=1.0, max_value=60.0, unit="deg"),
            TemplateParameter(name="wavelength_primary", description="Primary wavelength", default_value=0.5876, param_type="float", min_value=0.4, max_value=0.9, unit="um"),
        ],
        lens_description="Three elements: positive crown - negative flint - positive crown. Stop at second element.",
        reference="Smith, Modern Optical Engineering, Ch. 12",
    ),
    DesignTemplate(
        name="Double Gauss",
        system_type="DoubleGauss",
        description="Symmetrical Double Gauss design. Excellent correction for low F/# systems.",
        category="prime_lens",
        parameters=[
            TemplateParameter(name="focal_length", description="Effective focal length", default_value=50.0, param_type="float", min_value=10.0, max_value=500.0, unit="mm"),
            TemplateParameter(name="f_number", description="F-number", default_value=2.0, param_type="float", min_value=0.95, max_value=8.0, unit=""),
            TemplateParameter(name="field_angle", description="Half field of view", default_value=25.0, param_type="float", min_value=5.0, max_value=45.0, unit="deg"),
            TemplateParameter(name="wavelength_primary", description="Primary wavelength", default_value=0.5876, param_type="float", min_value=0.4, max_value=0.9, unit="um"),
        ],
        lens_description="Six elements in 4 groups, symmetrical about the stop. Outer meniscus elements with inner doublets.",
        reference="Kingslake, Lens Design Fundamentals, Ch. 10",
    ),
    DesignTemplate(
        name="Petzval Portrait",
        system_type="Petzval",
        description="Classic Petzval portrait lens with high speed and narrow field.",
        category="prime_lens",
        parameters=[
            TemplateParameter(name="focal_length", description="Effective focal length", default_value=85.0, param_type="float", min_value=50.0, max_value=300.0, unit="mm"),
            TemplateParameter(name="f_number", description="F-number", default_value=1.8, param_type="float", min_value=0.95, max_value=5.6, unit=""),
            TemplateParameter(name="field_angle", description="Half field of view", default_value=15.0, param_type="float", min_value=5.0, max_value=25.0, unit="deg"),
            TemplateParameter(name="wavelength_primary", description="Primary wavelength", default_value=0.5876, param_type="float", min_value=0.4, max_value=0.9, unit="um"),
        ],
        lens_description="Two separated positive groups. Front: cemented doublet. Rear: air-spaced doublet.",
        reference="Smith, Modern Lens Design, Ch. 8",
    ),
    DesignTemplate(
        name="Telephoto",
        system_type="Telephoto",
        description="Telephoto design with reduced overall length compared to focal length.",
        category="telephoto",
        parameters=[
            TemplateParameter(name="focal_length", description="Effective focal length", default_value=200.0, param_type="float", min_value=100.0, max_value=1000.0, unit="mm"),
            TemplateParameter(name="f_number", description="F-number", default_value=4.0, param_type="float", min_value=2.8, max_value=11.0, unit=""),
            TemplateParameter(name="field_angle", description="Half field of view", default_value=6.0, param_type="float", min_value=1.0, max_value=15.0, unit="deg"),
            TemplateParameter(name="telephoto_ratio", description="Length/Focal length ratio", default_value=0.7, param_type="float", min_value=0.5, max_value=0.95, unit=""),
        ],
        lens_description="Positive front group + negative rear group. Front: cemented doublet. Rear: singlet or doublet.",
        reference="Fischer, Optical System Design, Ch. 5",
    ),
    DesignTemplate(
        name="Reverse Telephoto",
        system_type="ReverseTelephoto",
        description="Retrofocus wide-angle design with long back focal length.",
        category="wide_angle",
        parameters=[
            TemplateParameter(name="focal_length", description="Effective focal length", default_value=24.0, param_type="float", min_value=10.0, max_value=50.0, unit="mm"),
            TemplateParameter(name="f_number", description="F-number", default_value=2.8, param_type="float", min_value=1.4, max_value=8.0, unit=""),
            TemplateParameter(name="field_angle", description="Half field of view", default_value=42.0, param_type="float", min_value=30.0, max_value=80.0, unit="deg"),
        ],
        lens_description="Negative front group + positive rear group. Requires strong negative power at front.",
        reference="Laikin, Lens Design, Ch. 9",
    ),
    DesignTemplate(
        name="Aspheric Singlet",
        system_type="AsphericSinglet",
        description="Single element with aspheric surface(s). Suitable for laser collimation and simple imaging.",
        category="special",
        parameters=[
            TemplateParameter(name="focal_length", description="Effective focal length", default_value=50.0, param_type="float", min_value=5.0, max_value=500.0, unit="mm"),
            TemplateParameter(name="f_number", description="F-number", default_value=5.0, param_type="float", min_value=1.0, max_value=20.0, unit=""),
            TemplateParameter(name="wavelength_primary", description="Wavelength", default_value=0.6328, param_type="float", min_value=0.3, max_value=2.0, unit="um"),
        ],
        lens_description="Single aspheric lens. Use Even Asphere surface on first surface, Sphere on second.",
        reference="",
    ),
]


class TemplateLibrary:
    def __init__(self, templates: Optional[list[DesignTemplate]] = None):
        self._templates: dict[str, DesignTemplate] = {}
        for tmpl in (templates or PRESET_TEMPLATES):
            self._templates[tmpl.name] = tmpl

    def get(self, name: str) -> Optional[DesignTemplate]:
        return self._templates.get(name)

    def list_all(self) -> list[DesignTemplate]:
        return list(self._templates.values())

    def list_by_category(self, category: str) -> list[DesignTemplate]:
        return [t for t in self._templates.values() if t.category == category]

    def get_categories(self) -> list[str]:
        return sorted({t.category for t in self._templates.values() if t.category})

    def generate_params(self, name: str, overrides: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        tmpl = self.get(name)
        if tmpl is None:
            return {}

        params = {p.name: p.default_value for p in tmpl.parameters}
        if overrides:
            params.update({k: v for k, v in overrides.items() if k in params})
        return params

    def __len__(self) -> int:
        return len(self._templates)
