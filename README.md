# Luca

[English](README.md) | [Italiano](README.it.md)

Luca is an experimental **external synaptic-memory system for LLMs**. It manages
persistent knowledge nodes, directed addresses, canonical content families and
bounded SSD/RAM/VRAM working sets. The LLM supplies language and reasoning;
Luca supplies explicit, navigable memory. It is not a new language model.

## Scope

Luca owns storage, indexes, focus/navigation, atomic mutations and local arc
reorganization during inactivity. External producers create and partition the
knowledge. PDF import, distillation, book/library creation, LLM training and
Cesare integration are outside the current scope.

The bundled chat, graph and dashboard are test consumers. They show and request
Core operations; they do not implement memory logic or certify model answers.

## How memory works

- A node contains articulated text, not necessarily a word. An arc is the directed
  pair `(source_id, target_id)`; it does not contain a semantic assertion.
- A family is an explicit root A and its parts An. Reading a part retains A's
  external identity and shared complete directory. Ordinary neighbors are not
  automatically family members.
- The global index returns possible entry IDs/titles. The fast directory exposes
  all first-degree incoming/outgoing addresses and family parts independently of
  payload residency. Seeing an address is not reading the target's content.
- SQLite retains the persistent source; bounded host RAM and, with the CUDA
  backend, real GPU allocations hold working payloads. GPU residency is not LLM
  knowledge: selected text must still fit the model's prompt budget.
- One owning runtime performs revision-checked atomic updates. Direct SQL writes
  and independent concurrent writers are not supported integration interfaces.

During automatic sleep, only roots exceeding the configured external degree
limit are candidates. With the distributed 50/45 settings, the LLM labels the
complete neighborhood by topic; a deterministic planner builds only the routing
groups needed to reach 45 exactly when compatible single-level capacity suffices.
Unknown or insufficient classifications do not authorize unrelated merges.
Manual confirmation, cancellation on renewed activity and guarded undo are available.

Read the [integration contract](docs/memory-integration-contract.md) before
producing nodes, and the [routing specification](docs/category-routing-planner.md)
before changing maintenance. The [executable producer example](examples/memory_contract.py)
uses a new database, not the user's existing memory.

## Start the test application

Python 3.11+ is required. PyYAML is the only declared application dependency;
setuptools builds the package. Node.js is not required to run the GUI.

From the repository root, a Windows virtual environment is recommended:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe run_luca.py
```

There is one application entry point: `run_luca.py` reads `config.yaml`, starts
the Python HTTP server and opens the bundled cockpit at
`http://127.0.0.1:8765/`. No separate frontend shell, Vite or Node server is needed.
Use **Esci** for orderly shutdown; restart after Python/config changes.

Before launching with the supplied config:

- Start LM Studio's local server at `http://127.0.0.1:1234` and install the configured
  `google/gemma-4-e2b` model. Luca requests loading an installed model, but does not
  download models or launch LM Studio itself.
- Review `storage.directory` (currently `D:/Test/Luca`) for this machine.
- Review `runtime.memory_backend` and `gpu_device`: supplied config uses real CUDA
  storage on ordinal 1. Select an available device, or explicitly choose `host`
  for host-only tiers; host mode does not exercise physical VRAM.

[Configuration](docs/configuration.md), [dashboard/API boundary](docs/gui-runtime.md)
and [LLM connector](docs/llm-connector.md) explain the operational details.
The distributed database is `luca_library.sqlite` with an empty seed; synthetic
fixtures stay separate. Do not refresh a populated library with a seed loader.

## Verification and limits

```powershell
python -m unittest discover -s tests -v
```

Latest portable checkpoint: **300 Python tests, OK with seven optional
hardware/service skips**; 19 JavaScript checks and Ruff passed. Node is needed
only for the frontend development tests:

```powershell
node --test tests/test_graph_frontend.js tests/test_cockpit_frontend.js
```

Opt-in diagnostics use disposable databases:

```powershell
python -m luca_memory.sleep_check --repeat 2
python -m luca_memory.hardware_check
```

The first requires LM Studio; the second requires a suitable NVIDIA CUDA driver
and device. See the contract for prerequisites and the historical reports for
earlier hardware results. Do not equate skipped checks with a fresh GPU run.

With the current classification pipeline, two E2B and two 26B A4B live runs on
the controlled fixture all reached **52→45**, with intact routes and successful
reopening/undo. This does not prove semantic correctness for arbitrary topics,
unlimited storage, a universal speed benefit or equivalence to human memory.
Ambiguous labels, model-selected navigation and single-level routing capacity
remain explicit limitations. Larger/different providers are not automatically
certified by these tests.

## Documentation

[Documentation index](docs/README.md) | [Indice italiano](docs/it/INDICE.md).
Current guides are separated from dated designs, experiments and archived
startup instructions. Earlier demo commands and assertion-learning experiments
remain in the archive, not as the recommended entry point or product scope.
