"""
3 つのアフィリエイトブログ（jisaku-biz-lab / pm-genba-lab / aws-cert-lab）の dev リポジトリの
md/mdx を Obsidian 用に変換してミラーする。

仕様:
  ① 画像: dev 側を絶対パス参照 file:///E:/dev/<repo>/public/...
  ② ファイル名: glossary は frontmatter.term、posts は frontmatter.title から生成、既存上書き
  ③ MDX → MD: import 削除 / 各種 Astro コンポーネントを Obsidian 構文に変換
  ④ 内部リンク: /glossary/<slug>/ → [[<term>]], /posts/<slug>/ → [[<title>]],
                /category|tags|hub/* は文言のみ残す

使い方:
  python affiliate_mirror.py jisaku       # jisaku のみ
  python affiliate_mirror.py pm           # pm のみ
  python affiliate_mirror.py aws          # aws のみ
  python affiliate_mirror.py all          # 3 ブログ全部
  python affiliate_mirror.py <blog> sample # 1 件ずつサンプル変換
"""

import os
import re
import sys
import yaml
from pathlib import Path

# Windows コンソール（cp932）でも UTF-8 で出力できるようにする
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

# === ブログ設定 ===
OBSIDIAN_BASE = Path(r"E:/5つの力+生きる/1. 稼ぐ/07. 副業・複業/06. アフィリエイトブログ")

BLOGS = {
    "jisaku": {
        "label": "自作PC",
        "dev_repo": Path(r"E:/dev/jisaku-biz-lab"),
        "dev_glossary": Path(r"E:/dev/jisaku-biz-lab/src/content/glossary"),
        "dev_posts": Path(r"E:/dev/jisaku-biz-lab/src/content/posts"),
        "dev_images_public": "E:/dev/jisaku-biz-lab/public",
        "obsidian_glossary": OBSIDIAN_BASE / "02_自作PC" / "11_用語集",
        "obsidian_posts": OBSIDIAN_BASE / "02_自作PC" / "03_記事ドラフト" / "03_公開済み",
        "sample_glossary": "noctua.md",
        "sample_post": "jisaku-pc-roadmap-7steps.mdx",
    },
    "pm": {
        "label": "PM",
        "dev_repo": Path(r"E:/dev/pm-genba-lab"),
        "dev_glossary": None,  # PM には glossary なし
        "dev_posts": Path(r"E:/dev/pm-genba-lab/src/content/posts"),
        "dev_images_public": "E:/dev/pm-genba-lab/public",
        "obsidian_glossary": None,
        "obsidian_posts": OBSIDIAN_BASE / "03_PM" / "03_記事ドラフト" / "03_公開済み",
        "sample_glossary": None,
        "sample_post": "pmp-complete-guide-2026.mdx",
    },
    "aws": {
        "label": "AWS",
        "dev_repo": Path(r"E:/dev/aws-cert-lab"),
        "dev_glossary": None,  # 現状 dev に glossary collection なし
        "dev_posts": Path(r"E:/dev/aws-cert-lab/src/content/posts"),
        "dev_images_public": "E:/dev/aws-cert-lab/public",
        "obsidian_glossary": None,
        "obsidian_posts": OBSIDIAN_BASE / "04_AWS資格" / "03_記事ドラフト" / "03_公開済み",
        "sample_glossary": None,
        "sample_post": "acm.mdx",
    },
}

# === ユーティリティ ===
WIN_FORBIDDEN = str.maketrans({
    ":": "：", "\\": "￥", "/": "／", "?": "？",
    "*": "＊", "<": "＜", ">": "＞", '"': "”", "|": "｜",
})


def sanitize_filename(name: str) -> str:
    return name.translate(WIN_FORBIDDEN).strip()


def parse_frontmatter(text: str):
    if not text.startswith("---"):
        return {}, text
    m = re.match(r"^---\s*\r?\n(.*?)\r?\n---\s*\r?\n", text, flags=re.DOTALL)
    if not m:
        return {}, text
    try:
        fm = yaml.safe_load(m.group(1)) or {}
    except Exception as e:
        print(f"  [warn] frontmatter YAML parse failed: {e}", file=sys.stderr)
        fm = {}
    return fm, text[m.end():]


