param([string]$Version = '0.45')
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$gameProject = Join-Path $projectRoot 'game25d'
$engineExe = Join-Path $projectRoot 'tools/vendor/godot-4.7.2/Godot_v4.7.2-stable_win64.exe'
$outputDir = Join-Path $projectRoot ('dist/LastTrain-' + $Version + '-25D')
$logDir = Join-Path $projectRoot 'release'
$qaRunDir = Join-Path $logDir ('build-' + $Version)
New-Item -ItemType Directory -Force -Path $outputDir | Out-Null
New-Item -ItemType Directory -Force -Path $qaRunDir | Out-Null
function Invoke-GodotStep([string]$Step, [string]$Arguments) {
    $stdoutPath = Join-Path $qaRunDir ($Step + '.log')
    $stderrPath = Join-Path $qaRunDir ($Step + '-err.log')
    $nativeProcess = Start-Process -FilePath $engineExe -ArgumentList $Arguments -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput $stdoutPath -RedirectStandardError $stderrPath
    if ($nativeProcess.ExitCode -ne 0) { throw ($Step + ': exit ' + $nativeProcess.ExitCode) }
    $errors = Select-String -LiteralPath $stdoutPath,$stderrPath -Pattern 'SCRIPT ERROR|Parse Error|^ERROR:'
    if ($errors) { throw ($Step + ': engine error. See ' + $stderrPath) }
}
Invoke-GodotStep 'import-25d' ('--headless --path "' + $gameProject + '" --editor --import')
Invoke-GodotStep 'qa-25d' ('--headless --path "' + $gameProject + '" --quit-after 500 --script res://tests/gameplay.gd -- --qa-report="' + (Join-Path $qaRunDir 'base-gameplay.json') + '"')
Invoke-GodotStep 'qa-expedition' ('--headless --path "' + $gameProject + '" --script res://tests/expedition_routes.gd -- --fresh --save-slot=qa-build-routes.json --qa-report="' + (Join-Path $qaRunDir 'first-routes.json') + '"')
Invoke-GodotStep 'qa-expedition-reload' ('--headless --path "' + $gameProject + '" --script res://tests/expedition_reload.gd -- --fresh --save-slot=qa-build-reload.json --qa-report="' + (Join-Path $qaRunDir 'first-reload.json') + '"')
Invoke-GodotStep 'qa-hospital-rules' ('--headless --path "' + $gameProject + '" --script res://tests/hospital_rules.gd -- --fresh --save-slot=qa-build-hospital-rules.json --qa-report="' + (Join-Path $qaRunDir 'hospital-rules.json') + '"')
Invoke-GodotStep 'qa-campaign-transition' ('--headless --path "' + $gameProject + '" --script res://tests/campaign_transition.gd -- --fresh --save-slot=qa-build-transition.json --qa-report="' + (Join-Path $qaRunDir 'campaign-transition.json') + '"')
Invoke-GodotStep 'qa-exit' ('--headless --path "' + $gameProject + '" --script res://tests/chapter1_exit_rules.gd -- --fresh --save-slot=qa-build-exit.json --qa-report="' + (Join-Path $qaRunDir 'exit-rules.json') + '"')
Invoke-GodotStep 'qa-motion' ('--headless --path "' + $gameProject + '" --script res://tests/motion_rules.gd -- --qa-report="' + (Join-Path $qaRunDir 'motion-rules.json') + '"')
Invoke-GodotStep 'qa-foundation' ('--headless --fixed-fps 60 --path "' + $gameProject + '" --script res://tests/foundation_rules.gd -- --fresh --save-slot=qa-build-foundation.json --qa-report="' + (Join-Path $qaRunDir 'foundation-rules.json') + '"')
Invoke-GodotStep 'qa-environment' ('--headless --fixed-fps 60 --path "' + $gameProject + '" --script res://tests/environment_rules.gd -- --fresh --save-slot=qa-build-environment.json --qa-report="' + (Join-Path $qaRunDir 'environment-rules.json') + '"')
Invoke-GodotStep 'qa-locations' ('--headless --fixed-fps 60 --path "' + $gameProject + '" --script res://tests/locations_controls.gd -- --fresh --save-slot=qa-build-locations.json --qa-report="' + (Join-Path $qaRunDir 'locations-controls.json') + '"')
Invoke-GodotStep 'qa-hospital-power' ('--headless --fixed-fps 60 --path "' + $gameProject + '" --script res://tests/hospital_tour.gd -- --fresh --save-slot=qa-build-hospital-power.json --tour-output="' + (Join-Path $qaRunDir 'hospital-power') + '"')
Invoke-GodotStep 'qa-hospital-winch' ('--headless --fixed-fps 60 --path "' + $gameProject + '" --script res://tests/hospital_tour.gd -- --fresh --save-slot=qa-build-hospital-winch.json --method=winch --tour-output="' + (Join-Path $qaRunDir 'hospital-winch') + '"')
Invoke-GodotStep 'qa-first-stopper' ('--headless --fixed-fps 60 --path "' + $gameProject + '" --script res://tests/chapter1_tour.gd -- --fresh --save-slot=qa-build-first-stopper.json --tour-output="' + (Join-Path $qaRunDir 'first-stopper') + '"')
Invoke-GodotStep 'qa-first-power' ('--headless --fixed-fps 60 --path "' + $gameProject + '" --script res://tests/chapter1_tour.gd -- --fresh --save-slot=qa-build-first-power.json --method=power --tour-output="' + (Join-Path $qaRunDir 'first-power') + '"')
Invoke-GodotStep 'qa-forest' ('--headless --fixed-fps 60 --path "' + $gameProject + '" --script res://tests/environment_tour.gd -- --fresh --save-slot=qa-build-forest.json --landscape=forest --tour-output="' + (Join-Path $qaRunDir 'forest') + '"')
Invoke-GodotStep 'qa-wasteland' ('--headless --fixed-fps 60 --path "' + $gameProject + '" --script res://tests/environment_tour.gd -- --fresh --save-slot=qa-build-wasteland.json --landscape=wasteland --tour-output="' + (Join-Path $qaRunDir 'wasteland') + '"')
Invoke-GodotStep 'export-25d' ('--headless --path "' + $gameProject + '" --export-release "Windows Desktop" "' + (Join-Path $outputDir 'LastTrain.exe') + '"')
$licenseDir = Join-Path $outputDir 'licenses'
New-Item -ItemType Directory -Force -Path $licenseDir | Out-Null
Copy-Item -LiteralPath (Join-Path $projectRoot 'release/licenses-25d/LICENSE.txt') -Destination (Join-Path $licenseDir 'Godot-MIT.txt')
Copy-Item -LiteralPath (Join-Path $projectRoot 'release/licenses-25d/COPYRIGHT.txt') -Destination (Join-Path $licenseDir 'Godot-third-party.txt')
Copy-Item -LiteralPath (Join-Path $gameProject 'assets/audio/Kenney-CC0.txt') -Destination $licenseDir
Copy-Item -LiteralPath (Join-Path $gameProject 'assets/characters/motion-v38/UAL-CC0.txt') -Destination $licenseDir
Copy-Item -LiteralPath (Join-Path $gameProject 'LICENSES.txt') -Destination $outputDir
Copy-Item -LiteralPath (Join-Path $projectRoot 'design/run-campaign-ru.txt') -Destination (Join-Path $outputDir 'README-RU.txt')
$digest = Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $outputDir 'LastTrain.exe')
$manifest = [ordered]@{version=$Version; engine='Godot 4.7.2'; renderer='Forward+'; sha256=$digest.Hash; release_ready=$false; campaign_migrated=$false; human_playtest=$false; target_minutes_min=240; target_minutes_max=300; scope='Foundation fixes: sight/noise AI, animation-delayed enemy contact, generator reload, queued dialogue and persistent journal, full pause and saved audio preferences, hospital objectives. Three environment themes. Full hospital evacuation and campaign remain in development'}
$manifest | ConvertTo-Json | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $outputDir 'build-manifest.json')
Write-Output ('Built: ' + $outputDir)
Write-Output ('SHA256: ' + $digest.Hash)
