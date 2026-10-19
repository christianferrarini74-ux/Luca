# Physical synaptic carousel — Phase 1.09

Date: 2026-10-19

[Italiano](it/fase-1-sinapsi/09-memoria-fisica.md) · [Dependency audit](dependency-audit.md)

This milestone supersedes the logical-cache limitation in Phases 1.07 and 1.08.
The task is physical storage and transfer of complete knowledge nodes, initially
with small/synthetic content. Real-library evaluation is reserved for joint work
with Christian. Integration with Cesare is explicitly excluded.

## Storage contract

| Layer | CUDA backend | Lifetime |
| --- | --- | --- |
| Disk / SSD | SQLite contains the complete persistent nodes and directed graph. | Survives cache eviction and restart. |
| RAM | Python objects contain warm, complete nodes. | Bounded by node count and serialized-payload budget. |
| VRAM | Explicit `cuMemAlloc_v2` device allocations contain serialized complete nodes, including sections. | Owned by Luca; released on eviction, reset and shutdown. |

GPU slot metadata on the host contains only IDs, device pointers, lengths and
SHA-256 digests. It does not retain a second CPU payload cache. Reading a node
for the planner, dashboard or LLM creates a transient host copy using
`cuMemcpyDtoH_v2`. Upload uses `cuMemcpyHtoD_v2` and checks an actual readback
before committing the replacement. Downloads verify SHA-256 before decoding.
The LLM still receives selected text through the connector; these allocations
are not model weights, KV cache or an inference-engine integration.

On recall, a RAM hit avoids a SQLite node load. A GPU hit downloads from its
allocation. Otherwise the node is decoded from SQLite into host memory before
upload. Evicted GPU payloads are downloaded into the warm RAM slot. RAM overflow
removes the retained host copy: the complete persistent copy is already on disk,
so eviction does not rewrite the document. A later cold recall loads it again.

All graph, focus and LRU decisions remain in the Core. GPU allocation is a
storage backend, not a new semantic ranking mechanism. Edges are still indexed
in SQLite, with active graph metadata in CPU RAM; this milestone moves node
payloads, not the graph indexes or every Core object, onto the GPU.

## Configuration and dependencies

```yaml
runtime:
  memory_backend: cuda
  gpu_device: 1
  vram_capacity: 5
  ram_capacity: 12
  vram_bytes: 8000000
  ram_bytes: 32000000
frontend:
  enabled: true
```

Start normally with `python run_luca.py`. CUDA ordinals are zero-based. The
current machine has three RTX 5060 Ti devices; ordinal 1 was selected to keep
node allocations away from the current inference process on GPU 0. Select an
available ordinal in `config.yaml` on another machine. Capacity is per selected
GPU; this is not a multi-GPU sharding implementation.

Only PyYAML is required beyond Python's standard library. The driver binding
uses `ctypes` and the NVIDIA driver library (`nvcuda.dll` on Windows,
`libcuda.so.1` on Linux). Neither a CUDA Toolkit installation nor PyTorch/CuPy is
required for these byte transfers. Windows/NVIDIA is hardware-validated; the
Linux loading path has not been hardware-tested.

`memory_backend: host` explicitly selects the previous CPU reference behavior.
It is useful for portable tests and is visibly labeled HOST in the cockpit.
Missing backend keys retain this reference default for older configurations;
the checked-in runtime configuration explicitly selects CUDA. A failed CUDA
initialization, allocation or copy never silently selects HOST.

## Limits and failure handling

- Complete CUDA node payloads are never replaced by partial cache views. A
  single node larger than `vram_bytes` is rejected with an actionable error;
  increase the budget rather than silently truncating it.
- Cluster count/byte overflow keeps the most relevant prefix of the requested
  batch and sends the other complete nodes through the warm tier. A node larger
  than the RAM payload budget bypasses that cache; its source remains on disk.
- Batch uploads are staged and verified before replacing existing device
  entries or removing RAM copies. Allocation/copy/integrity failure releases
  staged buffers and preserves previous slot membership. Actual device-loss or
  free failures are surfaced; recovery from a driver reset is not implemented.
- Staging temporarily needs additional VRAM alongside old allocations. The
  slot budget measures retained serialized bytes, not total peak GPU usage.
  Driver contexts, allocation granularity and other applications also consume
  memory. Host budgets are payload bounds, not Python process RSS limits.
- A retained primary-context reference is pushed/popped on the calling thread;
  the API serializes Core work. Reset creates a replacement slot and closes the
  old one. Shutdown frees buffers and releases only Luca's context reference,
  not the inference application's resources. Partial startup/bind failures close
  owned resources as well.
- Explicit device allocations are real, not host dictionaries labeled VRAM.
  Windows WDDM and the driver still manage physical residency/paging. We do not
  claim pinned, non-pageable GPU residency. SQLite/OS caches can likewise serve
  reads without an actual SSD transaction on each recall.

## Diagnostics

`GET /api/state` includes `physical_memory`: backend, selected GPU, owned
allocation count/bytes, actual copied byte totals and operation counts, and
driver-reported free/total device memory. It also counts carousel SQLite node
loads and their serialized payload sizes. These SQLite counters are not raw
disk I/O metrics and exclude unrelated index/dashboard queries.

The cockpit displays the active backend and device prominently, with transfer
counts in the memory controls. Reading snapshots itself downloads GPU content;
these copies are included in totals. Tiny allocations need not change the
rounded GPU usage shown by `nvidia-smi`; owned pointer/length bookkeeping is
reported separately from device-wide free memory.

## Reproducible checks

```powershell
python -m unittest discover -s tests
$env:LUCA_TEST_CUDA = '1'
$env:LUCA_TEST_GPU = '1'
python -m unittest discover -s tests
python -m luca_memory.hardware_check
```

`hardware_check` reads configuration, but never opens the configured personal
database or loads its seed. It creates a temporary synthetic SQLite database
under the configured storage directory and removes it after closing resources.
It copies a 1,650,000-byte synthetic chapter, forces GPU/RAM eviction, reloads
it from disk and verifies identical content hashes. Output includes actual
driver-operation counters and the cleanup result. `--device` can override the
configured ordinal for this diagnostic only.

Validation: 92 tests pass with real CUDA enabled (89 portable tests and three
hardware tests). Coverage includes Unicode/sections, complete payloads,
count/byte eviction, simulated allocation failure/corruption, no fallback,
cross-thread reads, disk reopen, real HTTP worker recall, reset, shutdown and
zero remaining owned buffers. JavaScript syntax and targeted rendering checks
are separate from these tests. No broad visual-browser audit or performance
comparison is claimed.

Normal startup and reset no longer replace existing knowledge when the number
of nodes changes. A seed-version mismatch fails instead of refreshing the
database destructively. Explicit experimental seed-loading functions remain
destructive by design and must not be used as personal-library migrations.

Next: evaluate the real library together with Christian. No personal library
was opened or modified during this milestone's hardware tests.

A separate live smoke test used the configured LM Studio model and a temporary
experimental database with the CUDA backend. The three-turn submarine dialogue
kept focus on yellow vehicles before switching to the dogs' red vehicles; all
Luca-owned device buffers were released afterwards. This checks compatibility,
not broad model accuracy or real-library quality.
