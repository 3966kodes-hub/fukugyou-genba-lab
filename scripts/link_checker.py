"""
MDX / MD ファイル内の外部リンク・内部リンクを抽出し、HTTP ステータスを検証する。

使い方:
    python scripts/link_checker.py <file_or_dir>
    python scripts/link_checker.py src/content/posts/elevenlabs-side-job.mdx
    python scripts/link_checker.py src/content/posts/

仕様:
  - Markdown リンク [text](url) と素 URL を抽出
  - 外部 URL は HTTP HEAD（フォールバックで GET）でステータス確認
  - 内部リンク（/posts/<slug>/ など）は src/content/posts/<slug>.mdx の存在で検証
  - サマリ：合計 / OK / NG / SKIP（mailto: 等）を表示
  - 失敗が 1 件でもあれば終了コード 1（自動投稿ジョブで判定可能）

注意:
  - WordPress 等の bot 弾きで 403 になる正規 URL は WARN 扱い（exit 1 にしない）
  - タイムアウトは 10 秒
"""

import os
import re
import sys
import urllib.request
import urllib.error
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

REPO_ROOT = Path(__file__).resolve().parent.parent
POSTS_DIR = REPO_ROOT / "src" / "content" / "posts"

# Markdown リンク [text](url) と裸 URL を拾う
MD_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^\s)]+|/[^)\s]+)\)")
BARE_URL_RE = re.compile(r"(?<![\(\[])\bhttps?://[^\s<>\"'`)]+")

USER_AGENT = (
    "Mozilla/5.0 (compatible; FukugyouGenbaLab-LinkChecker/1.0; "
    "+https://fukugyou-genba-lab.com)"
)
TIMEOUT = 10


def collect_files(target: Path):
    if target.is_file():
        return [target]
    if target.is_dir():
        return sorted(target.rglob("*.mdx")) + sorted(target.rglob("*.md"))
    return []


def extract_links(text: str):
    """ファイル内容から (kind, url) のタプル一覧を返す。kind は 'ext' / 'internal'。"""
    found = set()
    for m in MD_LINK_RE.finditer(text):
        url = m.group(2)
        if url.startswith("http"):
            found.add(("ext", url))
        elif url.startswith("/"):
            found.add(("internal", url))
    for m in BARE_URL_RE.finditer(text):
        found.add(("ext", m.group(0).rstrip(".,;:")))
    return sorted(found)


def check_external(url: str):
    """外部 URL を HEAD で叩く。失敗時は GET にフォールバック。"""
    req = urllib.request.Request(
        url, method="HEAD", headers={"User-Agent": USER_AGENT}
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as res:
            return res.status, "HEAD"
    except urllib.error.HTTPError as e:
        if e.code in (403, 405, 501):
            # bot 弾き / HEAD 非対応 → GET でリトライ
            try:
                req2 = urllib.request.Request(
                    url, method="GET", headers={"User-Agent": USER_AGENT}
                )
                with urllib.request.urlopen(req2, timeout=TIMEOUT) as res2:
                    return res2.status, "GET"
            except Exception as e2:
                return f"ERR:{type(e2).__name__}", "GET"
        return e.code, "HEAD"
    except Exception as e:
        return f"ERR:{type(e).__name__}", "HEAD"


def check_internal(path: str):
    """/posts/<slug>/ → src/content/posts/<slug>.mdx の存在検証。"""
    if path.startswith("/posts/"):
        slug = path.rstrip("/").split("/")[-1]
        for ext in ("mdx", "md"):
            if (POSTS_DIR / f"{slug}.{ext}").exists():
                return "OK"
        return "MISSING"
    # /category /tags /hub などはルーティングに任せて SKIP（静的検証不可）
    return "SKIP"


def check_file(file: Path):
    text = file.read_text(encoding="utf-8")
    links = extract_links(text)
    rows = []

    ext_links = [u for k, u in links if k == "ext"]
    int_links = [u for k, u in links if k == "internal"]

    # 外部は並列
    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = {ex.submit(check_external, u): u for u in ext_links}
        for fut in as_completed(futures):
            url = futures[fut]
            status, method = fut.result()
            rows.append(("ext", url, status, method))

    for u in int_links:
        rows.append(("internal", u, check_internal(u), "-"))

    return rows


def is_ok(status):
    if isinstance(status, int):
        return 200 <= status < 400
    return status == "OK"


def is_warn(status):
    return isinstance(status, int) and status == 403


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/link_checker.py <file_or_dir>")
        sys.exit(2)

    target = Path(sys.argv[1]).resolve()
    if not target.exists():
        print(f"[ERROR] not found: {target}")
        sys.exit(2)

    files = collect_files(target)
    if not files:
        print(f"[ERROR] no md/mdx files in: {target}")
        sys.exit(2)

    total = ok = ng = warn = skip = 0
    failures = []

    for f in files:
        rel = f.relative_to(REPO_ROOT)
        rows = check_file(f)
        if not rows:
            continue
        print(f"\n=== {rel} ===")
        for kind, url, status, method in rows:
            total += 1
            label = f"[{kind:8}]"
            if is_ok(status):
                ok += 1
                print(f"  OK   {label} {status} {method:4} {url}")
            elif is_warn(status):
                warn += 1
                print(f"  WARN {label} {status} {method:4} {url} (bot ブロックの可能性)")
            elif status == "SKIP":
                skip += 1
                print(f"  SKIP {label} {url}")
            else:
                ng += 1
                failures.append((rel, url, status))
                print(f"  NG   {label} {status} {method:4} {url}")

    print("\n" + "=" * 60)
    print(f"Total : {total} | OK : {ok} | NG : {ng} | WARN : {warn} | SKIP : {skip}")
    if failures:
        print("\nFailures:")
        for f, u, s in failures:
            print(f"  {f} → {u} ({s})")
        sys.exit(1)

    print("All links OK.")
    sys.exit(0)


if __name__ == "__main__":
    main()
