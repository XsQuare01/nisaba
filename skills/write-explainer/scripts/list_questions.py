"""본문에서 글이 스스로 던진 질문의 후보 문장을 뽑는다(질문 장부 초안용).

후보일 뿐이다. 종류(본문이 답함 / 실험·조작으로 확인 / 다음 글로 넘김 / 일부러 열어 둠)를
정하고 답과 짝을 맞추는 일은 작성자와 cold-reader가 한다.

사용: python list_questions.py --doc page.md   (항상 exit 0)
"""
import argparse
import re
import sys

SIGNAL_RE = re.compile(
    r"\?\s*$|것 같지만|것 같다|일까|까[?.]|(?:^|\s)왜(?:\s|$)|어떻게\s|무엇이|얼마나\s|될까")
SPLIT_RE = re.compile(r"(?<=[.?!])\s+")
TAG_RE = re.compile(r"<[^>]*>")
LINK_URL_RE = re.compile(r"\]\([^)]*\)")


def _prose_lines(doc_text):
    in_fence = in_math = False
    for no, line in enumerate(doc_text.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if stripped == "$$" or (stripped.startswith("$$") and not stripped.endswith("$$")):
            in_math = not in_math
            continue
        if in_math or (stripped.startswith("$$") and stripped.endswith("$$") and len(stripped) > 2):
            continue
        yield no, LINK_URL_RE.sub("]", TAG_RE.sub("", line)).strip()


def list_questions(doc_text):
    """(줄 번호, 문장) 목록."""
    out = []
    for no, text in _prose_lines(doc_text):
        if not text:
            continue
        for sent in SPLIT_RE.split(text):
            sent = sent.strip()
            if sent and SIGNAL_RE.search(sent):
                out.append((no, sent))
    return out


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--doc", required=True)
    args = ap.parse_args(argv)
    try:
        with open(args.doc, encoding="utf-8-sig") as f:
            doc = f.read()
    except OSError as exc:
        print(f"입력 오류: {exc}")
        return 0
    found = list_questions(doc)
    for no, sent in found:
        print(f"L{no} {sent}")
    print(f"요약: 질문 후보 {len(found)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
