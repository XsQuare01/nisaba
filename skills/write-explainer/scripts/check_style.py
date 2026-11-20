"""문장·구성 후보를 뽑는다: 긴 문장, 쉼표로 이은 절, 맨 식별자, 시각 자료 없는 절, 분량.

판정이 아니라 후보 목록이다. 작성자가 문맥을 보고 고칠지 정한다(references/korean-style.md, structure.md).

python check_style.py --doc page.md [--max-len 60] [--max-page 8000] [--strict]
"""
import argparse
import re
import sys

TAG_RE = re.compile(r"<[^>\n]+>")
CODE_RE = re.compile(r"`[^`\n]*`")
MATH_RE = re.compile(r"\$[^$\n]+\$")
LINK_RE = re.compile(r"\]\([^)]*\)")
SENT_RE = re.compile(r"(?<=[.?!])\s+")
# 연결 어미로 끝난 절 뒤의 쉼표: 「…어서,」 「…면,」 「…고,」 같은 꼴
CLAUSE_COMMA_RE = re.compile(r"[가-힣](?:어서|아서|해서|므로|니까|는데|지만|면서|으며|이며|며|고|면|니),\s")
# 앞뒤 경계는 ASCII로만 본다. 한글 조사(「base_dt로」)는 경계다.
IDENT_RE = re.compile(r"(?<![A-Za-z0-9_`$])[a-z][a-z0-9]*(?:_[a-z0-9]+)+(?![A-Za-z0-9_`$])")
VISUAL_RE = re.compile(r"^\s*(<image|<figure|<img|<embed|<iframe|<svg)", re.I)  # 표는 시각 자료로 치지 않는다
H2_RE = re.compile(r"^##\s+(?!#)(.*)")


def _prose(doc):
    """(줄 번호, 원래 줄, 검사할 글) — 펜스 코드와 $$ 블록은 건너뛴다."""
    out, fence, math = [], False, False
    for no, line in enumerate(doc.splitlines(), 1):
        s = line.strip()
        if s.startswith("```") or s.startswith("~~~"):
            fence = not fence
            continue
        if s == "$$":
            math = not math
            continue
        if fence or math:
            continue
        text = LINK_RE.sub("]", MATH_RE.sub("", CODE_RE.sub("", TAG_RE.sub("", line))))
        out.append((no, line, text))
    return out


def check(doc, max_len=60, max_page=8000):
    """[(종류, 줄 번호, 문장 또는 절 이름)]"""
    res = []
    total = 0
    for no, line, text in _prose(doc):
        s = text.strip()
        if not s or s.startswith("|") or H2_RE.match(s) or s.startswith("#"):
            continue
        body = re.sub(r"^([-*]|\d+\.)\s+", "", s)
        total += len(body)
        for sent in SENT_RE.split(body):
            sent = sent.strip()
            if not sent:
                continue
            if len(sent) > max_len:
                res.append(("긴 문장", no, sent))
            if CLAUSE_COMMA_RE.search(sent):
                res.append(("쉼표 이음", no, sent))
        for m in IDENT_RE.finditer(text):
            res.append(("맨 식별자", no, m.group()))
    # 절마다 시각 자료
    section, start, has_visual = None, 0, False
    lines = doc.splitlines()
    for no, line in enumerate(lines + ["## <끝>"], 1):
        m = H2_RE.match(line.strip())
        if m:
            if section is not None and not has_visual:
                res.append(("시각 자료 없는 절", start, section))
            section, start, has_visual = m.group(1).strip(), no, False
        elif VISUAL_RE.match(line):
            has_visual = True
    if total > max_page:
        res.append(("분량", 0, f"{total}자 > {max_page}자 — 페이지 나누기 검토"))
    return res


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--doc", required=True)
    ap.add_argument("--max-len", type=int, default=60)
    ap.add_argument("--max-page", type=int, default=8000)
    ap.add_argument("--strict", action="store_true", help="후보가 하나라도 있으면 종료 코드 1")
    a = ap.parse_args(argv)
    with open(a.doc, encoding="utf-8-sig") as f:
        doc = f.read()
    res = check(doc, a.max_len, a.max_page)
    for kind, no, what in res:
        print(f"{kind} L{no} | {what}")
    count = lambda k: sum(1 for r in res if r[0] == k)
    print(f"요약: 긴 문장 {count('긴 문장')} · 쉼표 이음 {count('쉼표 이음')} · 맨 식별자 {count('맨 식별자')}"
          f" · 시각 자료 없는 절 {count('시각 자료 없는 절')} · 분량 초과 {count('분량')}")
    return 1 if (a.strict and res) else 0


if __name__ == "__main__":
    sys.exit(main())
