# kit109.viewport_spout

Real-time **Spout** GPU texture streaming of the active viewport for **NVIDIA Omniverse Kit 109**.

Stream the rendered viewport (no UI chrome) of any Kit-based app to Spout-aware applications such as **TouchDesigner**, **Resolume**, **OBS**, **MadMapper**, etc. — Windows only.

![status](https://img.shields.io/badge/platform-windows--x86_64-blue) ![kit](https://img.shields.io/badge/Kit-109-76b900) ![license](https://img.shields.io/badge/license-MIT-green)

---

## What it does

- Captures the **viewport-only LDR color** (BGRA8) — no UI, no overlays
- Sends it via **Spout2** GPU texture sharing as a sender named `OmniverseViewport`
- Runs at the viewport's render rate, with a frame-pending guard that drops frames if readback is slower than render rate
- Adds a small **Spout Viewport Sender** UI window with Start / Stop buttons and live status

## How the pipeline works

1. Subscribe to `omni.hydratexture.GLOBAL_EVENT_DRAWABLE_CHANGED` filtered to the active viewport's `hydra_texture` event key — fires once per rendered viewport frame.
2. Resolve the LDR `RpResource` via `hydra_texture._get_drawable_ldr_resource(result_handle)`.
3. Trigger an async GPU→CPU readback through `omni.kit.renderer.capture.IRendererCapture.capture_next_frame_rp_resource_callback`.
4. In the callback, extract the raw pointer from the `PyCapsule` with `ctypes.pythonapi.PyCapsule_GetPointer` and pass it as `c_void_p` directly to `SpoutSender.send_image(ptr, w, h, GL_BGRA_EXT)` — zero extra Python copies.

Total copies: **GPU → CPU readback** (unavoidable from Python) + **CPU → GPU upload** into the Spout DX11 shared texture.

## Requirements

- Windows 10/11 x64
- NVIDIA Omniverse **Kit SDK 109** (or any Kit 109 application — USD Composer, custom apps built from `kit-app-template`, etc.)
- DirectX 11 capable GPU
- A Spout receiver to display the stream (TouchDesigner Spout In TOP, Resolume, etc.)

## Install

### Option A — drop into a `kit-app-template` repo

1. Copy `source/extensions/kit109.viewport_spout/` into your repo's `source/extensions/` directory.
2. Add the extension to your `.kit` file's `[dependencies]`:
   ```toml
   "kit109.viewport_spout" = {}
   ```
3. Rebuild: `.\repo.bat build` — the build creates a junction from `_build/.../exts/` back to the source folder.
4. Launch: `.\repo.bat launch`. The **Spout Viewport Sender** window appears; click **Start Streaming**.

### Option B — register as an external extension search path

If you don't want to copy the folder, point Kit's extension manager at this repo's `source/extensions/` directory and enable `kit109.viewport_spout` from the Extension Manager UI.

## Usage

Open the **Spout Viewport Sender** window (auto-shown on extension load) and click **Start Streaming**. The sender appears as `OmniverseViewport` in any Spout-aware app.

To change the sender name, edit the literal in `kit109/viewport_spout/extension.py`:
```python
self._sender = SpoutSender("OmniverseViewport")
```

## Repo layout

```
source/extensions/kit109.viewport_spout/
├── config/
│   └── extension.toml          # Kit metadata + dependencies
├── kit109/
│   └── viewport_spout/
│       ├── __init__.py         # exports ViewportSpoutExtension
│       └── extension.py        # IExt: UI + capture pipeline
├── spout/                      # bundled Python ctypes bindings to Spout2
│   ├── __init__.py
│   ├── _lib.py                 # SpoutLibrary.dll loader + vtable indices
│   ├── sender.py               # SpoutSender wrapper
│   ├── receiver.py             # SpoutReceiver wrapper (not used here)
│   ├── utils.py                # SpoutUtils helpers
│   └── SpoutLibrary.dll        # Spout2 v2.007.017 (x64)
└── premake5.lua                # links kit109/ and spout/ into target_dir
```

## Gotchas (the hard-won lessons)

- `kit109/viewport_spout/__init__.py` **must** import the class — `from .extension import ViewportSpoutExtension`. If empty, Kit silently finds no `IExt` and never calls `on_startup`. No error is logged.
- `SpoutLibrary.dll` **must** sit inside the `spout/` package. The Carb-tokens fallback path is unreliable — keep the DLL bundled.
- `ctypes` argtype for the pixel buffer in `sender.py`'s `send_image` vtable call must be **`c_void_p`**, not `c_char_p`, or you get `argument 2: TypeError: wrong type`.
- Module-level imports of `spout` fail silently if the DLL is missing — Kit swallows the `ImportError` and marks the extension "started" with no class instantiated. Imports are kept lazy inside `on_startup` to surface them.
- The build creates **Windows junctions** at `_build/windows-x86_64/release/exts/kit109.viewport_spout/` pointing back to the source. Python edits are picked up live, no rebuild needed. If real directories already exist there (e.g. from a manual `cp -r`), the build errors out — delete them and rebuild.

## Credits

- **Spout2** — <https://spout.zeal.co/> (BSD-2-Clause). `SpoutLibrary.dll` is built from the upstream Spout2 SDK.
- **SpoutForPython** — <https://github.com/leadedge/SpoutForPython>. The bundled ctypes layout was inspired by this project; the bindings here are a from-scratch reimplementation to avoid the ABI drift in the upstream wrappers.
- **NVIDIA Omniverse Kit SDK** — capture pipeline relies on `omni.kit.renderer.capture` and `omni.kit.hydra_texture`.

## License

This extension is released under the **MIT License** — see [LICENSE](LICENSE).

`SpoutLibrary.dll` is distributed under the upstream **BSD-2-Clause** Spout2 license.
