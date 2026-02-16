# app/openclaw_client.py

import json
import os
import time
import base64
import hashlib
import hmac
import socket
import subprocess

import websocket


GATEWAY_HOST = os.getenv("OPENCLAW_GATEWAY_HOST", "127.0.0.1")
GATEWAY_PORT = int(os.getenv("OPENCLAW_GATEWAY_PORT", "4840"))
OPENCLAW_TOKEN = os.getenv("OPENCLAW_TOKEN", "")
OPENCLAW_SECRET = os.getenv("OPENCLAW_SECRET", "")
UDS_PATH = os.getenv("OPENCLAW_UDS_PATH", os.path.expanduser("~/.openclaw/gateway.sock"))


def _make_hmac(payload_bytes: bytes) -> str:
    return hmac.new(
        OPENCLAW_SECRET.encode(), payload_bytes, hashlib.sha256
    ).hexdigest()


def _send_ws_message(action: str, params: dict = None) -> dict:
    """Send a message to the OpenClaw Gateway over WebSocket and return the response."""
    url = f"ws://{GATEWAY_HOST}:{GATEWAY_PORT}/node"
    payload = {
        "action": action,
        "params": params or {},
        "token": OPENCLAW_TOKEN,
        "ts": int(time.time()),
    }
    payload_bytes = json.dumps(payload).encode()
    if OPENCLAW_SECRET:
        payload["hmac"] = _make_hmac(payload_bytes)

    ws = websocket.create_connection(url, timeout=30)
    try:
        ws.send(json.dumps(payload))
        result = json.loads(ws.recv())
        return result
    finally:
        ws.close()


def _send_uds_message(action: str, params: dict = None) -> dict:
    """Send a message via Unix Domain Socket (local-only, faster path)."""
    payload = {
        "action": action,
        "params": params or {},
        "token": OPENCLAW_TOKEN,
        "ts": int(time.time()),
    }
    payload_bytes = json.dumps(payload).encode()
    if OPENCLAW_SECRET:
        payload["hmac"] = _make_hmac(payload_bytes)

    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.settimeout(30)
    try:
        sock.connect(UDS_PATH)
        sock.sendall(json.dumps(payload).encode() + b"\n")
        chunks = []
        while True:
            chunk = sock.recv(65536)
            if not chunk:
                break
            chunks.append(chunk)
        return json.loads(b"".join(chunks))
    finally:
        sock.close()


def send(action: str, params: dict = None) -> dict:
    """Send a command to OpenClaw, preferring UDS when available."""
    if os.path.exists(UDS_PATH):
        try:
            return _send_uds_message(action, params)
        except (ConnectionRefusedError, FileNotFoundError, OSError):
            pass
    return _send_ws_message(action, params)


# --- High-level helpers wrapping OpenClaw native tools ---


def canvas_snapshot(output_path: str = None) -> str:
    """Capture a screenshot via OpenClaw's canvas.snapshot.
    Returns the path to the saved image."""
    result = send("canvas.snapshot")
    img_data = result.get("data", {}).get("image_b64", "")
    if not img_data:
        raise RuntimeError(f"canvas.snapshot failed: {result}")

    if output_path is None:
        os.makedirs("images", exist_ok=True)
        output_path = "images/screen.png"

    with open(output_path, "wb") as f:
        f.write(base64.b64decode(img_data))
    return output_path


def canvas_navigate(url: str) -> dict:
    """Navigate the canvas (browser/webview) to a URL."""
    return send("canvas.navigate", {"url": url})


def canvas_eval(js_code: str) -> dict:
    """Execute JavaScript in the canvas context."""
    return send("canvas.eval", {"code": js_code})


def canvas_click(x: int, y: int) -> dict:
    """Click at coordinates via canvas.eval dispatching a pointer event."""
    js = f"""
    (function() {{
        var el = document.elementFromPoint({x}, {y});
        if (el) {{
            el.dispatchEvent(new PointerEvent('pointerdown', {{clientX:{x}, clientY:{y}, bubbles:true}}));
            el.dispatchEvent(new PointerEvent('pointerup', {{clientX:{x}, clientY:{y}, bubbles:true}}));
            el.click();
        }}
    }})();
    """
    return canvas_eval(js)


def canvas_type(text: str) -> dict:
    """Type text into the currently focused element via canvas.eval."""
    escaped = json.dumps(text)
    js = f"""
    (function() {{
        var el = document.activeElement;
        if (el) {{
            el.value = (el.value || '') + {escaped};
            el.dispatchEvent(new Event('input', {{bubbles: true}}));
        }}
    }})();
    """
    return canvas_eval(js)


def canvas_swipe(x1: int, y1: int, x2: int, y2: int, duration_ms: int = 500) -> dict:
    """Simulate a swipe/scroll gesture via canvas pointer events."""
    steps = max(5, duration_ms // 50)
    js = f"""
    (async function() {{
        var el = document.elementFromPoint({x1}, {y1}) || document.body;
        el.dispatchEvent(new PointerEvent('pointerdown', {{clientX:{x1}, clientY:{y1}, bubbles:true}}));
        for (var i = 1; i <= {steps}; i++) {{
            var t = i / {steps};
            var cx = {x1} + ({x2} - {x1}) * t;
            var cy = {y1} + ({y2} - {y1}) * t;
            await new Promise(r => setTimeout(r, {duration_ms // steps}));
            el.dispatchEvent(new PointerEvent('pointermove', {{clientX:cx, clientY:cy, bubbles:true}}));
        }}
        el.dispatchEvent(new PointerEvent('pointerup', {{clientX:{x2}, clientY:{y2}, bubbles:true}}));
    }})();
    """
    return canvas_eval(js)


def camera_snap() -> str:
    """Take a photo using the Mac camera. Returns path to saved image."""
    result = send("camera.snap")
    img_data = result.get("data", {}).get("image_b64", "")
    if not img_data:
        raise RuntimeError(f"camera.snap failed: {result}")
    path = "images/camera_snap.png"
    os.makedirs("images", exist_ok=True)
    with open(path, "wb") as f:
        f.write(base64.b64decode(img_data))
    return path


def screen_record(duration_seconds: int = 5) -> dict:
    """Record the screen for a given duration."""
    return send("screen.record", {"duration": duration_seconds})


def system_run(command: str) -> dict:
    """Execute a system command via OpenClaw's system.run."""
    return send("system.run", {"command": command})


def system_notify(title: str, body: str) -> dict:
    """Show a macOS notification."""
    return send("system.notify", {"title": title, "body": body})


def get_screen_size_via_canvas() -> tuple:
    """Get screen dimensions from the canvas viewport."""
    result = canvas_eval("JSON.stringify({w: window.innerWidth, h: window.innerHeight})")
    data = result.get("data", {})
    if isinstance(data, str):
        data = json.loads(data)
    return data.get("w", 1440), data.get("h", 900)


def is_gateway_available() -> bool:
    """Check if the OpenClaw Gateway is reachable."""
    try:
        if os.path.exists(UDS_PATH):
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect(UDS_PATH)
            sock.close()
            return True
    except (ConnectionRefusedError, FileNotFoundError, OSError):
        pass

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        sock.connect((GATEWAY_HOST, GATEWAY_PORT))
        sock.close()
        return True
    except (ConnectionRefusedError, OSError):
        return False
