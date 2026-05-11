# 副業現場ラボ — manual deploy script
#
# 用途:
#   通常運用は GitHub `main` への push で Cloudflare Pages が自動デプロイするが、
#   本スクリプトは「ローカルビルド成果物（dist/）を Wrangler 経由で直接 push 配信」
#   したい場合の手動デプロイ手段を提供する。
#
# 前提:
#   - `wrangler` が devDependencies に入っている（package.json）
#   - Cloudflare アカウントに `wrangler login` 済み、または CLOUDFLARE_API_TOKEN がセット済み
#   - Pages プロジェクト名は既定で `fukugyou-genba-lab`（環境変数で上書き可）
#
# 使い方:
#   pwsh deploy.ps1                 # 通常デプロイ
#   pwsh deploy.ps1 -SkipBuild      # 既存 dist/ をそのまま push
#   pwsh deploy.ps1 -Project name   # 別プロジェクトに push
#
# 失敗時の挙動:
#   - npm run build が失敗 → exit 1
#   - wrangler pages deploy が失敗 → exit 1

param(
    [switch]$SkipBuild,
    [string]$Project = "fukugyou-genba-lab",
    [string]$Branch  = "main"
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

Set-Location $repoRoot

Write-Host "== 副業現場ラボ deploy =="
Write-Host "repo    : $repoRoot"
Write-Host "project : $Project"
Write-Host "branch  : $Branch"

if (-not $SkipBuild) {
    Write-Host "`n[1/2] npm run build ..."
    npm run build
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] build failed (exit $LASTEXITCODE)" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "`n[1/2] build skipped (-SkipBuild)"
}

if (-not (Test-Path "$repoRoot\dist")) {
    Write-Host "[ERROR] dist/ not found. Run without -SkipBuild." -ForegroundColor Red
    exit 1
}

Write-Host "`n[2/2] wrangler pages deploy ..."
npx wrangler pages deploy "$repoRoot\dist" --project-name $Project --branch $Branch
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] wrangler deploy failed (exit $LASTEXITCODE)" -ForegroundColor Red
    exit 1
}

Write-Host "`nDeploy completed: https://$Project.pages.dev" -ForegroundColor Green
