"""본문 숫자를 수량 목록(numbers.json)과 대조한다.

- 계산식(expr)이나 명령(cmd)이 있는 항목은 다시 계산해 표기값과 비교한다.
- 다시 계산할 수 없는 항목은 '출처만'으로 따로 센다. 통과로 세지 않는다.
- 본문에 있는데 목록에 없는 숫자를 '미등록 숫자'로 뽑는다.

사용: python check_numbers.py --doc page.md --numbers numbers.json [--strict]
exit 0 = 실패 없음, 1 = 실패 있음(--strict면 미등록 숫자도), 2 = 입력 오류
"""
import argparse
import ast
import json
import math
import os
import re
import subprocess
import sys

KINDS = ("계산", "측정", "가정값", "코드 사실")
DEFAULT_IGNORE = [r"\d{4}-\d{2}-\d{2}", r"\d+(?:절|편)", r"^\s*\d+\.\s"]

_FUNCS = {name: getattr(math, name) for name in (
    "sqrt", "sin", "cos", "tan", "asin", "acos", "atan", "atan2", "radians",
    "degrees", "hypot", "exp", "log", "log10", "floor", "ceil")}
_FUNCS.update({"abs": abs, "min": min, "max": max, "round": round})
_CONSTS = {"pi": math.pi, "e": math.e}
_BINOPS = {ast.Add: lambda a, b: a + b, ast.Sub: lambda a, b: a - b,
           ast.Mult: lambda a, b: a * b, ast.Div: lambda a, b: a / b,
           ast.Pow: lambda a, b: a ** b, ast.Mod: lambda a, b: a % b}
_UNOPS = {ast.UAdd: lambda a: a, ast.USub: lambda a: -a}

NUMBER_RE = re.compile(r"(?<![A-Za-z_\d.])\d+(?:[.,]\d+)*")
TAG_RE = re.compile(r"<[^>]*>")
LINK_URL_RE = re.compile(r"\]\([^)]*\)")


def load_numbers(path):
    """(항목 목록, 무시 패턴 목록)을 돌려준다. 형식이 틀리면 ValueError."""
    try:
        with open(path, encoding="utf-8-sig") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"수량 목록을 읽지 못함: {exc}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("items"), list):
        raise ValueError("최상위에 items 목록이 있어야 함")
    ignore = data.get("ignore", [])
    if not isinstance(ignore, list):
        raise ValueError("ignore는 정규식 목록이어야 함")
    for pat in ignore:
        try:
            re.compile(pat)
        except re.error as exc:
            raise ValueError(f"ignore 패턴 오류 {pat!r}: {exc}") from exc
    seen = set()
    for item in data["items"]:
        _validate(item, seen)
    return data["items"], ignore


def _validate(item, seen):
    iid = item.get("id")
    if not iid or not isinstance(iid, str):
        raise ValueError(f"id가 없음: {item}")
    if iid in seen:
        raise ValueError(f"id 중복: {iid}")
    seen.add(iid)
    kind = item.get("kind")
    if kind not in KINDS:
        raise ValueError(f"{iid}: kind는 {'/'.join(KINDS)} 중 하나여야 함")
    if not item.get("shown"):
        raise ValueError(f"{iid}: shown(본문 표기)이 없음")
    has_expr, has_cmd = "expr" in item, "cmd" in item
    if has_expr and has_cmd:
        raise ValueError(f"{iid}: expr와 cmd는 함께 둘 수 없음")
    if (has_expr or has_cmd) and ("value" not in item or "tol" not in item):
        raise ValueError(f"{iid}: 다시 계산하려면 value와 tol이 있어야 함")
    if kind == "계산" and not (has_expr or has_cmd):
        raise ValueError(f"{iid}: kind 계산에는 expr나 cmd가 있어야 함")
    if kind in ("측정", "코드 사실") and not item.get("source"):
        raise ValueError(f"{iid}: kind {kind}에는 source가 있어야 함")
    if has_cmd and not (isinstance(item["cmd"], list) and item["cmd"]):
        raise ValueError(f"{iid}: cmd는 비어 있지 않은 문자열 목록이어야 함")


