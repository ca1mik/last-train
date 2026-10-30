$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location -LiteralPath $projectRoot
try {
    $version = python -c "import lasttrain; print('.'.join(lasttrain.__version__.split('.')[:2]))"
    if ($LASTEXITCODE -ne 0) { throw 'Could not read version' }
    $package = Join-Path $projectRoot ('dist/LastTrain-' + $version)
    python tools/qa.py
    if ($LASTEXITCODE -ne 0) { throw 'Campaign, runtime or asset validation failed' }
    # PyInstaller writes ordinary INFO messages to stderr. Windows PowerShell
    # otherwise treats them as terminating errors when the caller redirects output.
    $builder = Start-Process -FilePath (Get-Command python).Source -ArgumentList '-m PyInstaller --noconfirm LastTrain.spec' -WindowStyle Hidden -PassThru -Wait -RedirectStandardOutput (Join-Path $projectRoot 'release/pyinstaller-out.log') -RedirectStandardError (Join-Path $projectRoot 'release/pyinstaller-err.log')
    if ($builder.ExitCode -ne 0) { throw 'Build failed; see release/pyinstaller-err.log' }
    Copy-Item -LiteralPath README.md -Destination (Join-Path $package 'README.md')
    Copy-Item -LiteralPath release/THIRD_PARTY_NOTICES.md -Destination (Join-Path $package 'THIRD_PARTY_NOTICES.md')
    $env:SDL_VIDEODRIVER = 'dummy'
    $env:SDL_AUDIODRIVER = 'dummy'
    $executable = Join-Path $package 'LastTrain.exe'
    $process = Start-Process -FilePath $executable -ArgumentList '--smoke-test' -WindowStyle Hidden -PassThru -Wait
    if ($process.ExitCode -ne 0) { throw 'Frozen executable failed' }
    python tools/record_build.py
    if ($LASTEXITCODE -ne 0) { throw 'Manifest failed' }
}
finally { Pop-Location }
