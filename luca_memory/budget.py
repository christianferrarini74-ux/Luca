"""Separate physical byte accounting from model-native prompt token budgets."""

from dataclasses import dataclass, field, replace


def units(text: str) -> int:
    """Use UTF-8 bytes as a conservative estimate, not a model tokenizer count."""
    return len(text.encode("utf-8"))


def clip(text: str, limit: int) -> str:
    """Bound physical UTF-8 storage without leaving a partial Unicode character."""
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
    unit: str = "utf8_bytes"
    counter: object = field(default=None, repr=False, compare=False)

    def __post_init__(self):
        if self.unit not in {"tokens", "utf8_bytes"}:
            raise ValueError("context_budget.unit must be tokens or utf8_bytes.")
        if min(self.context_window, self.output_reserve, self.memory_limit, self.per_node_limit,
               self.history_limit, self.task_limit) < 1 or self.framing_reserve < 64:
            raise ValueError("Context budgets must be positive and framing reserve at least 64.")
        if self.context_window - self.output_reserve - self.framing_reserve < 2048:
            raise ValueError("The input budget must leave at least 2048 input units.")

    @classmethod
    def from_config(cls, config: dict):
        options = config.get("context_budget", {})
        if not isinstance(options, dict):
            # Preserve the existing ValueError contract used by validation callers.
            raise ValueError("context_budget must be a mapping.")  # noqa: TRY004
        return cls(**{key: str(value) if key == "unit" else int(value) for key, value in options.items()})

    @property
    def accounting(self):
        return "model_tokens" if self.unit == "tokens" else "utf8_bytes_conservative"

    def count(self, text):
        if self.unit == "utf8_bytes":
            return units(text)
        if self.counter is None:
            raise ValueError("Token budgets require the selected model's token counter.")
        return self.counter.count(text)

    def truncate(self, text, limit):
        """Keep a Unicode prefix measured with the selected model's tokenizer."""
        limit = max(0, limit)
        if self.unit == "utf8_bytes":
            return clip(text, limit)
        if self.count(text) <= limit:
            return text
        low, high = 0, len(text)
        while low < high:
            middle = (low + high + 1) // 2
            if self.count(text[:middle]) <= limit:
                low = middle
            else:
                high = middle - 1
        # Prefix token counts need not be strictly monotonic; the selected
        # prefix is rechecked, and no maximal-prefix guarantee is required.
        result = text[:low]
        return result if self.count(result) <= limit else ""

    def history_count(self, history):
        return self.count("\n".join(item["content"] for item in history))

    def trim_history(self, history):
        """Bound stored conversation by tokens, not a fixed number of turns."""
        low, high = 0, len(history) // 2
        while low < high:
            pairs = (low + high + 1) // 2
            if self.history_count(history[-2 * pairs:]) <= self.history_limit:
                low = pairs
            else:
                high = pairs - 1
        # Preserve the latest complete pair for excerpting if it alone is huge.
        return history[-2 * max(1, low):] if history else []

    def _token_messages(self, instruction, memory, history, question, required_context):
        """Pack mandatory context first, then optional memory and complete history pairs."""
        if self.count(required_context) > self.task_limit:
            raise ValueError("Il compito supera il budget riservato in token.")
        if required_context:
            instruction += "\n\n" + required_context
        available = self.context_window - self.output_reserve - self.framing_reserve
        def assemble(memory_text, selected):
            return [{"role": "system", "content": instruction + ("\n\n" + memory_text if memory_text else "")},
                    *selected, {"role": "user", "content": question}]
        def measure(memory_text, selected):
            return self.counter.messages(assemble(memory_text, selected))
        # Count the provider's full chat template; isolated strings can have different boundaries.
        fixed = measure("", [])
        if fixed > available:
            raise ValueError("Messaggio, istruzioni e rubrica completa superano il contesto in token configurato.")
        memory_text = self.truncate(memory, min(self.memory_limit, max(0, available - fixed)))
        # Template boundaries may tokenize differently from isolated text.
        while measure(memory_text, []) > available:
            memory_text = self.truncate(memory_text, max(0, self.count(memory_text) - 32))
        # Binary-search whole pairs; excerpt only the newest pair when no full pair fits.
        low, high = 0, len(history) // 2
        while low < high:
            pairs = (low + high + 1) // 2
            selected = history[-pairs * 2:]
            if self.history_count(selected) <= self.history_limit and measure(memory_text, selected) <= available:
                low = pairs
            else:
                high = pairs - 1
        selected = history[-low * 2:] if low else []
        excerpted = False
        if not selected and len(history) >= 2:
            capacity = min(self.history_limit, max(0, available - measure(memory_text, [])))
            while capacity >= 64:
                selected = [{"role": item["role"], "content": self.truncate(item["content"], max(0, capacity // 2 - 16)) + " [estratto cronologia]"}
                            for item in history[-2:]]
                if self.history_count(selected) <= self.history_limit and measure(memory_text, selected) <= available:
                    excerpted = True
                    break
                capacity //= 2
                selected = []
        messages = assemble(memory_text, selected)
        total = self.counter.messages(messages)
        if total > available:
            raise ValueError("Il prompt completo supera il limite in token; nessuna istruzione obbligatoria è stata troncata.")
        return messages, {"accounting": self.accounting, "input_units": total, "input_tokens": total,
            "input_limit": available, "context_window": self.context_window, "output_reserve": self.output_reserve,
            "history_messages": len(selected), "history_tokens": self.history_count(selected),
            "memory_units": self.count(memory_text), "memory_bytes": units(memory_text),
            "history_excerpted": excerpted, "memory_truncated": memory_text != memory}

    def messages(self, instruction: str, memory: str, history: list, question: str, *, required_context: str = "") -> tuple[list, dict]:
        """Keep native-token packing distinct from the legacy conservative byte contract."""
        if self.unit == "tokens":
            self.count("")  # Fail clearly when no model tokenizer has been bound.
            return self._token_messages(instruction, memory, history, question, required_context)
        if units(required_context) > self.task_limit:
            raise ValueError("Il compito supera il budget riservato.")
        if required_context:
            instruction = instruction + "\n\n" + required_context
        available = self.context_window - self.output_reserve - self.framing_reserve
        fixed = units(instruction) + units(question) + 2
        if fixed > available:
            raise ValueError("Il messaggio e le istruzioni superano il budget configurato; riduci il messaggio o aumenta context_window.")
        memory_text = clip(memory, min(self.memory_limit + self.task_limit, available - fixed))
        system = instruction + ("\n\n" + memory_text if memory_text else "")
        remaining = max(0, available - units(system) - units(question))
        chosen = []
        history_size = 0
        history_excerpted = False
        # Preserve paired roles; excerpt the newest oversized pair without changing stored history.
        for end in range(len(history), 1, -2):
            pair = history[end - 2:end]
            size = sum(units(item["content"]) + 16 for item in pair)
            if history_size + size > min(self.history_limit, remaining):
                capacity = min(self.history_limit, remaining) - history_size
                if not chosen and capacity >= 64:
                    marker = " [estratto cronologia]"
                    user_allowance = min(units(pair[0]["content"]), capacity // 2 - 16)
                    allowances = (user_allowance, capacity - 32 - user_allowance)
                    excerpt_pair = []
                    for item, allowance in zip(pair, allowances):
                        content = item["content"]
                        if units(content) > allowance:
                            content = clip(content, max(0, allowance - units(marker))) + clip(marker, allowance)
                        excerpt_pair.append({"role": item["role"], "content": content})
                    chosen = excerpt_pair
                    history_size = sum(units(item["content"]) + 16 for item in chosen)
                    history_excerpted = True
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
                          "history_messages": len(chosen), "memory_units": units(memory_text),
                          "memory_bytes": units(memory_text),
                          "history_excerpted": history_excerpted,
                          "memory_truncated": units(memory_text) < units(memory)}
