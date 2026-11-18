#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
ROOT="$PWD"
export HOME="$ROOT/.home" DOTNET_CLI_HOME="$ROOT/.dotnet-home"
export NUGET_PACKAGES="$ROOT/.nuget/packages" NUGET_HTTP_CACHE_PATH="$ROOT/.nuget/http-cache" NUGET_PLUGINS_CACHE_PATH="$ROOT/.nuget/plugins-cache"
export XDG_RUNTIME_DIR="$ROOT/.runtime"
export TMPDIR="$ROOT/.tmp" DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1 DOTNET_SKIP_FIRST_TIME_EXPERIENCE=1
mkdir -p "$HOME" "$DOTNET_CLI_HOME" "$NUGET_PACKAGES" "$NUGET_HTTP_CACHE_PATH" "$NUGET_PLUGINS_CACHE_PATH" "$TMPDIR" "$XDG_RUNTIME_DIR" logs TestResults
chmod 700 "$XDG_RUNTIME_DIR"
if [[ -n "${DOTNET:-}" ]]; then
  : # Пользователь явно указал исполняемый файл.
else
  DOTNET=dotnet # SDK должен находиться в PATH.
fi
{
  echo "SDK: $("$DOTNET" --version)"
  echo "Command: dotnet test Lab3.sln -c Release --logger trx --results-directory TestResults --collect XPlat\ Code\ Coverage"
  "$DOTNET" test Lab3.sln -c Release --logger 'trx;LogFileName=lab3.trx' --results-directory TestResults --collect 'XPlat Code Coverage' --verbosity normal
} 2>&1 | tee logs/dotnet-test.log
