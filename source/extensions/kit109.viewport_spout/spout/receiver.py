"""SpoutReceiver — receive pixel data from any Spout sender."""
import ctypes
from . import _lib


class SpoutReceiver:
    def __init__(self, sender_name: str = ""):
        self._h = _lib._create_handle()
        if sender_name:
            fn = _lib._vtbl_fn(self._h, _lib.V_SET_RECEIVER_NAME, None, [ctypes.c_char_p])
            fn(self._h, sender_name.encode())

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.release()

    def __del__(self):
        self.release()

    def _fn(self, index, restype, argtypes):
        return _lib._vtbl_fn(self._h, index, restype, argtypes)

    def receive(self) -> bool:
        fn = self._fn(_lib.V_RECEIVE_TEXTURE, ctypes.c_bool,
                      [ctypes.c_uint, ctypes.c_uint, ctypes.c_bool, ctypes.c_uint])
        return bool(fn(self._h, 0, 0, False, 0))

    def receive_image(self, buffer, width: int, height: int,
                      gl_format: int = _lib.GL_RGBA, invert: bool = False) -> bool:
        if isinstance(buffer, (bytearray, memoryview)):
            buf = (ctypes.c_ubyte * len(buffer)).from_buffer(buffer)
        else:
            buf = buffer
        fn = self._fn(_lib.V_RECEIVE_IMAGE, ctypes.c_bool,
                      [ctypes.c_char_p, ctypes.c_uint, ctypes.c_bool, ctypes.c_uint])
        return bool(fn(self._h, buf, gl_format, invert, 0))

    def release(self):
        if self._h:
            fn = self._fn(_lib.V_RELEASE_RECEIVER, None, [])
            fn(self._h)
            fn2 = self._fn(_lib.V_RELEASE, None, [])
            fn2(self._h)
            self._h = None

    @property
    def is_connected(self) -> bool:
        return bool(self._fn(_lib.V_IS_CONNECTED, ctypes.c_bool, [])(self._h))

    @property
    def is_updated(self) -> bool:
        return bool(self._fn(_lib.V_IS_UPDATED, ctypes.c_bool, [])(self._h))

    @property
    def is_frame_new(self) -> bool:
        return bool(self._fn(_lib.V_IS_FRAME_NEW, ctypes.c_bool, [])(self._h))

    @property
    def sender_name(self) -> str:
        result = self._fn(_lib.V_GET_SENDER_NAME, ctypes.c_char_p, [])(self._h)
        return result.decode() if result else ""

    @property
    def sender_width(self) -> int:
        return self._fn(_lib.V_GET_SENDER_WIDTH, ctypes.c_uint, [])(self._h)

    @property
    def sender_height(self) -> int:
        return self._fn(_lib.V_GET_SENDER_HEIGHT, ctypes.c_uint, [])(self._h)

    @property
    def sender_fps(self) -> float:
        return self._fn(_lib.V_GET_SENDER_FPS, ctypes.c_double, [])(self._h)

    @property
    def sender_frame(self) -> int:
        return self._fn(_lib.V_GET_SENDER_FRAME, ctypes.c_long, [])(self._h)