def parse_jsx_attrs(attr_str: str) -> dict:
    return dict(re.findall(r'(\w+)="([^"]*)"', attr_str))


def extract_balanced_array(text: str, after_keyword: str):
    """`<keyword>=\\{ [ ... ] \\}` の配列内側を、括弧バランスを取りつつ抽出。"""
    pattern = after_keyword + r"\s*=\s*\{\s*\["
    m = re.search(pattern, text)
    if not m:
        return None
    start = m.end()
    depth = 1
    i = start
    while i < len(text):
        ch = text[i]
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                return text[start:i]
        elif ch == '"':
            i += 1
            while i < len(text):
                if text[i] == "\\":
                    i += 2
                    continue
                if text[i] == '"':
                    break
                i += 1
        i += 1
    return None


def split_jsx_objects(text: str):
    """`{...}, {...}, ...` を中括弧バランスで個別オブジェクトに分割（中身のみ返す）。"""
    objs, depth, cur = [], 0, ""
    in_str = False
    esc = False
    for ch in text:
        if esc:
            cur += ch
            esc = False
            continue
        if in_str:
            cur += ch
            if ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
            cur += ch
            continue
        if ch == "{":
            depth += 1
            if depth == 1:
                cur = ""
                continue
        elif ch == "}":
            depth -= 1
            if depth == 0:
                objs.append(cur)
                cur = ""
                continue
        if depth >= 1:
            cur += ch
    return objs


def extract_string_field(obj_text: str, key: str):
    m = re.search(rf'{key}\s*:\s*"((?:[^"\\]|\\.)*)"', obj_text)
    return m.group(1) if m else None


def extract_number_field(obj_text: str, key: str):
    m = re.search(rf"{key}\s*:\s*(\d+(?:\.\d+)?)", obj_text)
    return m.group(1) if m else None


def extract_string_array_field(obj_text: str, key: str):
    m = re.search(rf"{key}\s*:\s*\[([^\]]*)\]", obj_text)
    if not m:
        return []
    return re.findall(r'"((?:[^"\\]|\\.)*)"', m.group(1))


# === 状態（現在処理中のブログ） ===
_current_blog = None
_glossary_slug_to_term = {}
_post_slug_to_title = {}


def set_active_blog(name):
    global _current_blog
    _current_blog = BLOGS[name]


def build_maps():
    global _glossary_slug_to_term, _post_slug_to_title
    _glossary_slug_to_term = {}
    _post_slug_to_title = {}
    cfg = _current_blog
    if cfg["dev_glossary"]:
        for f in cfg["dev_glossary"].glob("*.md"):
            text = f.read_text(encoding="utf-8")
            fm, _ = parse_frontmatter(text)
            _glossary_slug_to_term[f.stem] = fm.get("term") or f.stem
    for f in cfg["dev_posts"].glob("*.mdx"):
        text = f.read_text(encoding="utf-8")
        fm, _ = parse_frontmatter(text)
        _post_slug_to_title[f.stem] = fm.get("title") or f.stem


# === 内部リンク → wikilink ===
def convert_internal_links(text: str) -> str:
    def repl_g(m):
        display = m.group(1)
        slug = m.group(2)
        term = _glossary_slug_to_term.get(slug)
        if not term:
            return m.group(0)
        term_safe = sanitize_filename(term)
        return f"[[{term_safe}]]" if display.strip() == term.strip() else f"[[{term_safe}|{display}]]"
    text = re.sub(r"\[([^\]]+)\]\(/glossary/([^/)]+)/?\)", repl_g, text)

    def repl_p(m):
        display = m.group(1)
        slug = m.group(2)
        title = _post_slug_to_title.get(slug)
        if not title:
            return m.group(0)
        title_safe = sanitize_filename(title)
        return f"[[{title_safe}]]" if display.strip() == title.strip() else f"[[{title_safe}|{display}]]"
    text = re.sub(r"\[([^\]]+)\]\(/posts/([^/)]+)/?\)", repl_p, text)

    text = re.sub(r"\[([^\]]+)\]\(/(?:category|tags|hub)/[^)]*\)", r"\1", text)
    text = re.sub(
        r"\[([^\]]+)\]\(/(?!images/|glossary/|posts/|category/|tags/|hub/)[^)]*\)",
        r"\1",
        text,
    )
    return text


