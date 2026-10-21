"""Validated, dependency-free configuration for navigation and maintenance."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SynapticSettings:
    edge_upper: int = 50
    edge_target: int = 45
    navigation_steps: int = 8
    global_candidates: int = 20
    fast_index_bytes: int = 65536
    automatic_sleep: bool = True
    idle_seconds: int = 60
    sleep_poll_seconds: int = 5
    sleep_retry_seconds: int = 300
    navigation_output_tokens: int = 2048
    maintenance_output_tokens: int = 2048
    interpretation_output_tokens: int = 1024
    recall_output_tokens: int = 1024
    search_query_characters: int = 2000

    @classmethod
    def from_config(cls, runtime):
        values = runtime.get("synaptic", {})
        if not isinstance(values, dict):
            raise ValueError("runtime.synaptic must be a mapping.")
        settings = cls(**values)
        for name in ("edge_upper", "edge_target", "navigation_steps", "global_candidates",
                     "fast_index_bytes", "idle_seconds", "sleep_poll_seconds", "sleep_retry_seconds",
                     "navigation_output_tokens", "maintenance_output_tokens", "interpretation_output_tokens", "recall_output_tokens",
                     "search_query_characters"):
            value = getattr(settings, name)
            if type(value) is not int or value < 1:
                raise ValueError(f"synaptic.{name} must be a positive integer.")
        if settings.edge_upper < 3 or not 2 <= settings.edge_target < settings.edge_upper:
            raise ValueError("Synaptic limits must satisfy 2 <= edge_target < edge_upper, with edge_upper >= 3.")
        if type(settings.automatic_sleep) is not bool:
            raise ValueError("synaptic.automatic_sleep must be boolean.")
        return settings
