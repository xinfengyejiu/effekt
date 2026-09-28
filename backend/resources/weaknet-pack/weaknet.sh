#!/usr/bin/env bash
# Weak-network pack entry (macOS/Linux) — mirror of weaknet.ps1
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
PROFILE="$ROOT/profile.json"
SESSION="$ROOT/session.json"
STATE="$ROOT/.weaknet.state.json"
PIDFILE="$ROOT/.weaknet.pid"
PORT=18888

cmd="${1:-status}"
shift || true

read_serial() {
  if [[ -n "${WEAKNET_SERIAL:-}" ]]; then
    echo "$WEAKNET_SERIAL"
    return
  fi
  if [[ -f "$SESSION" ]] && command -v python3 >/dev/null; then
    s="$(python3 -c "import json;print(json.load(open('$SESSION')).get('device_serial') or '')" 2>/dev/null || true)"
    if [[ -n "$s" ]]; then echo "$s"; return; fi
  fi
  adb devices | awk '/\tdevice$/{print $1; exit}'
}

stop_proxy() {
  if [[ -f "$PIDFILE" ]]; then
    kill "$(cat "$PIDFILE")" 2>/dev/null || true
    rm -f "$PIDFILE"
  fi
  pkill -f "weaknet_proxy.py --config $PROFILE" 2>/dev/null || true
}

clear_device() {
  local serial="$1" port="$2"
  adb -s "$serial" shell settings delete global http_proxy >/dev/null 2>&1 || true
  adb -s "$serial" shell settings put global http_proxy :0 >/dev/null 2>&1 || true
  adb -s "$serial" reverse --remove "tcp:$port" >/dev/null 2>&1 || true
}

do_apply() {
  [[ -f "$PROFILE" ]] || { echo "profile.json missing"; exit 1; }
  command -v adb >/dev/null || { echo "adb not found"; exit 1; }
  command -v python3 >/dev/null || { echo "python3 not found"; exit 1; }
  serial="$(read_serial)"
  [[ -n "$serial" ]] || { echo "No device serial"; exit 1; }
  stop_proxy
  clear_device "$serial" "$PORT"
  python3 "$ROOT/weaknet_proxy.py" --config "$PROFILE" --host 127.0.0.1 --port "$PORT" --pidfile "$PIDFILE" &
  sleep 0.6
  adb -s "$serial" reverse "tcp:$PORT" "tcp:$PORT"
  adb -s "$serial" shell settings put global http_proxy "127.0.0.1:$PORT"
  python3 - <<PY
import json, time
from pathlib import Path
profile=json.load(open("$PROFILE",encoding="utf-8"))
state={
  "active": True,
  "port": $PORT,
  "device_serial": "$serial",
  "profile_code": profile.get("preset_code") or profile.get("code") or "",
  "profile_name": profile.get("name") or "",
  "applied_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
  "http_proxy_value": "127.0.0.1:$PORT",
}
Path("$STATE").write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding="utf-8")
print("APPLY ok: serial=$serial port=$PORT profile=%s" % state["profile_code"])
PY
}

do_status() {
  python3 - <<PY
import json,socket
from pathlib import Path
port=$PORT
state={}
if Path("$STATE").exists():
  state=json.load(open("$STATE",encoding="utf-8"))
  port=int(state.get("port") or port)
listening=False
try:
  s=socket.create_connection(("127.0.0.1",port),timeout=0.4); s.close(); listening=True
except Exception:
  pass
active=bool(state.get("active")) and listening
print("STATUS active=%s serial=%s port=%s profile=%s listening=%s" % (
  active, state.get("device_serial",""), port, state.get("profile_code",""), listening))
PY
}

do_restore() {
  serial=""
  if [[ -f "$STATE" ]]; then
    serial="$(python3 -c "import json;print(json.load(open('$STATE')).get('device_serial') or '')" 2>/dev/null || true)"
  fi
  stop_proxy
  if [[ -n "$serial" ]]; then
    clear_device "$serial" "$PORT"
    echo "RESTORE device proxy cleared: serial=$serial"
  fi
  python3 - <<PY
import json,time
from pathlib import Path
Path("$STATE").write_text(json.dumps({
  "active": False,
  "restored_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
  "port": $PORT,
},ensure_ascii=False,indent=2),encoding="utf-8")
print("RESTORE ok (idempotent).")
PY
}

case "$cmd" in
  apply) do_apply ;;
  status) do_status ;;
  restore) do_restore ;;
  run)
    do_apply
    code=0
    if [[ $# -gt 0 ]]; then
      set +e
      "$@"
      code=$?
      set -e
      do_restore
      exit "$code"
    fi
    echo "No command after run; call restore when done."
    ;;
  *) echo "usage: $0 apply|status|restore|run"; exit 1 ;;
esac