# === MDX → MD 変換 ===
def convert_mdx(text: str) -> str:
    # import 行
    text = re.sub(r"^import\s+.*$\n?", "", text, flags=re.MULTILINE)

    # <PRBadge />
    text = re.sub(r"<PRBadge\s*/>", "> [!info] PR\n> 本記事はアフィリエイトリンクを含みます。", text)

    # === Callout (block-form) ===
    def repl_callout(m):
        attrs = parse_jsx_attrs(m.group(1) or "")
        ctype = attrs.get("type", "note")
        title = attrs.get("title", "")
        body = m.group(2)
        body = re.sub(r"<br\s*/?>", "\n", body)
        lines = [ln.rstrip() for ln in body.split("\n")]
        non_empty = [ln for ln in lines if ln.strip()]
        if non_empty:
            common = min(len(ln) - len(ln.lstrip(" ")) for ln in non_empty)
            if common > 0:
                lines = [ln[common:] if len(ln) >= common else ln for ln in lines]
        while lines and not lines[0].strip():
            lines.pop(0)
        while lines and not lines[-1].strip():
            lines.pop()
        quoted = "\n".join(f"> {ln}" if ln.strip() else ">" for ln in lines)
        head = f"> [!{ctype}] {title}".rstrip()
        return f"\n{head}\n{quoted}\n"
    text = re.sub(r"<Callout([^>]*)>([\s\S]*?)</Callout>", repl_callout, text)

    # === TipsBox (block-form, 属性なし) ===
    def repl_tipsbox(m):
        body = m.group(1).strip()
        # 内部の "---" 区切りは削除（Obsidian callout 内で水平線として機能しないため）
        body = re.sub(r"^---+\s*$", "", body, flags=re.MULTILINE)
        lines = [ln.rstrip() for ln in body.split("\n")]
        while lines and not lines[0].strip():
            lines.pop(0)
        while lines and not lines[-1].strip():
            lines.pop()
        quoted = "\n".join(f"> {ln}" if ln.strip() else ">" for ln in lines)
        return f"\n> [!tip] Tips\n{quoted}\n"
    text = re.sub(r"<TipsBox\s*>([\s\S]*?)</TipsBox>", repl_tipsbox, text)

    # === ComparisonTable ===
    def repl_comparison(m):
        whole = m.group(0)
        title_m = re.search(r'title="([^"]*)"', whole)
        options_inner = extract_balanced_array(whole, "options")
        rows_inner = extract_balanced_array(whole, "rows")
        caption_m = re.search(r'caption="([^"]*)"', whole)
        if options_inner is None or rows_inner is None:
            return whole
        options = re.findall(r'"((?:[^"\\]|\\.)*)"', options_inner)
        rows = []
        for rm in re.finditer(
            r'\{\s*label:\s*"((?:[^"\\]|\\.)*)"\s*,\s*values:\s*\[([^\]]*)\]\s*\}',
            rows_inner,
        ):
            values = re.findall(r'"((?:[^"\\]|\\.)*)"', rm.group(2))
            rows.append((rm.group(1), values))
        out = []
        if title_m:
            out.append(f"\n**{title_m.group(1)}**\n")
        out.append("| 項目 | " + " | ".join(options) + " |")
        out.append("|" + "---|" * (len(options) + 1))
        for label, values in rows:
            cells = [label] + values + [""] * (len(options) - len(values))
            cells = [c.replace("|", "\\|") for c in cells]
            out.append("| " + " | ".join(cells) + " |")
        if caption_m:
            out.append(f"\n*{caption_m.group(1)}*")
        out.append("")
        return "\n".join(out)
    text = re.sub(r"<ComparisonTable[\s\S]*?/>", repl_comparison, text)

    # === BuildTable ===
    def repl_build(m):
        whole = m.group(0)
        title_m = re.search(r'title="([^"]*)"', whole)
        parts_text = extract_balanced_array(whole, "parts")
        if parts_text is None:
            return whole
        objs = split_jsx_objects(parts_text)
        parts = []
        for o in objs:
            parts.append({
                "type": extract_string_field(o, "type") or "",
                "name": extract_string_field(o, "name") or "",
                "price": int(extract_number_field(o, "price") or 0),
                "url": extract_string_field(o, "url") or "",
                "note": extract_string_field(o, "note") or "",
            })
        out = []
        if title_m:
            out.append(f"\n**{title_m.group(1)}**\n")
        out.append("| 種別 | パーツ | 価格 | 備考 |")
        out.append("|---|---|---:|---|")
        total = 0
        for p in parts:
            name_link = f"[{p['name']}]({p['url']})" if p["url"] else p["name"]
            price_str = f"{p['price']:,} 円" if p["price"] else "—"
            cells = [p["type"], name_link, price_str, p["note"]]
            cells = [c.replace("|", "\\|") for c in cells]
            out.append("| " + " | ".join(cells) + " |")
            total += p["price"]
        if total:
            out.append(f"| **合計** |  | **{total:,} 円** |  |")
        out.append("")
        return "\n".join(out)
    text = re.sub(r"<BuildTable[\s\S]*?/>", repl_build, text)

    # === PartsCard ===
    def repl_partscard(m):
        whole = m.group(0)
        t = re.search(r'type="((?:[^"\\]|\\.)*)"', whole)
        n = re.search(r'name="((?:[^"\\]|\\.)*)"', whole)
        img = re.search(r'image="((?:[^"\\]|\\.)*)"', whole)
        asin = re.search(r'asin="((?:[^"\\]|\\.)*)"', whole)
        pros_inner = extract_balanced_array(whole, "pros")
        out = ["\n---"]
        if t:
            out.append(f"**{t.group(1)}**")
        if n:
            out.append(f"📦 {n.group(1)}")
        if img:
            ipath = img.group(1)
            full = (_current_blog["dev_images_public"] + ipath) if ipath.startswith("/") else ipath
            out.append(f"\n![{n.group(1) if n else ''}](file:///{full})\n")
        if asin:
            out.append(f"🛒 Amazon: https://www.amazon.co.jp/dp/{asin.group(1)}")
        if pros_inner is not None:
            items = re.findall(r'"((?:[^"\\]|\\.)*)"', pros_inner)
            if items:
                out.append("**特徴:**")
                for item in items:
                    out.append(f"- {item}")
        out.append("---\n")
        return "\n".join(out)
    text = re.sub(r"<PartsCard[\s\S]*?/>", repl_partscard, text)

    # === ProsCons ===
    def repl_proscons(m):
        whole = m.group(0)
        title_m = re.search(r'title="([^"]*)"', whole)
        pros_inner = extract_balanced_array(whole, "pros")
        cons_inner = extract_balanced_array(whole, "cons")
        if pros_inner is None or cons_inner is None:
            return whole

        def items(s):
            return [
                x.replace('\\"', '"').replace("\\\\", "\\")
                for x in re.findall(r'"((?:[^"\\]|\\.)*)"', s)
            ]
        pros = items(pros_inner)
        cons = items(cons_inner)
        out = []
        if title_m:
            out.append(f"\n**{title_m.group(1)}**\n")
        out.append("| ✅ メリット | ❌ デメリット |")
        out.append("|---|---|")
        for i in range(max(len(pros), len(cons))):
            p = pros[i] if i < len(pros) else ""
            c = cons[i] if i < len(cons) else ""
            out.append(f"| {p} | {c} |")
        out.append("")
        return "\n".join(out)
    text = re.sub(r"<ProsCons[\s\S]*?/>", repl_proscons, text)

    # === StudyPlanTimeline (PM) ===
    def repl_timeline(m):
        whole = m.group(0)
        title_m = re.search(r'title="([^"]*)"', whole)
        weeks_m = re.search(r"totalWeeks=\{(\d+)\}", whole)
        phases_text = extract_balanced_array(whole, "phases")
        if phases_text is None:
            return whole
        phases = []
        for o in split_jsx_objects(phases_text):
            phases.append({
                "name": extract_string_field(o, "name") or "",
                "startWeek": extract_number_field(o, "startWeek") or "",
                "endWeek": extract_number_field(o, "endWeek") or "",
                "topics": extract_string_array_field(o, "topics"),
            })
        out = []
        if title_m:
            out.append(f"\n**{title_m.group(1)}**" + (f"（全 {weeks_m.group(1)} 週）" if weeks_m else "") + "\n")
        out.append("| Phase | 期間（週） | 学習トピック |")
        out.append("|---|---|---|")
        for p in phases:
            period = f"{p['startWeek']}〜{p['endWeek']}" if p["startWeek"] else ""
            topics = " / ".join(p["topics"]).replace("|", "\\|")
            out.append(f"| {p['name']} | {period} | {topics} |")
        out.append("")
        return "\n".join(out)
    text = re.sub(r"<StudyPlanTimeline[\s\S]*?/>", repl_timeline, text)

    # === SchoolComparisonTable (PM) ===
    def repl_school(m):
        whole = m.group(0)
        exam_m = re.search(r'exam="([^"]*)"', whole)
        schools_text = extract_balanced_array(whole, "schools")
        if schools_text is None:
            return whole
        schools = []
        for o in split_jsx_objects(schools_text):
            schools.append({
                "name": extract_string_field(o, "name") or "",
                "price": int(extract_number_field(o, "price") or 0),
                "support": extract_string_field(o, "support") or "",
                "duration": extract_string_field(o, "duration") or "",
                "rating": extract_number_field(o, "rating") or "",
                "note": extract_string_field(o, "note") or "",
            })
        out = []
        head = "スクール比較"
        if exam_m:
            head = f"{exam_m.group(1)} 対策スクール比較"
        out.append(f"\n**{head}**\n")
        out.append("| スクール | 価格 | サポート | 期間 | 評価 | 備考 |")
        out.append("|---|---:|---|---|---:|---|")
        for s in schools:
            price_str = f"{s['price']:,}円" if s["price"] else "—"
            cells = [s["name"], price_str, s["support"], s["duration"], str(s["rating"]), s["note"]]
            cells = [c.replace("|", "\\|") for c in cells]
            out.append("| " + " | ".join(cells) + " |")
        out.append("")
        return "\n".join(out)
    text = re.sub(r"<SchoolComparisonTable[\s\S]*?/>", repl_school, text)

    # === ExamRoadmap (PM) ===
    def repl_roadmap(m):
        whole = m.group(0)
        title_m = re.search(r'title="([^"]*)"', whole)
        steps_text = extract_balanced_array(whole, "steps")
        if steps_text is None:
            return whole
        steps = []
        for o in split_jsx_objects(steps_text):
            steps.append({
                "num": extract_number_field(o, "num") or "",
                "label": extract_string_field(o, "label") or "",
                "description": extract_string_field(o, "description") or "",
            })
        out = []
        if title_m:
            out.append(f"\n**{title_m.group(1)}**\n")
        for s in steps:
            out.append(f"{s['num']}. **{s['label']}** — {s['description']}")
        out.append("")
        return "\n".join(out)
    text = re.sub(r"<ExamRoadmap[\s\S]*?/>", repl_roadmap, text)

    # === PMBOKPrincipleCard (PM) ===
    def repl_pmbok(m):
        whole = m.group(0)
        num_m = re.search(r"number=\{(\d+)\}", whole)
        en_m = re.search(r'nameEn="([^"]*)"', whole)
        ja_m = re.search(r'nameJa="([^"]*)"', whole)
        desc_m = re.search(r'description="((?:[^"\\]|\\.)*)"', whole)
        out = []
        head_parts = []
        if num_m:
            head_parts.append(num_m.group(1) + ".")
        if en_m:
            head_parts.append(en_m.group(1))
        if ja_m:
            head_parts.append(f"— {ja_m.group(1)}")
        out.append(f"\n**{' '.join(head_parts)}**" if head_parts else "")
        if desc_m:
            out.append(f"\n{desc_m.group(1)}\n")
        return "\n".join(out)
    text = re.sub(r"<PMBOKPrincipleCard[\s\S]*?/>", repl_pmbok, text)

    # === HTML wrapper の不要な div は削除（Tailwind 系クラスの装飾用） ===
    text = re.sub(r"<div\s+class=\"[^\"]*\"\s*>", "", text)
    text = re.sub(r"</div>", "", text)

    # 残った未処理 JSX を警告
    leftovers = sorted(set(re.findall(r"<([A-Z]\w+)[^>]*/?>", text)))
    if leftovers:
        print(f"  [warn] unhandled JSX components remain: {leftovers}", file=sys.stderr)

    return text


