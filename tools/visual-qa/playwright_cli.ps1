param([Parameter(ValueFromRemainingArguments=$true)][string[]]$CliArguments)
# Windows adapter for the official skill's Bash wrapper; uses locked local CLI.
$ErrorActionPreference = 'Stop'
& (Join-Path $PSScriptRoot 'node_modules/.bin/playwright-cli.cmd') --config (Join-Path $PSScriptRoot 'cli.config.json') @CliArguments
exit $LASTEXITCODE
