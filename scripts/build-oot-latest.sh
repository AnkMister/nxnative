#!/bin/zsh
set -euo pipefail

if [[ ${OOT_LOW_PRIORITY:-0} != 1 ]]; then
    exec taskpolicy -b nice -n 19 env OOT_LOW_PRIORITY=1 /bin/zsh "$0" "$@"
fi

REPO=/Users/ankur/Documents/Crypt/Gaming-rea/nxnative
RUN_ROOT=${OOT_BUILD_ROOT:-/Users/ankur/Documents/Crypt/Gaming-rea/_work/games/oot-latest}
PYTHON=/Users/ankur/Documents/Crypt/Gaming-rea/nxnative/.venv/bin/python
NSP='/Users/ankur/Documents/Crypt/Gaming-rea/_work/games/oot/The Legend of Zelda Ocarina of Time.nup'

if pgrep -x dmhost >/dev/null; then
    print -u2 'Quit dmhost before starting this full build.'
    exit 2
fi
cd "$REPO"
[[ $(git branch --show-current) == oot-latest ]] || { print -u2 'Wrong branch: expected oot-latest.'; exit 2; }
git diff --quiet && git diff --cached --quiet || { print -u2 'Commit source changes before the full build.'; exit 2; }
"$PYTHON" -c 'import shutil,sys; free=shutil.disk_usage(sys.argv[1]).free; print(f"Build disk headroom: {free // 2**30} GiB"); sys.exit(0 if free >= 64*2**30 else "At least 64 GiB free is required for the isolated full build.")' "$RUN_ROOT"
[[ -f "$NSP" ]] || { print -u2 "Missing NUP: $NSP"; exit 2; }

# Upstream profile and chain inputs. Do not inherit old experimental chain flags.
for name in ${(k)parameters}; do
    if [[ $name == DMSH_* ]]; then unset "$name"; fi
done
unset IOSOUT XLATE SPIRV_CROSS DMSH_CAS DMSH_PREFILL WORK DM_GAMES_DIR DM_GAMES_FIRST DM_OOT_BRENT DM_SDK22_SERVICES DM_NVN_GMEM_COMMIT
export GAME=0400486024DEC000 DM_GAME=0400486024DEC000
export J=12 MAKEFLAGS=-j12 DM_REWRITE_J=12 DM_PSO_J=12 DM_METAL_PACK_THREADS=12
export DOTNET_ROOT="$HOME/.dotnet"
export NUGET_PACKAGES=/Users/ankur/Documents/Crypt/Gaming-rea/_work/nxnative/oot-play-evidence/nuget-packages
export RestoreConfigFile="$RUN_ROOT/pipeline-inputs/NuGet.Config"
export NuGetAudit=false
export DOTNET_CLI_TELEMETRY_OPTOUT=1
export PATH="${PYTHON:h}:$DOTNET_ROOT:/opt/homebrew/bin:$PATH"
export TMPDIR="$RUN_ROOT/scratch"
mkdir -p "$TMPDIR"
export WORK="$RUN_ROOT/compiler-work.noindex"
mkdir -p "$WORK"
export DOTNET_CLI_HOME="$RUN_ROOT/dotnet-home"
export DMSH_HMMA_CHAIN=0
export PYTHONUNBUFFERED=1
export DMSH_TARGETS=mac
export XLATE="$REPO/dm/gfx/tools/dmsh_xlate_bin/dmsh_xlate"
export DM_AOT=1 DM_AOT_STRICT=1 DM_AOT_REBASE_SEEN=1
export DM_PSO_USER="$RUN_ROOT/pipeline-inputs/pso_user.tsv"
export DM_PSO_SEEN="$RUN_ROOT/pipeline-inputs/pso_seen.jsonl"

# The live file is copied only after dmhost has exited. Saved sessions remain immutable.
"$PYTHON" "$RUN_ROOT/pipeline-inputs/collect-census.py"
# Keep authoritative tables unchanged; add only census-proven BF variants in an external copy.
DM_GAMES_DIR=$("$PYTHON" "$RUN_ROOT/pipeline-inputs/prepare-profile.py" "$REPO")
export DM_GAMES_DIR
export DM_GAMES_FIRST=1
git rev-parse HEAD > "$RUN_ROOT/build-source-head.txt"
"$PYTHON" dm/gfx/tools/tool_lock.py --check-tools
"$PYTHON" -m unittest dm.tools.tests.test_nsp_chain

# Runtime AOT stays off in env.txt; the offline archive builder above stays on.
# The .noindex ancestor excludes all intermediate shader files from Spotlight.
exec "$PYTHON" scripts/build_ipa_from_nsp.py "$NSP" \
    --platform mac-app --progress lines --no-seen-shaders --no-heap-check \
    --work-dir "$RUN_ROOT/0400486024DEC000_build.noindex" \
    --out "$RUN_ROOT/The Legend of Zelda - Ocarina of Time.app" \
    --env-file "$RUN_ROOT/env.txt"