# === Frontmatter 整形 ===
def fm_to_yaml(fm: dict) -> str:
    if not fm:
        return ""
    return yaml.safe_dump(
        fm, allow_unicode=True, sort_keys=False, default_flow_style=False, width=10000
    )


def to_image_md(image_field, alt: str) -> str:
    if not image_field:
        return ""
    if image_field.startswith("/"):
        abs_path = _current_blog["dev_images_public"] + image_field
    else:
        abs_path = image_field
    return f"![{alt}](file:///{abs_path})\n\n"


# === ファイル変換 ===
def convert_glossary_file(src: Path) -> Path:
    text = src.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)
    term = fm.get("term") or src.stem
    alt = fm.get("imageAlt") or term
    image_md = to_image_md(fm.get("image"), alt)
    credit_md = ""
    if fm.get("imageCredit") or fm.get("imageSourceLabel"):
        parts = []
        if fm.get("imageCredit"):
            parts.append(str(fm["imageCredit"]))
        if fm.get("imageSourceLabel") and fm.get("imageSourceUrl"):
            parts.append(f"[{fm['imageSourceLabel']}]({fm['imageSourceUrl']})")
        elif fm.get("imageSourceLabel"):
            parts.append(str(fm["imageSourceLabel"]))
        if parts:
            credit_md = f"<small>{' / '.join(parts)}</small>\n\n"
    body = convert_internal_links(body)
    out = f"---\n{fm_to_yaml(fm)}---\n\n# {term}\n\n{image_md}{credit_md}{body.lstrip()}"
    fname = sanitize_filename(term) + ".md"
    out_path = _current_blog["obsidian_glossary"] / fname
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(out, encoding="utf-8")
    return out_path


