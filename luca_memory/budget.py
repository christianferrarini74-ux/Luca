"""Conservative UTF-8 accounting for payloads and complete model requests."""

from dataclasses import dataclass, replace


def units(text: str) -> int:
    """Use UTF-8 bytes as a conservative estimate, not a model tokenizer count."""
    return len(text.encode("utf-8"))


def clip(text: str, limit: int) -> str:
    return text.encode("utf-8")[:max(0, limit)].decode("utf-8", errors="ignore")


def payload_size(node) -> int:
    return len(node.to_cell().content)


def cache_view(node, limit: int):
    """Cache a bounded view; the complete source remains on SSD."""
    if payload_size(node) <= limit:
        return node
    sections = tuple(replace(s, key=clip(s.key, 64), title=clip(s.title, 128), content="") for s in node.sections[:16])
    compact = replace(node, slug=clip(node.slug, 128), title=clip(node.title, 256),
                      summary=clip(node.summary, min(512, limit // 4)), content="", keywords=(),
                      sections=sections, content_complete=False,
                      full_content_bytes=node.full_content_bytes or units(node.content))
    while payload_size(compact) > limit and compact.sections:
        compact = replace(compact, sections=compact.sections[:-1])
    available = max(0, limit - payload_size(compact) - 32)
    compact = replace(compact, content=clip(node.content, available))
    while payload_size(compact) > limit and compact.content:
        compact = replace(compact, content=clip(compact.content, max(0, units(compact.content) - 128)))
    return compact


@dataclass(frozen=True, slots=True)
class PromptBudget:
    context_window: int = 8192
    output_reserve: int = 512
    framing_reserve: int = 256
    memory_limit: int = 4096
    per_node_limit: int = 1536
    history_limit: int = 1024
    task_limit: int = 512

    def __post_init__(self):
        if min(self.context_window, self.output_reserve, self.memory_limit, self.per_node_limit,
               self.history_limit, self.task_limit) < 1 or self.framing_reserve < 64:
            raise ValueError("Context budgets must be positive and framing reserve at least 64.")
        if self.context_window - self.output_reserve - self.framing_reserve < 2048:
            raise ValueError("The input budget must leave at least 2048 conservative units.")

    @classmethod
    def from_config(cls, config: dict):
        options = config.get("context_budget", {})
        if not isinstance(options, dict):
            raise ValueError("context_budget must be a mapping.")
        return cls(**{key: int(value) for key, value in options.items()})

    def messages(self, instruction: str, memory: str, history: list, question: str) -> tuple[list, dict]:
        available = self.context_window - self.output_reserve - self.framing_reserve
        fixed = units(instruction) + units(question) + 2
        if fixed > available:
            raise ValueError("Il messaggio e le istruzioni superano il budget configurato; riduci il messaggio o aumenta context_window.")
        memory_text = clip(memory, min(self.memory_limit + self.task_limit, available - fixed))
        system = instruction + "\n\n" + memory_text
        remaining = max(0, available - units(system) - units(question))
        chosen = []
        history_size = 0
        # Keep complete user/assistant pairs, newest first, without orphaned replies.
        history = history[-8:]
        for end in range(len(history), 1, -2):
            pair = history[end - 2:end]
            size = sum(units(item["content"]) + 16 for item in pair)
            if history_size + size > min(self.history_limit, remaining):
                break
            chosen = pair + chosen
            history_size += size
        messages = [{"role": "system", "content": system}, *chosen, {"role": "user", "content": question}]
        estimated = sum(units(item["content"]) for item in messages)
        if estimated > available:
            # Account for separators even when the fixed portion exactly fills the budget.
            messages[0]["content"] = clip(system, max(0, available - units(question) - history_size))
            estimated = sum(units(item["content"]) for item in messages)
        return messages, {"accounting": "utf8_bytes_conservative", "input_units": estimated,
                          "input_limit": available, "output_reserve": self.output_reserve,
                          "history_messages": len(chosen), "memory_truncated": units(memory_text) < units(memory)}
