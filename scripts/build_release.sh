#!/usr/bin/env bash
set -euo pipefail

# 用法:
#   ./scripts/build_release.sh v0.1.0
# 不传则自动用当前 tag；没 tag 就用 commit 短哈希
VERSION="${1:-}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="$ROOT_DIR/frontend"
BACKEND_DIR="$ROOT_DIR/backend"

OUT_STAGING="$ROOT_DIR/dist_release"
PKG_NAME=""
ZIP_NAME=""

# ---- 版本号推断 ----
if [[ -z "$VERSION" ]]; then
  if git -C "$ROOT_DIR" describe --tags --exact-match >/dev/null 2>&1; then
    VERSION="$(git -C "$ROOT_DIR" describe --tags --exact-match)"
  else
    VERSION="dev-$(git -C "$ROOT_DIR" rev-parse --short HEAD)"
  fi
fi

PKG_NAME="DataFlow-WebUI-$VERSION"
ZIP_NAME="$PKG_NAME.zip"

echo "[build_release] VERSION=$VERSION"
echo "[build_release] PKG_NAME=$PKG_NAME"

# ---- 依赖检查（尽早失败）----
command -v node >/dev/null 2>&1 || { echo "node not found"; exit 1; }
command -v npm  >/dev/null 2>&1 || { echo "npm not found"; exit 1; }
command -v zip >/dev/null 2>&1 || { echo "zip not found (ubuntu: apt-get install zip)"; exit 1; }
command -v rsync >/dev/null 2>&1 || { echo "rsync not found (ubuntu: apt-get install rsync)"; exit 1; }

# ---- 清理 staging ----
rm -rf "$OUT_STAGING"
mkdir -p "$OUT_STAGING/$PKG_NAME"

# ---- 1) 构建前端 ----
echo "[build_release] Building frontend..."
pushd "$FRONTEND_DIR" >/dev/null
if [[ -f "package-lock.json" ]]; then
  npm ci
else
  # This repository currently tracks yarn.lock but it contains platform-specific
  # optional packages. Avoid mutating it during Linux release builds until the
  # project adopts one package manager and regenerates a portable lockfile.
  npm install --no-package-lock
fi
npm run build
popd >/dev/null

# dist 必须存在
if [[ ! -d "$FRONTEND_DIR/dist" ]]; then
  echo "[build_release] ERROR: frontend/dist not found after build."
  exit 1
fi

# ---- 2) 组装发布包：保持你的目录结构 backend/ + frontend/dist ----
echo "[build_release] Assembling package..."

# 2.1 后端：复制 backend/（排除 tests、cache、pycache 等）
rsync -a \
  --exclude "__pycache__" \
  --exclude ".venv" \
  --exclude ".pytest_cache" \
  --exclude "tests" \
  --exclude "cache_local" \
  "$BACKEND_DIR/" \
  "$OUT_STAGING/$PKG_NAME/backend/"

# 2.2 前端：只复制 dist（不带 node_modules/src 等）
mkdir -p "$OUT_STAGING/$PKG_NAME/frontend"
rsync -a --delete \
  "$FRONTEND_DIR/dist/" \
  "$OUT_STAGING/$PKG_NAME/frontend/dist/"

# 2.3 顶层文档
[[ -f "$ROOT_DIR/README-release-en.md" ]] && cp "$ROOT_DIR/README-release-en.md" "$OUT_STAGING/$PKG_NAME/"
[[ -f "$ROOT_DIR/README-release-zh.md" ]] && cp "$ROOT_DIR/README-release-zh.md" "$OUT_STAGING/$PKG_NAME/"
[[ -f "$ROOT_DIR/LICENSE" ]] && cp "$ROOT_DIR/LICENSE" "$OUT_STAGING/$PKG_NAME/" || true

# 2.4 被 release README 链接的文档。两个 README 都指向
# docs/RELEASE-PACKAGE.md；不打包它，用户解压后就是一个坏链接。
mkdir -p "$OUT_STAGING/$PKG_NAME/docs"
if [[ -f "$ROOT_DIR/docs/RELEASE-PACKAGE.md" ]]; then
  cp "$ROOT_DIR/docs/RELEASE-PACKAGE.md" "$OUT_STAGING/$PKG_NAME/docs/"
