from zemax_agent.tools.registry import ToolRegistry, ToolInput, ToolOutput, tool
from zemax_agent.tools.definitions import register_all_tools


class TestToolRegistry:
    def test_register_and_list(self):
        registry = ToolRegistry()

        def test_func(x: int, y: str = "hello") -> dict:
            """A test function."""
            return {"x": x, "y": y}

        registry.register("test", test_func, namespace="test_ns", description="Test tool")
        tools = registry.list_tools()
        assert len(tools) == 1
        assert tools[0].name == "test"
        assert tools[0].namespace == "test_ns"

    def test_list_namespaces(self):
        registry = ToolRegistry()
        registry.register("a", lambda: None, namespace="ns1")
        registry.register("b", lambda: None, namespace="ns2")
        namespaces = registry.list_namespaces()
        assert "ns1" in namespaces
        assert "ns2" in namespaces

    def test_list_by_namespace(self):
        registry = ToolRegistry()
        registry.register("a", lambda: None, namespace="ns1")
        registry.register("b", lambda: None, namespace="ns2")
        tools = registry.list_tools(namespace="ns1")
        assert len(tools) == 1
        assert tools[0].name == "a"

    def test_invoke_success(self):
        registry = ToolRegistry()

        def add(a: int, b: int) -> int:
            return a + b

        registry.register("add", add, namespace="math")
        result = registry.invoke("math.add", {"a": 1, "b": 2})
        assert result.success
        assert result.data == 3
        assert result.duration_ms > 0

    def test_invoke_not_found(self):
        registry = ToolRegistry()
        result = registry.invoke("nonexistent", {})
        assert not result.success
        assert "not found" in (result.error or "")

    def test_invoke_error(self):
        registry = ToolRegistry()

        def failing():
            raise ValueError("test error")

        registry.register("fail", failing)
        result = registry.invoke("fail", {})
        assert not result.success
        assert "test error" in (result.error or "")

    def test_get_tools_for_llm(self):
        registry = ToolRegistry()

        def lens_get(surface_index: int) -> dict:
            """Get surface data by index."""
            return {}

        registry.register("get_surface_data", lens_get, namespace="lens", description="Get surface data")
        tools = registry.get_tools_for_llm()
        assert len(tools) == 1
        assert tools[0]["function"]["name"] == "lens.get_surface_data"
        assert "description" in tools[0]["function"]

    def test_tool_decorator(self):
        registry = ToolRegistry()

        @tool(registry=registry, namespace="test", description="A decorated tool")
        def my_tool(value: float) -> float:
            return value * 2

        assert registry.get_tool("test.my_tool") is not None
        result = registry.invoke("test.my_tool", {"value": 3.0})
        assert result.data == 6.0

    def test_register_all_tools(self):
        registry = ToolRegistry()
        register_all_tools(registry)
        namespaces = registry.list_namespaces()
        assert "lens" in namespaces
        assert "analysis" in namespaces
        assert "optimize" in namespaces
        assert "tolerance" in namespaces
        assert "system" in namespaces

        all_tools = registry.list_tools()
        assert len(all_tools) >= 25

    def test_llm_format_all_tools(self):
        registry = ToolRegistry()
        register_all_tools(registry)
        tools = registry.get_tools_for_llm()
        assert len(tools) >= 25
        for t in tools:
            assert t["type"] == "function"
            assert "name" in t["function"]
            assert "description" in t["function"]
            assert "parameters" in t["function"]
