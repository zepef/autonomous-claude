# Test Lab Network Connectivity
# Run after VMs are set up

Write-Host "=== AI-Defender Lab Connectivity Test ===" -ForegroundColor Cyan

$tests = @(
    @{Name = "Host Network Adapter"; IP = "10.0.0.1"; Port = $null},
    @{Name = "Kali VM"; IP = "10.0.0.10"; Port = 22},
    @{Name = "DVWA Target"; IP = "10.0.0.20"; Port = 80}
)

$results = @()

foreach ($test in $tests) {
    Write-Host "`nTesting $($test.Name) ($($test.IP))..." -ForegroundColor Yellow

    # Ping test
    $ping = Test-Connection -ComputerName $test.IP -Count 2 -Quiet -ErrorAction SilentlyContinue

    if ($ping) {
        Write-Host "  [PASS] Ping successful" -ForegroundColor Green

        # Port test if specified
        if ($test.Port) {
            try {
                $tcpClient = New-Object System.Net.Sockets.TcpClient
                $tcpClient.ConnectAsync($test.IP, $test.Port).Wait(2000) | Out-Null
                if ($tcpClient.Connected) {
                    Write-Host "  [PASS] Port $($test.Port) open" -ForegroundColor Green
                    $tcpClient.Close()
                }
            } catch {
                Write-Host "  [WARN] Port $($test.Port) closed/filtered" -ForegroundColor Yellow
            }
        }
        $results += @{Name = $test.Name; Status = "OK"}
    } else {
        Write-Host "  [FAIL] Ping failed" -ForegroundColor Red
        $results += @{Name = $test.Name; Status = "FAIL"}
    }
}

# Test honeypot endpoint (if running)
Write-Host "`nTesting Honeypot endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://10.0.0.1:5000/health" -TimeoutSec 5 -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        Write-Host "  [PASS] Honeypot responding" -ForegroundColor Green
    }
} catch {
    Write-Host "  [INFO] Honeypot not running yet (expected)" -ForegroundColor Cyan
}

# Summary
Write-Host "`n=== Summary ===" -ForegroundColor Cyan
$passed = ($results | Where-Object { $_.Status -eq "OK" }).Count
$total = $results.Count
Write-Host "Tests passed: $passed / $total"

if ($passed -eq $total) {
    Write-Host "`nLab network is fully operational!" -ForegroundColor Green
} else {
    Write-Host "`nSome tests failed. Check VM status and network configuration." -ForegroundColor Yellow
    Write-Host @"

Troubleshooting:
1. Ensure VMs are running
2. Check host-only adapter is enabled on each VM
3. Verify static IPs are configured inside VMs
4. Check Windows Firewall isn't blocking

"@ -ForegroundColor White
}