else
  echo "[build_release] ERROR: docs/RELEASE-PACKAGE.md not found, but the release READMEs link to it."
  exit 1
fi

# ---- 3) 一键启动脚本 ----
# 关键：从 release 根目录启动，保证 backend 里用 ../frontend/dist 能找到前端资源
# 绑定地址默认 127.0.0.1：本服务没有任何认证，且 pipeline 执行等于任意代码执行，
# 因此默认不应暴露到局域网。需要局域网访问时显式设置 DATAFLOW_HOST=0.0.0.0。
# （之前这里硬编码 0.0.0.0，导致文档里的 DATAFLOW_HOST 说明是无效承诺。）
cat > "$OUT_STAGING/$PKG_NAME/run.sh" <<'EOF'
#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

# 本服务无认证，且执行 pipeline 等同于任意代码执行。
# 默认只监听本机；如需局域网访问：DATAFLOW_HOST=0.0.0.0 ./run.sh
HOST="${DATAFLOW_HOST:-127.0.0.1}"
PORT="${DATAFLOW_PORT:-8000}"

if [[ "$HOST" != "127.0.0.1" && "$HOST" != "localhost" ]]; then
  echo "[run] WARNING: binding $HOST — no authentication is enforced." >&2
  echo "[run]          anyone who can reach this port can run pipelines." >&2
fi

echo "[run] http://localhost:$PORT/"
cd backend
exec uvicorn app.main:app --port "$PORT" --host "$HOST"
EOF
chmod +x "$OUT_STAGING/$PKG_NAME/run.sh"

cat > "$OUT_STAGING/$PKG_NAME/run.bat" <<'EOF'
@echo off
setlocal
cd /d "%~dp0"

REM 本服务无认证，且执行 pipeline 等同于任意代码执行。
REM 默认只监听本机；如需局域网访问：set DATAFLOW_HOST=0.0.0.0
if "%DATAFLOW_HOST%"=="" set DATAFLOW_HOST=127.0.0.1
if "%DATAFLOW_PORT%"=="" set DATAFLOW_PORT=8000

if not "%DATAFLOW_HOST%"=="127.0.0.1" (
  echo [run] WARNING: binding %DATAFLOW_HOST% - no authentication is enforced.
  echo [run]          anyone who can reach this port can run pipelines.
)

echo [run] http://localhost:%DATAFLOW_PORT%/
cd backend
uvicorn app.main:app --port %DATAFLOW_PORT% --host %DATAFLOW_HOST%
EOF

# ---- 4) 打 zip ----
echo "[build_release] Creating zip..."
pushd "$OUT_STAGING" >/dev/null
zip -qr "$ROOT_DIR/$ZIP_NAME" "$PKG_NAME"
popd >/dev/null

# ---- 5) 校验产物 ----
# 发布包是用户拿到的唯一东西，缺文件只有解压后才会发现，所以在这里就查。
echo "[build_release] Verifying archive..."

zip -T "$ROOT_DIR/$ZIP_NAME" >/dev/null || {
  echo "[build_release] ERROR: archive failed its integrity test."
  exit 1
}

REQUIRED=(
  "$PKG_NAME/run.sh"
  "$PKG_NAME/run.bat"
  "$PKG_NAME/docs/RELEASE-PACKAGE.md"
  "$PKG_NAME/backend/app/main.py"
  "$PKG_NAME/frontend/dist/index.html"
)
LISTING="$(unzip -Z1 "$ROOT_DIR/$ZIP_NAME")"
MISSING=0
for entry in "${REQUIRED[@]}"; do
  if ! printf '%s\n' "$LISTING" | grep -qxF "$entry"; then
    echo "[build_release] ERROR: missing from archive: $entry"
    MISSING=$((MISSING + 1))
  fi
done
[[ "$MISSING" -eq 0 ]] || exit 1

# The release must not bind 0.0.0.0 by default — no auth, and running a pipeline
# is arbitrary code execution.
if grep -q 'host=0\.0\.0\.0\|--host 0\.0\.0\.0' "$OUT_STAGING/$PKG_NAME/run.sh"; then
  echo "[build_release] ERROR: run.sh hardcodes 0.0.0.0; it must default to 127.0.0.1."
  exit 1
fi

echo "[build_release] Done: $ROOT_DIR/$ZIP_NAME"
