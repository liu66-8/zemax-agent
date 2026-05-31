from __future__ import annotations

from zemax_agent.tools.registry import ToolRegistry
from zemax_agent.zos import api_lens, api_analysis, api_optimize, api_tolerance, api_system


def register_all_tools(registry: ToolRegistry) -> ToolRegistry:
    _register_lens_tools(registry)
    _register_analysis_tools(registry)
    _register_optimize_tools(registry)
    _register_tolerance_tools(registry)
    _register_system_tools(registry)
    return registry


def _register_lens_tools(registry: ToolRegistry) -> None:
    ns = "lens"
    registry.register("get_surface_data", api_lens.get_surface_data, ns,
                       "Get all data for a specific surface by index")
    registry.register("set_surface_data", api_lens.set_surface_data, ns,
                       "Set surface properties (radius, thickness, glass, type, etc.)")
    registry.register("insert_surface", api_lens.insert_surface, ns,
                       "Insert a new surface after the given index")
    registry.register("delete_surface", api_lens.delete_surface, ns,
                       "Delete a surface at the given index")
    registry.register("get_surface_count", api_lens.get_surface_count, ns,
                       "Get total number of surfaces in the current lens")
    registry.register("set_radius", api_lens.set_radius, ns,
                       "Set curvature radius for a surface")
    registry.register("set_thickness", api_lens.set_thickness, ns,
                       "Set thickness (distance to next surface) for a surface")
    registry.register("set_glass", api_lens.set_glass, ns,
                       "Set glass material for a surface")
    registry.register("set_surface_type", api_lens.set_surface_type, ns,
                       "Change the surface type (Standard, Even Asphere, etc.)")
    registry.register("make_surface_stop", api_lens.make_surface_stop, ns,
                       "Set a surface as the aperture stop")
    registry.register("set_aperture", api_lens.set_aperture, ns,
                       "Set system aperture type and value")
    registry.register("set_fields", api_lens.set_fields, ns,
                       "Configure field points (angles or heights)")
    registry.register("get_fields", api_lens.get_fields, ns,
                       "Get current field configuration")
    registry.register("set_wavelengths", api_lens.set_wavelengths, ns,
                       "Configure wavelength data")
    registry.register("get_wavelengths", api_lens.get_wavelengths, ns,
                       "Get current wavelength configuration")
    registry.register("get_lens_data_summary", api_lens.get_lens_data_summary, ns,
                       "Get complete lens summary including all surface data and system parameters")


def _register_analysis_tools(registry: ToolRegistry) -> None:
    ns = "analysis"
    registry.register("get_mtf", api_analysis.get_mtf, ns,
                       "Run MTF analysis and return modulation transfer function data")
    registry.register("get_spot", api_analysis.get_spot, ns,
                       "Run spot diagram analysis and return spot size data")
    registry.register("get_field_curvature", api_analysis.get_field_curvature, ns,
                       "Run field curvature and distortion analysis")
    registry.register("get_wavefront", api_analysis.get_wavefront, ns,
                       "Run wavefront analysis and return RMS/PV data")
    registry.register("get_seidel", api_analysis.get_seidel, ns,
                       "Run Seidel aberration coefficient analysis")
    registry.register("get_ray_fan", api_analysis.get_ray_fan, ns,
                       "Run ray fan (transverse aberration) analysis")
    registry.register("get_layout", api_analysis.get_layout, ns,
                       "Render optical system layout with ray tracing")
    registry.register("get_pop", api_analysis.get_pop, ns,
                       "Run Physical Optics Propagation (POP) analysis")


def _register_optimize_tools(registry: ToolRegistry) -> None:
    ns = "optimize"
    registry.register("build_merit_function", api_optimize.build_merit_function, ns,
                       "Build merit function with specified operands")
    registry.register("set_variables", api_optimize.set_variables, ns,
                       "Set optimization variables for specified surfaces and parameters")
    registry.register("run_optimization", api_optimize.run_optimization, ns,
                       "Execute local optimization with given configuration")
    registry.register("run_hammer", api_optimize.run_hammer, ns,
                       "Execute Hammer global optimization")
    registry.register("get_optimization_status", api_optimize.get_optimization_status, ns,
                       "Get current optimization status and merit function value")
    registry.register("clear_variables", api_optimize.clear_variables, ns,
                       "Remove all variable solves on specified surfaces")


def _register_tolerance_tools(registry: ToolRegistry) -> None:
    ns = "tolerance"
    registry.register("set_default_tolerances", api_tolerance.set_default_tolerances, ns,
                       "Apply default tolerance values to the current design")
    registry.register("set_tolerance_operand", api_tolerance.set_tolerance_operand, ns,
                       "Add a custom tolerance operand")
    registry.register("run_sensitivity", api_tolerance.run_sensitivity, ns,
                       "Run tolerance sensitivity analysis")
    registry.register("run_monte_carlo", api_tolerance.run_monte_carlo, ns,
                       "Run Monte Carlo tolerance analysis with specified sample count")
    registry.register("get_tolerance_results", api_tolerance.get_tolerance_results, ns,
                       "Get tolerance analysis results including worst offenders and yield estimate")


def _register_system_tools(registry: ToolRegistry) -> None:
    ns = "system"
    registry.register("load_zmx", api_system.load_zmx, ns,
                       "Load a ZMX design file into OpticStudio")
    registry.register("save_zmx", api_system.save_zmx, ns,
                       "Save current design to a ZMX file")
    registry.register("get_system_info", api_system.get_system_info, ns,
                       "Get comprehensive system information (mode, aperture, fields, wavelengths)")
    registry.register("make_sequential", api_system.make_sequential, ns,
                       "Switch to sequential (lens design) mode if not already")
