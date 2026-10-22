# Model size, required reads and multi-GPU coexistence

2026-10-22. [Italiano](it/fase-1-sinapsi/25-modello-lettura-obbligatoria-multi-gpu.md).

## Model selection and load

LM Studio's installed catalog offers `qwen/qwen3.8-27b` Q4_K_M, a 27B model
with a 16.52 GiB model file. It supports the configured context. The installed
CLI estimated 26.56 GiB GPU memory at 70,000 tokens, full offload and one parallel
prediction; the load completed in 55.52 seconds. No model was downloaded.
The actual loaded context is 70,144 tokens (backend rounding), while Luca's
prompt budget remains 70,000.

The comparison model is `google/gemma-4-e2b` Q4_K_M. LM Studio labels its
parameter count **4.6B**; the E2B name is not evidence that it is a simple dense
2B model. This is a comparison of two complete model/runtime combinations,
not a controlled ablation of parameter count alone.

The existing Gemma instance was preserved: loaded context 131,072 and parallel
limit four, versus Qwen's one. Requests are sequential, with the same Luca
budget, temperature, bible snapshot, questions and history. These differing load
settings, model families and tokenizer/grammar behavior limit latency comparisons.
Reasoning defaults are not forcibly disabled. The application's config is unchanged.

LM Studio load behavior was checked against its
[official load API documentation](https://lmstudio.ai/docs/developer/rest/load)
and the installed `lms load --help`; estimates are not measured allocations.

## Exact policy under test

The global entry index already runs in Luca. The experimental `required` policy
does **not** add a second generic search. If addresses exist but no node has
actually been read this turn, it restricts the action schema to legal `open`
choices. The LLM selects the ID; the normal Core validates the address. After
one read all ordinary choices return. If there are no candidates, general
answers remain possible. This is not "read the whole library" or guaranteed
complete knowledge: the first selected node can be wrong or insufficient.

`free` and `required` use the same unmodified bible. Their order alternates
between cases. Each arm has a fresh adapter, conversation and temporary database.
The stale-history probe explicitly injects the same old conversation in each arm.
No answer key is passed to the model. The production navigator is not changed.

```powershell
python -m luca_memory.model_memory_check --models google/gemma-4-e2b,qwen/qwen3.8-27b --case incomplete
python -m luca_memory.model_memory_check --models google/gemma-4-e2b,qwen/qwen3.8-27b --case updated,stale_history,conflict,general
python -m luca_memory.model_memory_check --models google/gemma-4-e2b,qwen/qwen3.8-27b --case generic_revision
```

Run from the checkout. The CLI assumes installed models and uses their current
LM Studio load state; it does not unload another user's model to force placement.

## Hardware and accounting

Three RTX 5060 Ti cards report about 16 GiB each. Before Qwen loading, GPU used
memory was 6,935/14/14 MiB for devices 0/1/2. After loading it was approximately
14,440/551/13,011 MiB. During Qwen generation, utilization was observed on both
0 and 2 (for example 40%/44%). GPU 1 holds Luca's actual CUDA node allocations;
LM Studio also creates some allocations there. It is not claimed to be exclusive.

This demonstrates a multi-GPU workload/coexistence, not a specific tensor-
parallel algorithm or speedup. Luca's node carousel still selects **one CUDA
device per session**, not a graph sharded across all GPUs. Content read by Luca
is serialized into model input; no direct device-to-device semantic integration
or GPU peer-to-peer path is claimed.

Both arms deliberately use one VRAM node slot and one RAM slot to make eviction
visible. Budgets in bytes and tokens remain unchanged. A separate deterministic
cycle opens document nodes 1–7 then 1 again, verifies content hashes and released
CUDA buffers. It runs with both models resident, not as evidence of concurrent
LLM computation during every transfer. SQLite/OS caches are not disabled: this
is an integrity/residency test, not a cold physical-disk benchmark.

Reports under `D:/Test/Luca/model-memory-check-*.json` record GPU samples,
all model requests and accumulated provider token usage, actual readings,
traces, RAM/SSD demotion events and physical transfers. Turn seconds exclude
adapter setup; wall seconds include it, but not the preloaded model's initial
load. Timing is not electrical energy or monetary cost. Small fixtures and
single runs cannot establish general reliability or large-library scalability.

The request counter counts generation calls, including a fallback response if
one occurs; management and tokenization HTTP calls are not generation calls.

## Results: 24 live executions

Evidence files:

- `D:/Test/Luca/model-memory-check-20261022-084939-505201.json`: recovery, four executions.
- `D:/Test/Luca/model-memory-check-20261022-085358-131429.json`: current revision, stale history, conflict and arithmetic, sixteen executions.
- `D:/Test/Luca/model-memory-check-20261022-090205-117666.json`: general definition with incidental revision-title matches, four executions.

No provider/execution errors occurred. Human review, not lexical scoring:

| Probe | Gemma E2B | Qwen 27B |
| --- | --- | --- |
| Recovery | Incomplete with either policy; required reads alarm then unrelated limits | Both policies read alarm → recovery → modes with two local steps; recovery improves, but opening thresholds remain unread/unspecified |
| Current Primula revision | Both policies answer for the wrong laboratory | Both read the active Primula revision and answer 1502 |
| Stale history | Free reads 1502 but wrongly begins "yes" to keeping the old port; required reads only the index and cannot give the replacement | Both reject old 502 and give current 1502 |
| Equal-authority conflict | Both read only A and choose 2502 | Both traverse A → B locally and disclose the unresolved 2502/3502 conflict |
| Arithmetic | Both answer 42 without reading | Both answer 42 without reading |

This changes the diagnosis: useful autonomous local exploration, scoped updates
and conflict detection appear with the larger model and the **original bible**.
The earlier small-model failures are not evidence that Luca's routes cannot work.
Nevertheless Qwen still stops early on the recovery task; do not declare full
autonomy solved. It did not read all archived/draft sources, so this is not a
complete certification of authority resolution, nor a direct test of outdated
knowledge inside weights.

### Measured cost of an unnecessary read

"What does document revision mean?" matches specific revision titles but needs
no IRIS-17 facts. Both free arms answer without opening memory. Required arms
read one node; Qwen also adds an unnecessary IRIS-17 example.

| Model / policy | Generation calls | Turn seconds | Total provider tokens |
| --- | ---: | ---: | ---: |
| Gemma free | 1 | 6.655 | 2,227 |
| Gemma required | 2 | 7.847 | 4,411 |
| Qwen free | 1 | 60.597 | 2,914 |
| Qwen required | 2 | 67.702 | 5,219 |

Thus the extra read costs one additional generation in this controlled case:
2,184/2,305 additional tokens and about 1.2/7.1 seconds for Gemma/Qwen respectively.
These are observations, not a fixed cost or a latency guarantee. Where Qwen
already reads freely, both policies often make the same number of calls. On the
conflict pair, free took 122.6 s and required 67.5 s with the same three calls;
completion lengths differed substantially. Do not interpret that single timing
reversal as evidence that forcing reads speeds the model up generally.

Across the six selected questions (not six repeats of one question):

| Model / policy | Calls | Summed turn seconds | Total provider tokens |
| --- | ---: | ---: | ---: |
| Gemma free | 11 | 65.336 | 27,088 |
| Gemma required | 13 | 75.247 | 32,206 |
| Qwen free | 14 | 347.291 | 36,604 |
| Qwen required | 15 | 319.108 | 38,207 |

The model/runtime is noticeably slower on several nontrivial requests. Generation
defaults, including any reasoning behavior, were preserved; time spent reasoning
was not isolated. Changing model, not merely enabling
first-read obligation, is the more consequential quality intervention here.
Required access guarantees neither relevant selection nor complete utilization.
Keep it experimental/configurable rather than treating it as a solved recall policy.

## Carousel evidence and cleanup

In the first deterministic eight-step cycle, seven recalls demote to RAM, six
evict to disk-only, with eight disk loads, eight CUDA uploads and 23 downloads.
Content hashes match and all owned CUDA buffers are released. Qwen's actual
three-node recovery walk also produces RAM and SSD demotions, so physical movement
is observed during autonomous navigation, not just in the separate scripted cycle.
GPU samples in that first report reach 81% on GPU 0 and 99% on GPU 2; these are
device-level samples, not exclusive per-process attribution.

After all tests Qwen, loaded only for this experiment, was unloaded. The original
Gemma instance and its settings remain loaded. GPU memory returned to the initial
6,935/14/14 MiB, with zero utilization at the final snapshot. Main config/bible
and personal memory remain unchanged. Automated checks pass: 254 Python tests
discovered (seven optional skips), 19 JavaScript tests, Ruff clean.
