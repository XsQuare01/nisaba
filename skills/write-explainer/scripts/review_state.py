"""검토 결과를 글의 판(파일 해시)에 묶고, 지금도 유효한지 본다.

record: 검사 이름, 결과(통과|미해결), 요약, 대상 파일(본문·그림 폴더·수량 목록)의 해시를 남긴다.
status: 검사마다 기록한 파일을 다시 해시해 '최신' 또는 '낡음'을 보이고,
        통과 · 미해결 · 미검토 세 묶음으로 나눈다. 낡은 검사와 --require에 있는데 기록이 없는 검사는 미검토다.

사용:
  python review_state.py record --state reviews/state.json --check cold-reader --outcome 통과 --result "막힘 없음" --files page.md figs
  python review_state.py status --state reviews/state.json --require check_numbers check_terms cold-reader rubric-reviewer
status exit 0 = 미해결·미검토 없음, 1 = 있음. 입력 오류는 2.
"""
import argparse
import datetime
import hashlib
import json
import os
import sys

OUTCOMES = ("통과", "미해결")


def _files_of(path):
    """(이름, 실제 경로) 목록. 이름은 실행 위치와 무관하게 인자 기준 상대 이름이다."""
    path = os.path.abspath(path)
    base = os.path.basename(path.rstrip("\\/"))
    if os.path.isdir(path):
        out = []
        for root, _, files in os.walk(path):
            for fn in files:
                full = os.path.join(root, fn)
                rel = os.path.relpath(full, path).replace("\\", "/")
                out.append((f"{base}/{rel}", full))
        return sorted(out)
    return [(base, path)]


def digest(paths):
    h = hashlib.sha256()
    for p in paths:
        if not os.path.exists(p):
            h.update(f"<없음>{os.path.abspath(p)}\0".encode("utf-8"))
            continue
        for name, full in _files_of(p):
            h.update(name.encode("utf-8") + b"\0")
            with open(full, "rb") as f:
                h.update(f.read())
            h.update(b"\0")
    return h.hexdigest()


def _load(state_path):
    if not os.path.exists(state_path):
        return {"checks": {}}
    with open(state_path, encoding="utf-8") as f:
        return json.load(f)


def record(state_path, check, outcome, result, paths):
    if outcome not in OUTCOMES:
        raise ValueError(f"outcome은 {'/'.join(OUTCOMES)} 중 하나여야 함")
    if not paths:
        raise ValueError("대상 파일이 하나 이상 있어야 함")
    missing = [p for p in paths if not os.path.exists(p)]
    if missing:
        raise ValueError(f"없는 경로: {missing} — 경로 오타나 실행 위치를 확인한다")
    state = _load(state_path)
    abs_paths = [os.path.abspath(p) for p in paths]
    state["checks"][check] = {
        "outcome": outcome,
        "result": result,
        "digest": digest(abs_paths),
        "files": abs_paths,
        "at": datetime.datetime.now().isoformat(timespec="seconds"),
    }
    os.makedirs(os.path.dirname(os.path.abspath(state_path)), exist_ok=True)
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def details(state_path):
    """검사마다 (이름, 최신 여부, outcome, result)."""
    state = _load(state_path)
    out = []
    for name, c in state["checks"].items():
        out.append((name, digest(c["files"]) == c["digest"], c["outcome"], c["result"]))
    return out


def status(state_path, require=()):
    res = {"통과": [], "미해결": [], "미검토": []}
    seen = set()
    for name, fresh, outcome, _ in details(state_path):
        seen.add(name)
        if not fresh:
            res["미검토"].append(name)
        else:
            res[outcome].append(name)
    for name in require:
        if name not in seen:
            res["미검토"].append(name)
    return res


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("record")
    r.add_argument("--state", required=True)
    r.add_argument("--check", required=True)
    r.add_argument("--outcome", required=True, choices=OUTCOMES)
    r.add_argument("--result", required=True)
    r.add_argument("--files", nargs="+", required=True)
    s = sub.add_parser("status")
    s.add_argument("--state", required=True)
    s.add_argument("--require", nargs="*", default=[])
    args = ap.parse_args(argv)
    try:
        if args.cmd == "record":
            record(args.state, args.check, args.outcome, args.result, args.files)
            print(f"기록: {args.check} {args.outcome} — {args.result}")
            return 0
        for name, fresh, outcome, result in details(args.state):
            print(f"{'최신' if fresh else '낡음'} {outcome} {name} — {result}")
        res = status(args.state, args.require)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"입력 오류: {exc}")
        return 2
    print()
    for key in ("통과", "미해결", "미검토"):
        print(f"{key}: {', '.join(res[key]) if res[key] else '없음'}")
    return 1 if res["미해결"] or res["미검토"] else 0


if __name__ == "__main__":
    sys.exit(main())
