# Dependency audit — 2026-10-19

[Italiano](it/dependency-audit.md)

The active application is Python plus a bundled HTML/CSS/JavaScript cockpit.
`run_luca.py` starts one Python HTTP server; it does not launch a Node process.

| Component | Decision | Reason |
| --- | --- | --- |
| Python 3.11+ | Keep | Application runtime; SQLite, HTTP, JSON, hashing, tests and native calls use its standard library. |
| PyYAML | Keep | The only imported third-party Python package. Preserves the agreed `config.yaml` interface and comments without maintaining our own YAML parser. |
| SQLite | Keep | Included through Python's `sqlite3` module; no database server or extra Python package. |
| NVIDIA driver | Required only for CUDA mode | Supplies the native driver library. It remains a real platform dependency, even without pip packages. |
| CUDA Toolkit / nvcc | Not required for node transfers | Allocation and byte copies use the driver API; no GPU kernels are compiled. |
| PyTorch / CuPy / CUDA Python | Not required | The small native binding uses standard-library `ctypes`. |
| LM Studio | Keep behind the connector | External inference application for the configured language adapter; not the owner of Luca's GPU allocations. Rules-only tests do not need it. |
| Browser | Keep | Displays the cockpit; no CDN resources or JavaScript runtime server are required. |
| Setuptools | Build-time only | Used by packaging/editable installation, not by the running application. |
| pip | Installation tooling | Not imported by the application. |
| Old `gui/` tree | Removed from the active checkout | 76 tracked files, 19 direct and 16 development dependencies were unused by startup. Their full history remains recoverable in Git. |

The former GUI's lockfile and package manifest were removed together; no active
Node dependencies remain. Installed software, `node_modules`, virtual environments,
drivers and unrelated processes were not deleted or altered by this cleanup.
Old `frontend.directory`, `frontend.url` and `frontend.api_url` settings are obsolete:
the cockpit is served by the API at the configured bind address and port.

Trade-off: our native GPU binding is small but must own ABI declarations, error
handling, context lifetime, transfer integrity and cleanup tests. CUDA mode is
NVIDIA-specific. A separate explicit `host` reference backend remains usable on
machines without NVIDIA; it is never presented as physical VRAM.

Upstream references: [NVIDIA driver dependency FAQ](https://developer.nvidia.com/cuda/faq),
[CUDA memory management API](https://docs.nvidia.com/cuda/cuda-driver-api/cuda_driver_api/group__CUDA__MEM.html).
