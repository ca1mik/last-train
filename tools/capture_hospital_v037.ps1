$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$auditDir = Join-Path $projectRoot 'release/campaign-v037'
$engineExe = Join-Path $projectRoot 'tools/vendor/godot-4.7.2/Godot_v4.7.2-stable_win64.exe'
$stdoutPath = Join-Path $auditDir 'motion.log'
$stderrPath = Join-Path $auditDir 'motion-err.log'
$arguments = '--path "' + (Join-Path $projectRoot 'game25d') + '" --position 3200,100 --fixed-fps 60 --write-movie "' + (Join-Path $auditDir 'hospital-motion.avi') + '" --script res://tests/hospital_motion.gd -- --fresh --save-slot=qa-motion-v037.json'
$captureRun = Start-Process -FilePath $engineExe -ArgumentList $arguments -WindowStyle Hidden -PassThru -RedirectStandardOutput $stdoutPath -RedirectStandardError $stderrPath
$captureHandle = $captureRun.Handle
$deadline = [DateTime]::UtcNow.AddMinutes(4)
while (-not $captureRun.WaitForExit(500)) {
    if ((Select-String -LiteralPath $stderrPath -Pattern 'SCRIPT ERROR|Parse Error|^ERROR:' -Quiet) -or [DateTime]::UtcNow -gt $deadline) {
        Stop-Process -Id $captureRun.Id
        throw 'Hospital capture failed or timed out; inspect motion-err.log'
    }
}
if ($captureRun.ExitCode -ne 0) {throw 'Hospital capture exited unsuccessfully'}
if (Select-String -LiteralPath $stderrPath -Pattern 'SCRIPT ERROR|Parse Error|^ERROR:' -Quiet) {throw 'Hospital capture script error'}
& ffmpeg -v error -y -i (Join-Path $auditDir 'hospital-motion.avi') -c:v libx264 -preset fast -crf 20 -pix_fmt yuv420p -c:a aac -movflags +faststart (Join-Path $auditDir 'hospital-motion.mp4')
if ($LASTEXITCODE -ne 0) {throw 'Hospital movie encoding failed'}
Write-Output 'Hospital movie captured and encoded'
