# Weak-network pack entry (Windows)
# Usage:
#   .\weaknet.ps1 apply
#   .\weaknet.ps1 status
#   .\weaknet.ps1 restore
#   .\weaknet.ps1 run -- <command...>

param(
    [Parameter(Position = 0)]
    [ValidateSet('apply', 'status', 'restore', 'run')]
    [string]$Command = 'status',
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Rest
)

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

$ProfilePath = Join-Path $Root 'profile.json'
$SessionPath = Join-Path $Root 'session.json'
$StatePath = Join-Path $Root '.weaknet.state.json'
$PidPath = Join-Path $Root '.weaknet.pid'
$DefaultPort = 18888

function Read-Json($path) {
    if (-not (Test-Path $path)) { return $null }
    return Get-Content -Raw -Encoding UTF8 $path | ConvertFrom-Json
}

function Write-State($obj) {
    ($obj | ConvertTo-Json -Depth 6) | Set-Content -Encoding UTF8 $StatePath
}

function Get-Adb {
    $adb = Get-Command adb -ErrorAction SilentlyContinue
    if ($adb) { return $adb.Source }
    throw 'adb not found in PATH. Install Android platform-tools.'
}

function Get-Serial($session) {
    if ($env:WEAKNET_SERIAL) { return $env:WEAKNET_SERIAL }
    if ($session -and $session.device_serial) { return [string]$session.device_serial }
    $adb = Get-Adb
    $lines = & $adb devices | Where-Object { $_ -match "`tdevice$" }
    if (-not $lines) { throw 'No adb device online. Connect USB device or set WEAKNET_SERIAL.' }
    return (($lines[0] -split "`t")[0].Trim())
}

function Test-PortOpen([int]$Port) {
    try {
        $c = New-Object System.Net.Sockets.TcpClient
        $iar = $c.BeginConnect('127.0.0.1', $Port, $null, $null)
        $ok = $iar.AsyncWaitHandle.WaitOne(800)
        if (-not $ok) { $c.Close(); return $false }
        $c.EndConnect($iar) | Out-Null
        $c.Close()
        return $true
    } catch { return $false }
}

function Invoke-Probe([int]$LatencyMs) {
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    try {
        # Probe through local proxy (HTTP). Failure is non-fatal if proxy is up.
        $proxy = New-Object System.Net.WebProxy("http://127.0.0.1:$DefaultPort")
        $req = [System.Net.HttpWebRequest]::Create('http://example.com/')
        $req.Proxy = $proxy
        $req.Timeout = 8000
        $req.Method = 'HEAD'
        $resp = $req.GetResponse()
        $resp.Close()
    } catch {
        # ignore — CONNECT/HTTP probe may fail in restricted networks
    }
    $sw.Stop()
    $elapsed = [int]$sw.ElapsedMilliseconds
    $expect = [Math]::Max(0, $LatencyMs - 50)
    if ($LatencyMs -gt 0 -and $elapsed -lt $expect) {
        Write-Host "PROBE degraded-but-active: RTT=${elapsed}ms (profile latency=${LatencyMs}ms); proxy is up."
        return 'degraded'
    }
    Write-Host "PROBE ok: RTT=${elapsed}ms (profile latency=${LatencyMs}ms)"
    return 'ok'
}

function Stop-ProxyIfAny {
    if (Test-Path $PidPath) {
        $pidText = (Get-Content -Raw $PidPath).Trim()
        if ($pidText -match '^\d+$') {
            $procId = [int]$pidText
            try { Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue } catch {}
        }
        Remove-Item $PidPath -Force -ErrorAction SilentlyContinue
    }
    Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -and $_.CommandLine -like '*weaknet_proxy.py*' -and $_.CommandLine -like "*$Root*" } |
        ForEach-Object { try { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue } catch {} }
}

function Clear-DeviceProxy($adb, $serial, $port) {
    & $adb -s $serial shell settings delete global http_proxy 2>$null | Out-Null
    & $adb -s $serial shell settings put global http_proxy :0 2>$null | Out-Null
    & $adb -s $serial reverse --remove tcp:$port 2>$null | Out-Null
}

