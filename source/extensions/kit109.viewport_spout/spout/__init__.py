"""
spout — Python bindings for Spout2 GPU texture sharing (Windows only).
Bundled inside kit109.viewport_spout extension.
"""
from .sender   import SpoutSender
from .receiver import SpoutReceiver
from .utils    import SpoutUtils
from ._lib import (
    GL_RGBA,
    GL_BGRA,
    GL_BGRA_EXT,
    LOG_SILENT,
    LOG_VERBOSE,
    LOG_NOTICE,
    LOG_WARNING,
    LOG_ERROR,
    LOG_FATAL,
    LOG_NONE,
)

__all__ = [
    "SpoutSender", "SpoutReceiver", "SpoutUtils",
    "GL_RGBA", "GL_BGRA", "GL_BGRA_EXT",
    "LOG_SILENT", "LOG_VERBOSE", "LOG_NOTICE",
    "LOG_WARNING", "LOG_ERROR", "LOG_FATAL", "LOG_NONE",
]
