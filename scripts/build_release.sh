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
command -v python >/dev/null 2>&1 || { echo "python not found"; exit 1; }
command -v zip >/dev/null 2>&1 || { echo "zip not found (ubuntu: apt-get install zip)"; exit 1; }
command -v rsync >/dev/null 2>&1 || { echo "rsync not found (ubuntu: apt-get install rsync)"; exit 1; }

# ---- 清理 staging ----
rm -rf "$OUT_STAGING"
mkdir -p "$OUT_STAGING/$PKG_NAME"

# ---- 1) 构建前端（你现在 dist 已在 frontend/ 下）----
echo "[build_release] Building frontend..."
pushd "$FRONTEND_DIR" >/dev/null
# 你仓库里是 yarn.lock；若你更想用 yarn，就把 npm ci 换成 yarn install --frozen-lockfile
# 这里先用 npm（要求有 package-lock.json）；如果你没 lock，建议改用 yarn
if [[ -f "package-lock.json" ]]; then
  npm ci
  npm run build
else
  echo "No package-lock.json found, using npm install (consider using yarn with yarn.lock)."
  npm install
  npm run build
fi
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

# 2.3 顶层文档（可选）
[[ -f "$ROOT_DIR/README-release-en.md" ]] && cp "$ROOT_DIR/README-release-en.md" "$OUT_STAGING/$PKG_NAME/"
[[ -f "$ROOT_DIR/README-release-zh.md" ]] && cp "$ROOT_DIR/README-release-zh.md" "$OUT_STAGING/$PKG_NAME/"
[[ -f "$ROOT_DIR/LICENSE" ]] && cp "$ROOT_DIR/LICENSE" "$OUT_STAGING/$PKG_NAME/" || true

# ---- 3) 一键启动脚本 ----
# 关键：从 release 根目录启动，保证 backend 里用 ../frontend/dist 能找到前端资源
cat > "$OUT_STAGING/$PKG_NAME/run.sh" <<'EOF'
#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

# 后端依赖
cd backend

uvicorn app.main:app --reload --port 8000  --reload-dir app --host=0.0.0.0
EOF
chmod +x "$OUT_STAGING/$PKG_NAME/run.sh"

cat > "$OUT_STAGING/$PKG_NAME/run.bat" <<'EOF'
@echo off
setlocal
cd /d "%~dp0"

cd backend

uvicorn app.main:app --reload --port 8000  --reload-dir app --host=0.0.0.0
EOF

# ---- 4) 打 zip ----
echo "[build_release] Creating zip..."
pushd "$OUT_STAGING" >/dev/null
zip -r "$ROOT_DIR/$ZIP_NAME" "$PKG_NAME"
popd >/dev/null

echo "[build_release] Done: $ROOT_DIR/$ZIP_NAME"
