from zemax_agent.core.optimization_monitor import OptimizationMonitor, OptimizationTrace, ConvergenceState
from zemax_agent.core.optimization_strategy import OptimizationStrategyAdjuster, OptimizationStrategy, StrategyStep, StrategyRecord, StrategyType
from zemax_agent.core.simulation_reader import (
    SimulationDataReader, SimulationData,
    MTFData as SimMTFData, SpotData as SimSpotData,
    WavefrontData as SimWavefrontData, SeidelData as SimSeidelData,
)
from zemax_agent.core.aberration import (
    ImagingQualityEvaluator, AberrationAnalyzer,
    PerformanceEvaluation, AberrationDiagnosis, MetricScore,
)
from zemax_agent.core.report_assembler import ReportAssembler, DesignReport, ReportSection


class TestOptimizationMonitor:
    def test_record_and_convergence_check(self):
        monitor = OptimizationMonitor(stagnation_threshold=3, stagnation_change_rate=0.01)
        for i, mf in enumerate([10.0, 9.5, 9.4, 9.35, 9.33, 9.32, 9.31, 9.305]):
            monitor.record(i, mf)
        state = monitor.check_convergence()
        assert state.is_stagnant

    def test_not_stagnant(self):
        monitor = OptimizationMonitor(stagnation_threshold=3, stagnation_change_rate=0.01)
        for i, mf in enumerate([10.0, 8.0, 5.0, 2.0]):
            monitor.record(i, mf)
        state = monitor.check_convergence()
        assert not state.is_stagnant

    def test_boundary_hits(self):
        monitor = OptimizationMonitor()
        monitor.record_boundary_hit("radius_3")
        monitor.record_boundary_hit("radius_3")
        monitor.record_boundary_hit("radius_3")
        state = monitor.check_convergence()
        assert "radius_3" in state.boundary_violations

    def test_get_summary(self):
        monitor = OptimizationMonitor()
        monitor.record(1, 10.0)
        monitor.record(2, 5.0)
        summary = monitor.get_summary()
        assert summary["iterations"] == 2
        assert summary["improvement_pct"] == 50.0

    def test_trend(self):
        monitor = OptimizationMonitor()
        monitor.record(1, 10.0)
        monitor.record(2, 8.0)
        trend = monitor.get_trend()
        assert len(trend) == 2


class TestOptimizationStrategy:
    def test_handle_stagnation(self):
        adjuster = OptimizationStrategyAdjuster()
        convergence = ConvergenceState(
            is_stagnant=True, stagnation_rounds=5,
            change_rate=1e-6, wall_hit_count=0,
        )
        strategy = adjuster.analyze_and_decide(convergence, [], {}, {})
        assert len(strategy.steps) >= 1
        assert "stagnation" in strategy.reasoning.lower()

    def test_handle_boundary_violations(self):
        adjuster = OptimizationStrategyAdjuster()
        convergence = ConvergenceState(
            is_stagnant=False, wall_hit_count=8,
            boundary_violations=["radius_2", "thickness_4"],
        )
        strategy = adjuster.analyze_and_decide(convergence, [])
        assert len(strategy.steps) >= 1
        assert any(s.strategy_type.value == "adjust_variable_range" for s in strategy.steps)

    def test_no_adjustment_needed(self):
        adjuster = OptimizationStrategyAdjuster()
        convergence = ConvergenceState(is_stagnant=False, wall_hit_count=0, change_rate=1.0)
        strategy = adjuster.analyze_and_decide(convergence, [])
        assert len(strategy.steps) == 0

    def test_record_result(self):
        adjuster = OptimizationStrategyAdjuster()
        strategy = OptimizationStrategy(
            steps=[StrategyStep(strategy_type=StrategyType.MODIFY_WEIGHT, reason="test")],
            reasoning="test", expected_improvement="2x", risk_level="low",
        )
        record = adjuster.record_result("s1", strategy, 10.0, 5.0)
        assert record.successful
        assert record.improvement_pct == 50.0

    def test_history(self):
        adjuster = OptimizationStrategyAdjuster()
        s = OptimizationStrategy(
            steps=[], reasoning="t", expected_improvement="", risk_level="low",
        )
        adjuster.record_result("s1", s, 10.0, 8.0)
        adjuster.record_result("s2", s, 8.0, 6.0)
        assert len(adjuster.get_history()) == 2
        summary = adjuster.get_strategy_summary()
        assert summary["total_adjustments"] == 2


