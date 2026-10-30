param([switch]$Close,[switch]$Carry)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$auditDir = Join-Path $projectRoot ('release/motion-v038/runtime' + $(if ($Close) {'-close'} else {''}))
if ($Carry) {$auditDir = Join-Path $projectRoot 'release/motion-v038/carry-native'}
New-Item -ItemType Directory -Force -Path $auditDir | Out-Null
$engineExe = Join-Path $projectRoot 'tools/vendor/godot-4.7.2/Godot_v4.7.2-stable_win64.exe'
$stdoutPath = Join-Path $auditDir 'capture.log'
$stderrPath = Join-Path $auditDir 'capture-err.log'
$arguments = '--path "' + (Join-Path $projectRoot 'game25d') + '" --position 3200,100 --fixed-fps 60 --write-movie "' + (Join-Path $auditDir 'motion.avi') + '" --script res://tests/motion_runtime.gd'
if ($Close) {$arguments += ' -- --motion-close'}
if ($Carry) {$arguments = '--path "' + (Join-Path $projectRoot 'game25d') + '" --position 3200,100 --fixed-fps 60 --write-movie "' + (Join-Path $auditDir 'motion.avi') + '" --script res://tests/carry_motion.gd -- --fresh --save-slot=qa-carry-native-v038.json --carry-output=' + (Join-Path $auditDir 'samples.json')}
$captureRun = Start-Process -FilePath $engineExe -ArgumentList $arguments -WindowStyle Hidden -PassThru -RedirectStandardOutput $stdoutPath -RedirectStandardError $stderrPath
$captureHandle = $captureRun.Handle
$deadline = [DateTime]::UtcNow.AddMinutes(5)
while (-not $captureRun.WaitForExit(500)) {
    if ((Select-String -LiteralPath $stderrPath -Pattern 'SCRIPT ERROR|Parse Error|^ERROR:' -Quiet) -or [DateTime]::UtcNow -gt $deadline) {
        Stop-Process -Id $captureRun.Id
        throw 'Motion capture failed or timed out; inspect capture-err.log'
    }
}
if ($captureRun.ExitCode -ne 0) {throw 'Motion capture exited unsuccessfully'}
if (Select-String -LiteralPath $stderrPath -Pattern 'SCRIPT ERROR|Parse Error|^ERROR:' -Quiet) {throw 'Motion capture script error'}
$trimArguments = @()
if (-not $Carry) {$trimArguments = @('-t','26.5')}
& ffmpeg -v error -y -i (Join-Path $auditDir 'motion.avi') @trimArguments -c:v libx264 -preset fast -crf 20 -pix_fmt yuv420p -c:a aac -movflags +faststart (Join-Path $auditDir 'motion.mp4')
if ($LASTEXITCODE -ne 0) {throw 'Motion encoding failed'}
Write-Output ('Motion captured: ' + $auditDir)