def convert_post_file(src: Path) -> Path:
    text = src.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)
    title = fm.get("title") or src.stem
    alt = fm.get("heroImageAlt") or title
    image_md = to_image_md(fm.get("heroImage"), alt)
    body = convert_mdx(body)
    body = convert_internal_links(body)
    out = f"---\n{fm_to_yaml(fm)}---\n\n# {title}\n\n{image_md}{body.lstrip()}"
    fname = sanitize_filename(title) + ".md"
    out_path = _current_blog["obsidian_posts"] / fname
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(out, encoding="utf-8")
    return out_path


# === ブログ単位の実行 ===
def run_blog(name: str, sample: bool = False):
    set_active_blog(name)
    cfg = _current_blog
    print(f"\n=== {name} ({cfg['label']}) ===")
    build_maps()
    if cfg["dev_glossary"]:
        print(f"  glossary: {len(_glossary_slug_to_term)} 件")
    print(f"  posts:    {len(_post_slug_to_title)} 件")

    if sample:
        if cfg["sample_glossary"] and cfg["dev_glossary"]:
            p = convert_glossary_file(cfg["dev_glossary"] / cfg["sample_glossary"])
            print(f"  sample glossary → {p}")
        if cfg["sample_post"]:
            p = convert_post_file(cfg["dev_posts"] / cfg["sample_post"])
            print(f"  sample post     → {p}")
        return

    if cfg["dev_glossary"]:
        files = sorted(cfg["dev_glossary"].glob("*.md"))
        ok = 0
        for f in files:
            try:
                convert_glossary_file(f)
                ok += 1
            except Exception as e:
                print(f"  [error] glossary/{f.name}: {e}", file=sys.stderr)
        print(f"  glossary 完了: {ok}/{len(files)} 件")

    files = sorted(cfg["dev_posts"].glob("*.mdx"))
    ok = 0
    for f in files:
        try:
            convert_post_file(f)
            ok += 1
        except Exception as e:
            print(f"  [error] posts/{f.name}: {e}", file=sys.stderr)
    print(f"  posts    完了: {ok}/{len(files)} 件")


def main():
    args = sys.argv[1:]
    if not args:
        print("使い方: python affiliate_mirror.py <jisaku|pm|aws|all> [sample]")
        sys.exit(1)
    target = args[0]
    sample = len(args) > 1 and args[1] == "sample"
    if target == "all":
        for name in BLOGS:
            run_blog(name, sample)
    elif target in BLOGS:
        run_blog(target, sample)
    else:
        print(f"unknown target: {target} (使えるのは {list(BLOGS.keys())} か all)")
        sys.exit(1)


if __name__ == "__main__":
    main()
