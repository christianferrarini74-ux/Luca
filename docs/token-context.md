# Model-token context budgets

> **Historical record — not current operating instructions.** Designs, defaults, results and next steps below belong to the recorded milestone. For current scope, APIs and behavior read the [current contract](memory-integration-contract.md). Original evidence is preserved.

[Italiano](it/fase-1-sinapsi/15-contesto-in-token.md)

2026-10-21. This supersedes the earlier UTF-8 prompt budgets, not physical
memory accounting. Historical reports remain unchanged.

## Configuration

All values inside `runtime.context_budget`, except `unit`, are now **model
tokens** in the project configuration:

```yaml
context_budget:
  unit: tokens
  context_window: 70000
  output_reserve: 4096
  framing_reserve: 512
  memory_limit: 20000
  per_node_limit: 16000
  history_limit: 40000
  task_limit: 2048
```

The 70,000-token window includes the answer and safety margin: the complete
input may use at most **65,392 tokens**. Limits are ceilings, not allocations
filled with padding. Fixed instructions, current question, explicit task and
complete routing directory come first; relevant knowledge and the newest
conversation pairs use the remaining space. History can therefore use less than
40,000 tokens when other required content needs the room. The configured
orchestrator timeout is 180 seconds to allow longer prefill and generation;
this does not guarantee a particular full-window latency.

The fixed four-pair prompt cap and eight-pair session cap are removed. History
is bounded by its token budget, keeping complete user/assistant pairs. A newest
pair exceeding the history allowance remains available for an explicitly marked
prompt excerpt; older pairs are discarded when the storage budget is exceeded.
This is not automatic conversation summarization or durable chat persistence.
Changing topic in LLM navigation does not itself reset the conversation.

## Native counting, without new packages

LM Studio's loaded model provides `countTokens` and `applyPromptTemplate` through
the same RPC interface used by its
[official Python SDK](https://github.com/lmstudio-ai/lmstudio-python/blob/main/src/lmstudio/sync_api.py).
Luca implements only these two request/response operations and their bounded
WebSocket transport using Python's standard library. Every operation closes its
socket; no subprocess, background tokenizer thread or copied model is needed.
Text-count caching keeps at most 256 hashes and counts, not copies of the text.
RPC changes are a compatibility risk and are surfaced as errors, never a silent
bytes/characters-per-token approximation. Token mode currently requires this
LM Studio interface, not an arbitrary OpenAI-compatible endpoint.

The preflight counts the model-rendered chat template, including roles and
separators. The actual completion's `usage.prompt_tokens` and completion tokens
are also retained separately in diagnostics. Template and inference formatting
can differ slightly: the smoke test counted 28 preflight tokens versus 27
reported by inference. `template_token_delta` records the difference; the
512-token reserve remains in place. Counts are model-native, not a guarantee
that template RPC and inference have identical special-token treatment.

Startup checks both the model's supported maximum and its loaded context. If
unloaded, Luca requests `context_length: 70000` and verifies the result. If
already loaded with a smaller window, startup reports an actionable error
instead of silently unloading a model used by another application. The model
observed here (`google/gemma-4-e2b`) was loaded with 131,072 tokens.

An explicit `unit: utf8_bytes` remains available for legacy/reference-only
configurations and dependency-free rule tests. Missing token service in token
mode is an error; it does not activate that legacy mode.

## Physical memory remains physical

`vram_bytes`, `ram_bytes`, `fast_index_bytes`, serialized payloads, CUDA transfer
statistics and diagnostic text offsets stay in **bytes**. Node-content, task,
navigation and answer prompt budgets use the same bound model token counter.
Offsets are explicitly labeled `span_unit: utf8_bytes`; `memory_bytes` prevents
mixing token counts with exposure offsets. The dashboard labels the units and
shows both preflight and server-confirmed prompt usage.

## Verification

Run the complete suite, including native tokenizer and real CUDA checks:

```powershell
$env:LUCA_TEST_LMSTUDIO = '1'
$env:LUCA_TEST_CUDA = '1'
python -m unittest discover -s tests
```

182 tests passed with both services available. Coverage includes pair retention,
overflow, Unicode, unmodified fixed instructions, task budgets, model loading,
bounded hash caching, fragmented WebSocket reads/messages, ping handling,
client masking, large frames, handshake rejection and socket cleanup.

The live tokenizer assembled a 63,760-token input with 44 historical messages,
20,000 memory tokens and 38,807 history-content tokens. Including answer and
safety reserves: **68,368 / 70,000 tokens**. The current question remained intact.
This verifies assembly/counting of a large prompt, **not** generation-quality
acceptance or a full-window inference stress test.

A separate short inference returned `Ciao`. An isolated SQLite/CUDA session
successfully recalled node 18 (cheese-carving mice), with 405 preflight versus
404 server-confirmed input tokens, and released its resources. Personal memory
was not changed. These checks do not close the outstanding dialogue-faithfulness
issues documented in [the preceding report](memory-entry-cues.md).

The broader synthetic navigation/maintenance run returned **7/8**:
`D:/Test/Luca/phase11-live-20261021-183304.json`. Family navigation, recall,
resident updates, general knowledge, manual grouping/restore and idle grouping
passed. On the external-route case the model oscillated between nodes 4 and 1,
exhausted eight steps, then invented an access code. This remains an open
navigation/answer-grounding defect; a larger context alone does not fix it.

Exit the running Luca instance using **Esci**, then launch `python run_luca.py`
to load the new configuration and code. Existing running processes are not
automatically restarted; no changes to LM Studio's current loaded model are
required when its context is already large enough.