class TestSimulationReader:
    def test_read_mtf(self):
        reader = SimulationDataReader()
        mtf = reader.read_mtf({
            "frequency": 30.0,
            "tangential": {"0": 0.8, "0.7": 0.6},
            "sagittal": {"0": 0.82, "0.7": 0.65},
        })
        assert mtf.frequency == 30.0
        assert mtf.tangential["0"] == 0.8

    def test_read_all(self):
        reader = SimulationDataReader()
        raw = {
            "mtf": {"frequency": 30.0},
            "spot": {"airy_radius": 5.0, "rms_radius": {"0": 3.0}},
            "wavefront": {"rms": {"0": 0.12}, "pv": {"0": 0.8}},
            "seidel": {"surfaces": [{"spherical": -0.2, "coma": 0.05}]},
        }
        sim = reader.read_all(raw)
        assert sim.mtf is not None
        assert sim.spot is not None
        assert sim.wavefront is not None
        assert sim.seidel is not None


class TestImagingQuality:
    def test_evaluate_excellent(self):
        evaluator = ImagingQualityEvaluator()
        reader = SimulationDataReader()
        sim = reader.read_all({
            "mtf": {"frequency": 30.0, "tangential": {"0": 0.75}, "sagittal": {"0": 0.75}},
            "spot": {"airy_radius": 10.0, "rms_radius": {"0": 3.0}},
            "wavefront": {"rms": {"0": 0.05}, "pv": {"0": 0.3}},
        })
        result = evaluator.evaluate(sim)
        assert result.overall_score >= 80
        assert result.overall_rating in ("Excellent", "Good")

    def test_evaluate_poor(self):
        evaluator = ImagingQualityEvaluator()
        reader = SimulationDataReader()
        sim = reader.read_all({
            "mtf": {"frequency": 30.0, "tangential": {"0": 0.1}, "sagittal": {"0": 0.1}},
            "spot": {"airy_radius": 5.0, "rms_radius": {"0": 20.0}},
            "wavefront": {"rms": {"0": 1.5}, "pv": {"0": 6.0}},
        })
        result = evaluator.evaluate(sim)
        assert len(result.problem_list) >= 2


class TestAberrationAnalyzer:
    def test_diagnose_spherical(self):
        analyzer = AberrationAnalyzer()
        reader = SimulationDataReader()
        seidel = reader.read_seidel({
            "surfaces": [{"spherical": -1.5, "coma": 0.01, "astigmatism": 0.01,
                          "field_curvature": 0.01, "distortion": 0.01,
                          "axial_color": 0.01, "lateral_color": 0.01}],
        })
        result = analyzer.diagnose(seidel)
        assert result.aberration_type == "spherical"
        assert result.severity == "high"

    def test_diagnose_well_corrected(self):
        analyzer = AberrationAnalyzer()
        reader = SimulationDataReader()
        seidel = reader.read_seidel({"surfaces": [{}]})
        result = analyzer.diagnose(seidel)
        assert "well corrected" in result.correction_suggestions[0].lower()


class TestReportAssembler:
    def test_assemble_minimal(self):
        assembler = ReportAssembler()
        report = assembler.assemble(project_name="Test Lens")
        assert report.project_name == "Test Lens"
        assert len(report.sections) >= 1

    def test_to_html(self):
        assembler = ReportAssembler()
        report = assembler.assemble(project_name="Test")
        html = assembler.to_html(report)
        assert "<html>" in html
        assert "Test" in html

    def test_to_markdown(self):
        assembler = ReportAssembler()
        report = assembler.assemble(project_name="Test")
        md = assembler.to_markdown(report)
        assert "# " in md
        assert "Test" in md
