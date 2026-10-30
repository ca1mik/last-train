$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$auditDir = Join-Path $projectRoot 'release/expedition-v036'
$engineExe = Join-Path $projectRoot 'tools/vendor/godot-4.7.2/Godot_v4.7.2-stable_win64.exe'
$stdoutPath = Join-Path $auditDir 'carry-motion.log'
$stderrPath = Join-Path $auditDir 'carry-motion-err.log'
$arguments = '--path "' + (Join-Path $projectRoot 'game25d') + '" --position 3200,100 --fixed-fps 60 --write-movie "' + (Join-Path $auditDir 'carry-motion.avi') + '" --script res://tests/carry_motion.gd -- --fresh --save-slot=qa-carry-motion-v036.json'
$captureRun = Start-Process -FilePath $engineExe -ArgumentList $arguments -WindowStyle Hidden -PassThru -RedirectStandardOutput $stdoutPath -RedirectStandardError $stderrPath
$captureHandle = $captureRun.Handle
$deadline = [DateTime]::UtcNow.AddMinutes(3)
while (-not $captureRun.WaitForExit(500)) {
    if ((Select-String -LiteralPath $stderrPath -Pattern 'SCRIPT ERROR|Parse Error|^ERROR:' -Quiet) -or [DateTime]::UtcNow -gt $deadline) {
        Stop-Process -Id $captureRun.Id
        throw 'Carry capture failed or timed out; inspect carry-motion-err.log'
    }
}
if ($captureRun.ExitCode -ne 0) {throw 'Carry capture exited unsuccessfully'}
if (Select-String -LiteralPath $stderrPath -Pattern 'SCRIPT ERROR|Parse Error|^ERROR:' -Quiet) {throw 'Carry capture script error'}
& ffmpeg -v error -y -i (Join-Path $auditDir 'carry-motion.avi') -c:v libx264 -preset fast -crf 20 -pix_fmt yuv420p -c:a aac -movflags +faststart (Join-Path $auditDir 'carry-motion.mp4')
if ($LASTEXITCODE -ne 0) {throw 'Carry movie encoding failed'}
Write-Output 'Carry movie captured and encoded'
