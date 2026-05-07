"""SpoutUtils — enumerate senders, query system state, manage memory buffers."""
import ctypes
from . import _lib


class SpoutUtils:
    def __init__(self):
        self._h = _lib._create_handle()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.release()

    def __del__(self):
        self.release()

    def _fn(self, index, restype, argtypes):
        return _lib._vtbl_fn(self._h, index, restype, argtypes)

    def release(self):
        if self._h:
            self._fn(_lib.V_RELEASE, None, [])(self._h)
            self._h = None

    def get_sender_count(self) -> int:
        return self._fn(_lib.V_GET_SENDER_COUNT, ctypes.c_int, [])(self._h)

    def get_sender(self, index: int) -> str:
        buf = ctypes.create_string_buffer(256)
        ok = self._fn(_lib.V_GET_SENDER, ctypes.c_bool,
                      [ctypes.c_int, ctypes.c_char_p, ctypes.c_int])(self._h, index, buf, 256)
        return buf.value.decode() if ok else ""

    def get_all_senders(self) -> list:
        return [self.get_sender(i) for i in range(self.get_sender_count())]

    def get_active_sender(self) -> str:
        buf = ctypes.create_string_buffer(256)
        ok = self._fn(_lib.V_GET_ACTIVE_SENDER, ctypes.c_bool, [ctypes.c_char_p])(self._h, buf)
        return buf.value.decode() if ok else ""

    def get_num_adapters(self) -> int:
        return self._fn(_lib.V_GET_NUM_ADAPTERS, ctypes.c_int, [])(self._h)

    def get_adapter_name(self, index: int) -> str:
        buf = ctypes.create_string_buffer(256)
        ok = self._fn(_lib.V_GET_ADAPTER_NAME, ctypes.c_bool,
                      [ctypes.c_int, ctypes.c_char_p, ctypes.c_int])(self._h, index, buf, 256)
        return buf.value.decode() if ok else ""

    def is_gldx_ready(self) -> bool:
        return bool(self._fn(_lib.V_IS_GLDX_READY, ctypes.c_bool, [])(self._h))
