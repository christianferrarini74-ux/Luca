"""Small CUDA Driver API binding; no toolkit or third-party Python package."""

from contextlib import contextmanager
import ctypes as C
import os
import threading


class DeviceMemoryError(RuntimeError):
    """A physical device operation failed; never fall back to host storage."""


class CudaMemory:
    """Own one primary-context reference and explicitly allocated device buffers."""

    def __init__(self, device_index: int = 0):
        if C.sizeof(C.c_void_p) != 8:
            raise DeviceMemoryError("The CUDA storage backend requires 64-bit Python.")
        self._lock = threading.RLock()
        self._buffers = {}
        self.upload_bytes = self.download_bytes = 0
        self.uploads = self.downloads = 0
        self.closed = False
        try:
            self.lib = C.WinDLL(os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32", "nvcuda.dll")) if os.name == "nt" else C.CDLL("libcuda.so.1")
        except OSError as error:
            raise DeviceMemoryError("NVIDIA driver unavailable. Install/configure the driver or explicitly select memory_backend: host.") from error
        signatures = {
            "cuInit": [C.c_uint], "cuDeviceGetCount": [C.POINTER(C.c_int)],
            "cuDeviceGet": [C.POINTER(C.c_int), C.c_int],
            "cuDeviceGetName": [C.c_void_p, C.c_int, C.c_int],
            "cuDevicePrimaryCtxRetain": [C.POINTER(C.c_void_p), C.c_int],
            "cuDevicePrimaryCtxRelease_v2": [C.c_int],
            "cuCtxPushCurrent_v2": [C.c_void_p],
            "cuCtxPopCurrent_v2": [C.POINTER(C.c_void_p)],
            "cuMemAlloc_v2": [C.POINTER(C.c_uint64), C.c_size_t],
            "cuMemFree_v2": [C.c_uint64],
            "cuMemcpyHtoD_v2": [C.c_uint64, C.c_void_p, C.c_size_t],
            "cuMemcpyDtoH_v2": [C.c_void_p, C.c_uint64, C.c_size_t],
            "cuMemGetInfo_v2": [C.POINTER(C.c_size_t), C.POINTER(C.c_size_t)],
            "cuGetErrorString": [C.c_int, C.POINTER(C.c_char_p)],
        }
        try:
            for name, args in signatures.items():
                fn = getattr(self.lib, name)
                fn.argtypes, fn.restype = args, C.c_int
        except AttributeError as error:
            raise DeviceMemoryError("The installed NVIDIA driver lacks a required CUDA entry point.") from error
        self._call("cuInit", 0)
        count = C.c_int()
        self._call("cuDeviceGetCount", C.byref(count))
        if not 0 <= device_index < count.value:
            raise DeviceMemoryError(f"CUDA device {device_index} unavailable; detected {count.value} devices.")
        device = C.c_int()
        self._call("cuDeviceGet", C.byref(device), device_index)
        self.device = device.value
        self.device_index = device_index
        name = C.create_string_buffer(256)
        self._call("cuDeviceGetName", name, len(name), self.device)
        self.device_name = name.value.decode("utf-8", errors="replace")
        self.context = C.c_void_p()
        self._call("cuDevicePrimaryCtxRetain", C.byref(self.context), self.device)

    def _call(self, name, *args):
        code = getattr(self.lib, name)(*args)
        if code:
            message = C.c_char_p()
            self.lib.cuGetErrorString(code, C.byref(message))
            detail = message.value.decode("utf-8", errors="replace") if message.value else str(code)
            raise DeviceMemoryError(f"{name}: {detail} (CUDA {code})")

    @contextmanager
    def _current(self):
        with self._lock:
            if self.closed:
                raise DeviceMemoryError("CUDA memory is closed.")
            self._call("cuCtxPushCurrent_v2", self.context)
            try:
                yield
            finally:
                previous = C.c_void_p()
                self._call("cuCtxPopCurrent_v2", C.byref(previous))

    def upload(self, payload: bytes) -> int:
        if not payload:
            raise ValueError("A device payload cannot be empty.")
        with self._current():
            pointer = C.c_uint64()
            self._call("cuMemAlloc_v2", C.byref(pointer), len(payload))
            self._buffers[pointer.value] = len(payload)
            try:
                source = C.create_string_buffer(payload, len(payload))
                self._call("cuMemcpyHtoD_v2", pointer.value, source, len(payload))
            except BaseException:
                self.free(pointer.value)
                raise
            self.upload_bytes += len(payload)
            self.uploads += 1
            return pointer.value

    def download(self, pointer: int) -> bytes:
        with self._current():
            size = self._buffers[pointer]
            target = C.create_string_buffer(size)
            self._call("cuMemcpyDtoH_v2", target, pointer, size)
            self.download_bytes += size
            self.downloads += 1
            return target.raw

    def free(self, pointer: int):
        with self._current():
            if pointer in self._buffers:
                self._call("cuMemFree_v2", pointer)
                del self._buffers[pointer]

    def stats(self):
        with self._current():
            free, total = C.c_size_t(), C.c_size_t()
            self._call("cuMemGetInfo_v2", C.byref(free), C.byref(total))
            return {"backend": "cuda", "physical_vram": True,
                    "device_index": self.device_index, "device_name": self.device_name,
                    "allocated_bytes": sum(self._buffers.values()), "allocations": len(self._buffers),
                    "upload_bytes": self.upload_bytes, "download_bytes": self.download_bytes,
                    "uploads": self.uploads, "downloads": self.downloads,
                    "device_free_bytes": free.value, "device_total_bytes": total.value}

    def close(self):
        with self._lock:
            if self.closed:
                return
            for pointer in tuple(self._buffers):
                self.free(pointer)
            self._call("cuDevicePrimaryCtxRelease_v2", self.device)
            self.closed = True
