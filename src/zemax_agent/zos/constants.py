"""Zemax Agent Constants — physical and design constraints for optical systems."""

MAX_ND = 4.0
MIN_ND = 1.3
MAX_ABBE = 100.0
MIN_ABBE = 15.0
MIN_THICKNESS_MM = 0.1
MAX_RADIUS_MM = 1e12
MIN_WAVELENGTH_UM = 0.1
MAX_WAVELENGTH_UM = 20.0

SURFACE_TYPES = [
    "Standard",
    "Even Asphere",
    "Odd Asphere",
    "Toroidal",
    "Binary 2",
    "Diffraction Grating",
    "Zernike Fringe Sag",
    "Zernike Standard Sag",
    "Extended Polynomial",
    "Biconic",
    "Cubic Spline",
]

GLASS_MODELS = ["Model", "Pickup", "Reflect", "Blank"]

ANALYSIS_TYPES = [
    "MTF",
    "SpotDiagram",
    "FieldCurvatureDistortion",
    "Wavefront",
    "SeidelCoefficients",
    "RayFan",
    "Layout",
    "POP",
]

OPTIMIZATION_ALGORITHMS = ["DampedLeastSquares", "OrthogonalDescent"]

TOLERANCE_TYPES = [
    "TRAD",   "TTHI",   "TIND",   "TABB",
    "TFRN",   "TIRR",   "TSTD",   "TEDX",
    "TEDY",   "TETX",   "TETY",   "TEXI",
    "TEYI",   "TSDX",   "TSDY",
]

DEFAULT_MTF_FREQUENCY = 30.0
