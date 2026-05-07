"""
SpoutSender — send pixel data (RGBA/BGRA images) to other Spout-aware applications.

Usage::

    from spout.sender import SpoutSender
    from spout._lib import GL_RGBA

    with SpoutSender("MySender") as sender:
        while True:
            pixels = get_frame_bytes()          # bytes/bytearray, width*height*4
            sender.send_image(pixels, 1920, 1080)
"""
import ctypes
from . import _lib


class SpoutSender:
    """
    Wraps the Spout sender side of SpoutLibrary.

    Parameters
    ----------
    name : str
        Sender name visible to other applications. Pass ``""`` or omit to let
        Spout assign a name based on the executable.
    """

    def __init__(self, name: str = ""):
        self._h = _lib._create_handle()
        if name:
            self._set_name(name)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.release()

    def __del__(self):
        self.release()

    def _fn(self, index, restype, argtypes):
        return _lib._vtbl_fn(self._h, index, restype, argtypes)

    def _set_name(self, name: str):
        fn = self._fn(_lib.V_SET_SENDER_NAME, None, [ctypes.c_char_p])
        fn(self._h, name.encode())

    def send_image(
        self,
        pixels,
        width: int,
        height: int,
        gl_format: int = _lib.GL_RGBA,
        invert: bool = False,
    ) -> bool:
        """
        Share a raw pixel buffer with connected receivers.

        Parameters
        ----------
        pixels : bytes | bytearray | ctypes array
            Pixel data. Must be exactly ``width * height * 4`` bytes.
        width, height : int
            Frame dimensions in pixels.
        gl_format : int
            GL_RGBA (default) or GL_BGRA_EXT.
        invert : bool
            Flip the image vertically before sharing (default False).
        """
        if isinstance(pixels, (bytes, bytearray, memoryview)):
            buf = (ctypes.c_ubyte * len(pixels)).from_buffer_copy(pixels)
        else:
            buf = pixels

        fn = self._fn(
            _lib.V_SEND_IMAGE,
            ctypes.c_bool,
            [ctypes.c_void_p, ctypes.c_uint, ctypes.c_uint,
             ctypes.c_uint, ctypes.c_bool],
        )
        return bool(fn(self._h, buf, ctypes.c_uint(width), ctypes.c_uint(height),
                       ctypes.c_uint(gl_format), ctypes.c_bool(invert)))

    def release(self):
        """Close the sender and free GPU resources."""
        if self._h:
            fn = self._fn(_lib.V_RELEASE_SENDER, None, [ctypes.c_ulong])
            fn(self._h, 0)
            fn2 = self._fn(_lib.V_RELEASE, None, [])
            fn2(self._h)
            self._h = None

    @property
    def is_initialized(self) -> bool:
        fn = self._fn(_lib.V_IS_INITIALIZED, ctypes.c_bool, [])
        return bool(fn(self._h))

    @property
    def name(self) -> str:
        fn = self._fn(_lib.V_GET_NAME, ctypes.c_char_p, [])
        result = fn(self._h)
        return result.decode() if result else ""

    @property
    def width(self) -> int:
        fn = self._fn(_lib.V_GET_WIDTH, ctypes.c_uint, [])
        return fn(self._h)

    @property
    def height(self) -> int:
        fn = self._fn(_lib.V_GET_HEIGHT, ctypes.c_uint, [])
        return fn(self._h)

    @property
    def fps(self) -> float:
        fn = self._fn(_lib.V_GET_FPS, ctypes.c_double, [])
        return fn(self._h)

    @property
    def frame(self) -> int:
        fn = self._fn(_lib.V_GET_FRAME, ctypes.c_long, [])
        return fn(self._h)

    @property
    def cpu_share(self) -> bool:
        fn = self._fn(_lib.V_GET_CPU, ctypes.c_bool, [])
        return bool(fn(self._h))

    @property
    def gldx_compatible(self) -> bool:
        fn = self._fn(_lib.V_GET_GLDX, ctypes.c_bool, [])
        return bool(fn(self._h))

    def hold_fps(self, fps: int):
        fn = self._fn(_lib.V_HOLD_FPS, None, [ctypes.c_int])
        fn(self._h, fps)

    def __repr__(self):
        return f"<SpoutSender name={self.name!r} {self.width}x{self.height}>"