function Do-Apply {
    $profile = Read-Json $ProfilePath
    $session = Read-Json $SessionPath
    if (-not $profile) { throw 'profile.json missing' }
    $adb = Get-Adb
    $serial = Get-Serial $session
    $port = $DefaultPort
    if ($session -and $session.proxy_port) { $port = [int]$session.proxy_port }

    Stop-ProxyIfAny
    Clear-DeviceProxy $adb $serial $port

    $py = Get-Command python -ErrorAction SilentlyContinue
    if (-not $py) { $py = Get-Command py -ErrorAction SilentlyContinue }
    if (-not $py) { throw 'python not found in PATH' }

    $proxyScript = Join-Path $Root 'weaknet_proxy.py'
    $argList = @($proxyScript, '--config', $ProfilePath, '--host', '127.0.0.1', '--port', "$port", '--pidfile', $PidPath)
    $proc = Start-Process -FilePath $py.Source -ArgumentList $argList -WorkingDirectory $Root -WindowStyle Hidden -PassThru
    Start-Sleep -Milliseconds 600
    if (-not (Test-PortOpen $port)) {
        throw "Proxy failed to listen on 127.0.0.1:$port"
    }

    & $adb -s $serial reverse tcp:$port tcp:$port | Out-Null
    & $adb -s $serial shell settings put global http_proxy "127.0.0.1:$port" | Out-Null

    $latency = 0
    if ($profile.latency_ms) { $latency = [int]$profile.latency_ms }
    $probe = Invoke-Probe $latency

    $state = [ordered]@{
        active           = $true
        pid              = $proc.Id
        port             = $port
        device_serial    = $serial
        profile_code     = $(if ($profile.preset_code) { $profile.preset_code } else { $profile.code })
        profile_name     = $(if ($profile.name) { $profile.name } else { '' })
        session_id       = $(if ($session.session_id) { $session.session_id } else { '' })
        applied_at       = (Get-Date).ToString('s')
        probe            = $probe
        http_proxy_value = "127.0.0.1:$port"
    }
    Write-State $state
    Write-Host "APPLY ok: serial=$serial port=$port profile=$($state.profile_code) probe=$probe"
    Write-Host "Tip: if App ignores system proxy, set Wi-Fi manual proxy to this PC LAN IP:$port (see README.txt)"
}

function Do-Status {
    $state = Read-Json $StatePath
    $profile = Read-Json $ProfilePath
    $port = $DefaultPort
    if ($state -and $state.port) { $port = [int]$state.port }
    $listening = Test-PortOpen $port
    $active = $false
    if ($state -and $state.active -and $listening) { $active = $true }
    $serial = if ($state) { $state.device_serial } else { '' }
    $code = if ($state -and $state.profile_code) { $state.profile_code } elseif ($profile) { $profile.preset_code } else { '' }
    Write-Host ("STATUS active={0} serial={1} port={2} profile={3} listening={4}" -f $active, $serial, $port, $code, $listening)
    if (-not $active -and (Test-Path $StatePath)) {
        Write-Host 'State file exists but proxy not listening — run restore then apply.'
    }
}

function Do-Restore {
    $state = Read-Json $StatePath
    $session = Read-Json $SessionPath
    $port = $DefaultPort
    if ($state -and $state.port) { $port = [int]$state.port }
    elseif ($session -and $session.proxy_port) { $port = [int]$session.proxy_port }

    Stop-ProxyIfAny

    try {
        $adb = Get-Adb
        $serial = $null
        if ($state -and $state.device_serial) { $serial = [string]$state.device_serial }
        elseif ($session) { $serial = Get-Serial $session }
        if ($serial) {
            Clear-DeviceProxy $adb $serial $port
            Write-Host "RESTORE device proxy cleared: serial=$serial"
        }
    } catch {
        Write-Host "RESTORE warning: $($_.Exception.Message)"
        Write-Host 'Manual: adb shell settings delete global http_proxy'
    }

    if (Test-Path $StatePath) {
        $cleared = [ordered]@{
            active        = $false
            restored_at   = (Get-Date).ToString('s')
            device_serial = $(if ($state) { $state.device_serial } else { '' })
            port          = $port
        }
        Write-State $cleared
    }
    Write-Host 'RESTORE ok (idempotent).'
}

function Do-Run {
    Do-Apply
    try {
        if ($Rest -and $Rest.Count -gt 0) {
            if ($Rest[0] -eq '--') { $Rest = $Rest[1..($Rest.Count - 1)] }
            if ($Rest.Count -gt 0) {
                $exe = $Rest[0]
                $exeArgs = @()
                if ($Rest.Count -gt 1) { $exeArgs = $Rest[1..($Rest.Count - 1)] }
                & $exe @exeArgs
                $code = $LASTEXITCODE
                if ($null -eq $code) { $code = 0 }
                exit $code
            }
        }
        Write-Host 'No command after run; weak network left applied. Call restore when done.'
    } finally {
        if ($Rest -and $Rest.Count -gt 0) {
            Do-Restore
        }
    }
}

switch ($Command) {
    'apply' { Do-Apply }
    'status' { Do-Status }
    'restore' { Do-Restore }
    'run' { Do-Run }
}
