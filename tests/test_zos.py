from zemax_agent.zos.models import (
    SurfaceData,
    LensSummary,
    MTFData,
    SpotData,
    OptimizationConfig,
    OptimizationResult,
    SystemInfo,
    FieldConfig,
    WavelengthConfig,
)
from zemax_agent.zos.exceptions import (
    ZOSError,
    ZOSConnectionError,
    ZOSParameterError,
    ZOSNotConnectedError,
    is_retryable,
)
from zemax_agent.zos.dispatcher import ZOSTask, TaskStatus, TaskPriority
from zemax_agent.zos.constants import MAX_ND, MIN_ND, MIN_THICKNESS_MM


class TestZOSModels:
    def test_surface_data_defaults(self):
        surf = SurfaceData(index=1)
        assert surf.surf_type == "Standard"
        assert surf.radius == 0.0
        assert not surf.is_stop

    def test_lens_summary(self):
        summary = LensSummary(surface_count=5, stop_surface=3, efl=100.0)
        assert summary.surface_count == 5
        assert summary.stop_surface == 3

    def test_mtf_data(self):
        mtf = MTFData(frequency=30.0, max_frequency=100.0)
        assert mtf.frequency == 30.0

    def test_spot_data(self):
        spot = SpotData(airy_radius=5.0)
        assert spot.airy_radius == 5.0

    def test_optimization_config(self):
        config = OptimizationConfig(algorithm="DampedLeastSquares", cycles=5)
        assert config.cycles == 5

    def test_optimization_result(self):
        result = OptimizationResult(initial_mf=10.0, final_mf=5.0, improvement_percent=50.0)
        assert result.improvement_percent == 50.0
        assert not result.converged

    def test_system_info(self):
        info = SystemInfo(surface_count=10, is_loaded=True)
        assert info.surface_count == 10
        assert info.is_loaded

    def test_field_config(self):
        config = FieldConfig()
        assert config.field_count == 3
        assert len(config.fields) == 3

    def test_wavelength_config(self):
        config = WavelengthConfig()
        assert config.primary_wavelength == 2
        assert config.wavelength_count == 3


class TestZOSExceptions:
    def test_hierarchy(self):
        assert issubclass(ZOSConnectionError, ZOSError)
        assert issubclass(ZOSParameterError, ZOSError)
        assert issubclass(ZOSNotConnectedError, ZOSError)

    def test_retryable(self):
        assert is_retryable(ZOSConnectionError("test"))
        assert is_retryable(ZOSConnectionError("test"))
        assert not is_retryable(ZOSParameterError("test"))
        assert not is_retryable(ValueError("test"))


class TestZOSTask:
    def test_task_creation(self):
        task = ZOSTask(
            priority=50, seq=1, task_id="test-1",
            task_type="lens.get", func=lambda: None,
        )
        assert task.status == TaskStatus.PENDING
        assert task.priority == 50

    def test_task_priority_ordering(self):
        t1 = ZOSTask(priority=100, seq=1, task_id="high", task_type="a", func=lambda: None)
        t2 = ZOSTask(priority=50, seq=2, task_id="normal", task_type="b", func=lambda: None)
        assert t1 > t2

    def test_task_enum_values(self):
        assert TaskPriority.CRITICAL > TaskPriority.NORMAL
        assert TaskStatus.PENDING.value == "pending"


class TestZOSConstants:
    def test_refractive_index_bounds(self):
        assert MIN_ND < MAX_ND
        assert MIN_ND > 0

    def test_physical_constraints(self):
        assert MIN_THICKNESS_MM >= 0
