Effekt Weak Network Pack
========================

Requirements
- Windows: PowerShell 5+, Python 3, adb in PATH, Android USB device (debug on)
- Optional: macOS/Linux use ./weaknet.sh

Quick start
1) Unzip this pack
2) USB-connect Android phone, accept debugging
3) .\weaknet.ps1 apply
4) Use the App under weak network
5) .\weaknet.ps1 status
6) .\weaknet.ps1 restore   (ALWAYS restore when finished)

Commands
- apply   Start local shaping proxy, adb reverse, set device http_proxy
- status  Show active flag, serial, port, profile
- restore Stop proxy, clear device proxy, remove reverse (safe to re-run)
- run -- <cmd>   apply, run command, then restore

If App ignores system proxy (fallback)
1) Keep apply running (proxy listens on PC)
2) Phone Wi-Fi -> Advanced -> Proxy Manual
3) Host = your PC LAN IP, Port = value in status (default 18888)
4) When done: restore AND clear Wi-Fi proxy on phone

Notes
- No HTTPS decryption / no Charles certificate
- profile.json is frozen at download time
- Override device: set WEAKNET_SERIAL=xxxx before apply