SIGNS = "-−"
SHOWN_NUMBER_RE = re.compile(r"(?<![\d.])([-−]?)(\d+(?:,\d{3})*(?:\.\d+)?)")


def _is_ascii_letter(ch):
    return ch.isascii() and ch.isalpha()


def shown_spans(doc_text, shown):
    """shown이 본문에 나오는 구간들. 이어지는 숫자·부호·천 단위·단위 글자 때문에
    다른 수량이 되는 일치(11 mm 속 1 mm, −0.4 mm 속 0.4 mm, 1,000,000 속 1,000, 5 mm 속 5 m)는 뺀다."""
    spans = []
    start = 0
    while True:
        i = doc_text.find(shown, start)
        if i < 0:
            return spans
        j = i + len(shown)
        before = doc_text[i - 1] if i > 0 else ""
        before2 = doc_text[i - 2] if i > 1 else ""
        after = doc_text[j] if j < len(doc_text) else ""
        after2 = doc_text[j + 1] if j + 1 < len(doc_text) else ""
        bad_before = shown[0].isdigit() and (
            before.isdigit() or before == "."
            or (before != "" and before in SIGNS and not before2.isdigit()))  # 부호. 10-20 같은 범위는 허용
        bad_after = shown[-1].isdigit() and (
            after.isdigit() or (after in ".," and after2.isdigit()))
        bad_unit = _is_ascii_letter(shown[-1]) and after != "" and (_is_ascii_letter(after) or after in "/²³")
        if not (bad_before or bad_after or bad_unit):
            spans.append((i, j))
        start = i + 1


def shown_numbers(shown):
    """shown에 적힌 숫자들: (값, 표기 자릿수의 반 단위)."""
    out = []
    for m in SHOWN_NUMBER_RE.finditer(shown):
        text = m.group(2).replace(",", "")
        decimals = len(text.split(".")[1]) if "." in text else 0
        value = float(text) * (-1 if m.group(1) else 1)
        out.append((value, 0.5 * 10 ** -decimals))
    return out


