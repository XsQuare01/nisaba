"""용어 사전(쓸 말 / 피할 말)과 본문을 대조한다.

사용: python check_terms.py --doc page.md --terms coord-series-terms.json
exit 0 = 지적 없음, 1 = 지적 있음, 2 = 입력 오류
용어 사전 형식: {"terms":[{"use":str,"avoid":[str],"note":str?}]}
"""
import argparse
import json
import re
import sys


def load_terms(path):
    try:
        with open(path, encoding="utf-8-sig") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"용어 사전을 읽지 못함: {exc}") from exc
    terms = data.get("terms") if isinstance(data, dict) else None
    if not isinstance(terms, list):
        raise ValueError("최상위에 terms 목록이 있어야 함")
    for t in terms:
        if not isinstance(t.get("use"), str) or not t["use"]:
            raise ValueError(f"use가 없음: {t}")
        if not isinstance(t.get("avoid"), list) or not all(isinstance(a, str) and a for a in t["avoid"]):
            raise ValueError(f"avoid는 비어 있지 않은 문자열 목록이어야 함: {t}")
    return terms


def _spans(text, word):
    out, start = [], 0
    while True:
        i = text.find(word, start)
        if i < 0:
            return out
        out.append((i, i + len(word)))
        start = i + 1


INLINE_CODE_RE = re.compile(r"`[^`]*`")


def find_avoided(doc_text, terms):
    """(줄 번호, 피할 말, 쓸 말, 문맥). 펜스 코드, 인라인 코드, 쓸 말 구간 안의 일치는 뺀다."""
    hits = []
    in_fence = False
    uses = [t["use"] for t in terms]
    for no, line in enumerate(doc_text.splitlines(), 1):
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        protected = [s for u in uses for s in _spans(line, u)]
        protected += [m.span() for m in INLINE_CODE_RE.finditer(line)]
        for t in terms:
            for avoid in t["avoid"]:
                for a, b in _spans(line, avoid):
                    if any(s <= a and b <= e for s, e in protected):
                        continue
                    hits.append((no, avoid, t["use"], line[max(0, a - 15):b + 15].strip()))
    return hits


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--doc", required=True)
    ap.add_argument("--terms", required=True)
    args = ap.parse_args(argv)
    try:
        with open(args.doc, encoding="utf-8-sig") as f:
            doc = f.read()
        terms = load_terms(args.terms)
    except (OSError, ValueError) as exc:
        print(f"입력 오류: {exc}")
        return 2
    hits = find_avoided(doc, terms)
    for no, avoid, use, ctx in hits:
        print(f"L{no} '{avoid}' → '{use}' | {ctx}")
    print(f"요약: 지적 {len(hits)}")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
