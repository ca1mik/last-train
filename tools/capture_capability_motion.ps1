$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$auditDir = Join-Path $projectRoot 'release/capability-audit'
$engineExe = Join-Path $projectRoot 'tools/vendor/godot-4.7.2/Godot_v4.7.2-stable_win64.exe'
$arguments = '--path "' + (Join-Path $projectRoot 'game25d') + '" --position 3200,100 --resolution 1280x720 --fixed-fps 60 --write-movie "' + (Join-Path $auditDir 'motion.avi') + '" --script res://tests/motion_review.gd'
$motionRun = Start-Process -FilePath $engineExe -ArgumentList $arguments -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $auditDir 'motion.log') -RedirectStandardError (Join-Path $auditDir 'motion-err.log')
$motionHandle = $motionRun.Handle
if (-not $motionRun.WaitForExit(600000)) {Stop-Process -Id $motionRun.Id; throw 'Motion capture timed out'}
if ($motionRun.ExitCode -ne 0) {throw 'Motion capture failed'}
if (Select-String -LiteralPath (Join-Path $auditDir 'motion.log'),(Join-Path $auditDir 'motion-err.log') -Pattern 'SCRIPT ERROR|^ERROR:') {throw 'Inspect engine motion logs'}
& ffmpeg -v error -y -i (Join-Path $auditDir 'motion.avi') -c:v libx264 -preset fast -crf 20 -pix_fmt yuv420p -c:a aac -movflags +faststart (Join-Path $auditDir 'motion.mp4')
if ($LASTEXITCODE -ne 0) {throw 'Motion encoding failed'}
Write-Output 'Captured and encoded actual native motion fixture'