def _eval_expr(expr, variables):
    names = dict(_CONSTS)
    names.update(variables or {})

    def ev(node):
        if isinstance(node, ast.Expression):
            return ev(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) \
                and not isinstance(node.value, bool):
            return node.value
        if isinstance(node, ast.Name) and node.id in names:
            return names[node.id]
        if isinstance(node, ast.BinOp) and type(node.op) in _BINOPS:
            return _BINOPS[type(node.op)](ev(node.left), ev(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _UNOPS:
            return _UNOPS[type(node.op)](ev(node.operand))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                and node.func.id in _FUNCS and not node.keywords:
            return _FUNCS[node.func.id](*[ev(a) for a in node.args])
        raise ValueError(f"허용하지 않는 식 요소: {ast.dump(node)[:60]}")

    return float(ev(ast.parse(expr, mode="eval")))


def _run_cmd(cmd, base_dir, timeout_s):
    proc = subprocess.run(cmd, cwd=base_dir, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=timeout_s)
    if proc.returncode != 0:
        raise ValueError(f"명령 실패(exit {proc.returncode}): {proc.stderr.strip()[-200:]}")
    lines = [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()]
    if not lines:
        raise ValueError("명령이 아무것도 출력하지 않음")
    return float(lines[-1])


def _fmt(x, tol):
    if tol and tol > 0:
        digits = max(0, -math.floor(math.log10(tol))) + 1
        return f"{x:.{digits}f}"
    return f"{x:.6g}"


def check(doc_text, items, base_dir, timeout_s=120):
    """항목마다 (id, 'PASS'|'FAIL'|'SOURCE', 메시지)."""
    results = []
    for item in items:
        iid, shown = item["id"], item["shown"]
        if not shown_spans(doc_text, shown):
            results.append((iid, "FAIL", f"본문에 없음: {shown!r}"))
            continue
        if "expr" not in item and "cmd" not in item:
            label = "가정값" if item.get("kind") == "가정값" else "출처만"
            results.append((iid, "SOURCE", f"{label}: {item.get('source', '-')}"))
            continue
        value = float(item["value"])
        if not item.get("anchor"):
            nums = shown_numbers(shown)
            if not any(abs(n - value) <= half + 1e-9 for n, half in nums):
                results.append((iid, "FAIL", f"표기 숫자 {[n for n, _ in nums]}가 value {value}와 맞지 않음 "
                                             f"(일부러 다른 문구를 기준점으로 쓰면 \"anchor\": true)"))
                continue
        try:
            if "expr" in item:
                computed = _eval_expr(item["expr"], item.get("vars"))
            else:
                computed = _run_cmd(item["cmd"], base_dir, timeout_s)
        except subprocess.TimeoutExpired:
            results.append((iid, "FAIL", f"계산 못 함: {timeout_s}s 안에 끝나지 않음"))
            continue
        except Exception as exc:  # 계산 실패는 모두 실패로 낸다. 통과시키지 않는다.
            results.append((iid, "FAIL", f"계산 못 함: {exc}"))
            continue
        tol = float(item["tol"])
        if abs(computed - value) <= tol:
            results.append((iid, "PASS", f"계산값 {_fmt(computed, tol)} (표기 {shown!r})"))
        else:
            results.append((iid, "FAIL",
                            f"계산값 {_fmt(computed, tol)} ≠ 표기값 {value} (허용 {tol})"))
    return results


def _prose_lines(doc_text):
    """(줄 번호, 태그와 링크 주소를 지운 줄). 펜스 코드와 $$ 블록은 건너뛴다."""
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
        yield no, LINK_URL_RE.sub("]", TAG_RE.sub("", line))


def find_unregistered(doc_text, items, ignore):
    """본문 숫자 중 등록된 표기 안에도, 무시 패턴에도 걸리지 않는 것: (줄, 숫자, 문맥)."""
    patterns = [re.compile(p) for p in DEFAULT_IGNORE + list(ignore)]
    shown_list = [it["shown"] for it in items]
    out = []
    for no, text in _prose_lines(doc_text):
        covered = []
        for shown in shown_list:
            covered += shown_spans(text, shown)
        for pat in patterns:
            covered += [m.span() for m in pat.finditer(text)]
        for m in NUMBER_RE.finditer(text):
            a, b = m.span()
            if any(s <= a and b <= e for s, e in covered):
                continue
            ctx = text[max(0, a - 15):b + 15].strip()
            out.append((no, m.group(), ctx))
    return out


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--doc", required=True)
    ap.add_argument("--numbers", required=True)
    ap.add_argument("--strict", action="store_true", help="미등록 숫자가 있어도 실패로 친다")
    ap.add_argument("--timeout", type=float, default=120)
    args = ap.parse_args(argv)
    try:
        with open(args.doc, encoding="utf-8-sig") as f:
            doc = f.read()
        items, ignore = load_numbers(args.numbers)
    except (OSError, ValueError) as exc:
        print(f"입력 오류: {exc}")
        return 2
    base_dir = os.path.dirname(os.path.abspath(args.numbers))
    results = check(doc, items, base_dir, timeout_s=args.timeout)
    for iid, status, msg in results:
        print(f"{status} {iid} {msg}")
    unreg = find_unregistered(doc, items, ignore)
    for no, tok, ctx in unreg:
        print(f"UNREG L{no} {tok} | {ctx}")
    n_pass = sum(1 for r in results if r[1] == "PASS")
    n_fail = sum(1 for r in results if r[1] == "FAIL")
    n_src = sum(1 for r in results if r[1] == "SOURCE")
    print(f"요약: 재계산 통과 {n_pass} · 실패 {n_fail} · 출처만 {n_src} · 미등록 숫자 {len(unreg)}")
    if n_fail or (args.strict and unreg):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
