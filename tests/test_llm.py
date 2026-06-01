from zemax_agent.core.config import LLMConfig
from zemax_agent.llm.provider import LLMProvider, LLMCallResult, OpticalRequirements


class TestLLMConfig:
    def test_default_config(self):
        config = LLMConfig()
        assert config.model == "gpt-4"
        assert config.temperature == 0.1

    def test_custom_config(self):
        config = LLMConfig(provider="openai", model="gpt-3.5-turbo", api_key="sk-test")
        assert config.model == "gpt-3.5-turbo"


class TestOpticalRequirements:
    def test_default(self):
        req = OpticalRequirements()
        assert req.system_type == ""
        assert req.missing_params == []

    def test_with_values(self):
        req = OpticalRequirements(
            system_type="Cooke Triplet",
            focal_length=100.0,
            f_number=4.0,
            missing_params=["wavelength_range"],
        )
        assert req.focal_length == 100.0
        assert "wavelength_range" in req.missing_params


class TestLLMProvider:
    def test_context_compression(self):
        config = LLMConfig(
            provider="openai", model="gpt-4", api_key="sk-test",
            context_window_size=1000, max_context_messages=4,
        )
        provider = LLMProvider(config)

        messages = [
            {"role": "system", "content": "You are an optical engineer."},
        ] + [
            {"role": "user", "content": f"Message {i}" + "x" * 200}
            for i in range(20)
        ]

        compressed = provider._compress_if_needed(messages)
        assert len(compressed) <= 5
        assert compressed[0]["role"] == "system"

    def test_stats_init(self):
        config = LLMConfig(provider="openai", model="gpt-4", api_key="sk-test")
        provider = LLMProvider(config)
        stats = provider.stats
        assert stats["call_count"] == 0
        assert stats["total_tokens"] == 0
