# Weak-network tool lock (phase 1)

## Chosen stack

| Piece | Choice | License | Why |
|-------|--------|---------|-----|
| Shaping | `weaknet_proxy.py` (Python stdlib) | Project / Apache-2.0 compatible | No MITM, CONNECT tunnel + delay/bandwidth/loss; no extra binary |
| Device bind | `adb reverse` + `settings put global http_proxy` | Android platform-tools | Matches existing MobileDeviceService trust model |
| Entrypoint | `weaknet.ps1` (Windows), `weaknet.sh` (optional) | Project | apply / status / restore / run |

## Explicitly rejected (phase 1)

- Charles / GUI limiters — not scriptable for restore
- mitmproxy decrypt — HTTPS interception out of scope
- toxiproxy alone — needs per-host port mapping, poor whole-device UX
- Cloud RF control — not available on local USB devices

## Fallback

If the App ignores system `http_proxy`:

1. Connect phone Wi‑Fi → Manual proxy → PC LAN IP + pack port (see README)
2. Still run `weaknet.ps1 apply` so local shaping is up; skip relies on Wi‑Fi proxy instead of `adb reverse` only when documented

## Start / stop

- Start: `python weaknet_proxy.py --config profile.json --port <port> --pidfile .weaknet.pid`
- Stop: kill PID from `.weaknet.state.json` / pidfile; PowerShell `Stop-Process`
- State file: `.weaknet.state.json` next to scripts (active, serial, port, profile code)
