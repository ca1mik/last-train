param([string]$Output = 'H:/game/release/capability-audit')
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$engineExe = Join-Path $projectRoot 'tools/vendor/godot-4.7.2/Godot_v4.7.2-stable_win64.exe'
$gameProject = Join-Path $projectRoot 'game25d'
New-Item -ItemType Directory -Force -Path $Output | Out-Null
function Run-NativeCheck([string]$Name, [string]$Arguments) {
    $stdoutPath = Join-Path $Output ($Name + '.log')
    $stderrPath = Join-Path $Output ($Name + '-err.log')
    $nativeCheck = Start-Process -FilePath $engineExe -ArgumentList $Arguments -WindowStyle Hidden -PassThru -RedirectStandardOutput $stdoutPath -RedirectStandardError $stderrPath
    # Keep the native handle before waiting; PowerShell can otherwise lose exit code.
    $nativeHandle = $nativeCheck.Handle
    if (-not $nativeCheck.WaitForExit(60000)) {
        Stop-Process -Id $nativeCheck.Id
        throw ($Name + ': timed out')
    }
    $nativeCheck.Refresh()
    if ($nativeCheck.ExitCode -ne 0) {throw ($Name + ': nonzero exit; inspect logs')}
    $errors = Select-String -LiteralPath $stdoutPath,$stderrPath -Pattern 'SCRIPT ERROR|Parse Error|^ERROR:'
    if ($errors) {throw ($Name + ': engine error; inspect logs')}
    Write-Output ($Name + ': process and error-log checks passed')
}
Run-NativeCheck 'poses' ('--path "' + $gameProject + '" --position 3200,100 --resolution 1600x900 --script res://tests/character_audit.gd -- --audit-output=' + $Output + '/poses')
Run-NativeCheck 'scene' ('--path "' + $gameProject + '" --position 3200,100 --resolution 1600x900 -- --preview --capture=' + $Output + '/scene')
Run-NativeCheck 'gameplay' ('--headless --path "' + $gameProject + '" --script res://tests/gameplay.gd')
Copy-Item -LiteralPath (Join-Path $projectRoot 'release/gameplay-latest.json') -Destination (Join-Path $Output 'gameplay.json')
