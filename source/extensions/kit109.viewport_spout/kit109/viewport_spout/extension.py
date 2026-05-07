import asyncio
import os
import sys

import carb
import omni.ext
import omni.kit.app
import omni.kit.renderer_capture
import omni.ui as ui

# Add the extension root to sys.path so the bundled `spout` module is importable.
_HERE = os.path.dirname(os.path.abspath(__file__))
_EXT_ROOT = os.path.dirname(os.path.dirname(_HERE))
if _EXT_ROOT not in sys.path:
    sys.path.insert(0, _EXT_ROOT)

# Lazy-loaded so import errors surface in on_startup and get logged.
SpoutSender = None
GL_BGRA_EXT = None


def _load_spout():
    global SpoutSender, GL_BGRA_EXT
    if SpoutSender is not None:
        return True
    try:
        from spout.sender import SpoutSender as _SS
        from spout._lib import GL_BGRA_EXT as _FMT
        SpoutSender = _SS
        GL_BGRA_EXT = _FMT
        return True
    except Exception as exc:
        carb.log_error(f"[SpoutSender] Failed to import spout: {exc}")
        import traceback
        carb.log_error(traceback.format_exc())
        return False


class ViewportSpoutExtension(omni.ext.IExt):

    def on_startup(self, _ext_id):
        carb.log_info("[SpoutSender] on_startup")
        self._streaming = False
        self._capture_pending = False
        self._sender = None
        self._drawable_sub = None
        self._hydra_texture = None
        self._status_label = None

        if not _load_spout():
            carb.log_error("[SpoutSender] Spout unavailable — extension disabled")
            return

        self._renderer_capture = omni.kit.renderer_capture.acquire_renderer_capture_interface()
        asyncio.ensure_future(self._build_ui_async())

    def on_shutdown(self):
        self._stop_streaming()
        if self._window:
            self._window.destroy()
            self._window = None
        self._renderer_capture = None

    # ------------------------------------------------------------------ #
    # UI
    # ------------------------------------------------------------------ #

    async def _build_ui_async(self):
        app = omni.kit.app.get_app()
        for _ in range(5):
            await app.next_update_async()
        self._window = ui.Window("Spout Viewport Sender", width=340, height=100)
        self._window.visible = True
        with self._window.frame:
            with ui.VStack(height=0, spacing=8):
                with ui.HStack(height=30, spacing=6):
                    ui.Button("Start Streaming", clicked_fn=self._start_streaming)
                    ui.Button("Stop Streaming", clicked_fn=self._stop_streaming)
                self._status_label = ui.Label("● Idle", style={"color": 0xFF888888})

    def _set_status(self, text: str, color: int):
        if self._status_label:
            self._status_label.text = f"● {text}"
            self._status_label.set_style({"color": color})

    # ------------------------------------------------------------------ #
    # Streaming control
    # ------------------------------------------------------------------ #

    def _start_streaming(self):
        if self._streaming:
            return

        from omni.kit.viewport.utility import get_active_viewport
        import omni.hydratexture
        from carb.eventdispatcher import get_eventdispatcher

        viewport_api = get_active_viewport()
        if viewport_api is None:
            carb.log_error("[SpoutSender] No active viewport found")
            self._set_status("Error: no viewport", 0xFF0000FF)
            return

        hydra_texture = viewport_api._hydra_texture
        if hydra_texture is None:
            carb.log_error("[SpoutSender] Viewport has no hydra_texture")
            self._set_status("Error: no hydra_texture", 0xFF0000FF)
            return

        try:
            self._sender = SpoutSender("OmniverseViewport")
        except Exception as exc:
            carb.log_error(f"[SpoutSender] Failed to create sender: {exc}")
            self._set_status(f"Error: {exc}", 0xFF0000FF)
            return

        self._hydra_texture = hydra_texture
        self._streaming = True
        self._capture_pending = False

        self._drawable_sub = get_eventdispatcher().observe_event(
            observer_name="kit109.viewport_spout:drawable_changed",
            event_name=omni.hydratexture.GLOBAL_EVENT_DRAWABLE_CHANGED,
            on_event=self._on_drawable_changed,
            filter=hydra_texture.get_event_key()
        )
        self._set_status("Streaming  ·  'OmniverseViewport'", 0xFF00CC00)
        carb.log_info("[SpoutSender] Streaming viewport as 'OmniverseViewport'")

    def _stop_streaming(self):
        if not self._streaming:
            return
        self._streaming = False
        self._drawable_sub = None
        self._hydra_texture = None
        if self._sender:
            self._sender.release()
            self._sender = None
        self._set_status("Idle", 0xFF888888)
        carb.log_info("[SpoutSender] Stopped")

    # ------------------------------------------------------------------ #
    # Per-frame capture
    # ------------------------------------------------------------------ #

    def _on_drawable_changed(self, event):
        """Fired by hydra_texture once per rendered viewport frame."""
        if not self._streaming or self._capture_pending:
            return
        result_handle = event["result_handle"]
        rp_resource = self._hydra_texture._get_drawable_ldr_resource(result_handle)
        if rp_resource is None:
            return
        self._capture_pending = True
        self._renderer_capture.capture_next_frame_rp_resource_callback(
            self._on_frame_captured, rp_resource
        )

    def _on_frame_captured(self, buf, buf_size, w, h, fmt):
        try:
            if not self._streaming or not self._sender:
                return
            # Extract the raw pointer from the PyCapsule — zero extra copies.
            # The readback buffer is owned by the capture system; we read it
            # in-place and Spout uploads it directly to the shared DX11 texture.
            import ctypes
            _get_ptr = ctypes.pythonapi.PyCapsule_GetPointer
            _get_ptr.restype = ctypes.c_void_p
            _get_ptr.argtypes = [ctypes.py_object, ctypes.c_char_p]
            ptr = _get_ptr(buf, None)
            if not ptr:
                return
            self._sender.send_image(ptr, int(w), int(h), GL_BGRA_EXT)
        except Exception as exc:
            carb.log_error(f"[SpoutSender] Frame error: {exc}")
        finally:
            self._capture_pending = False
