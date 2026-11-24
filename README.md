# Nisaba

수학·공학 해설 글과 기능 개발기를 쓰는 Claude Code 플러그인이다. 글을 쓰기 전에 독자와 근거를 정하고, 쓴 뒤에 숫자를 다시 계산하고, 쓴 사람과 다른 맥락의 독자에게 읽힌다.

> **이름:** 니사바(Nisaba)는 수메르 신화에서 글쓰기와 셈을 맡은 여신이다. 서기들은 점토판 끝에 "니사바를 찬양하라"를 적었다. 이 플러그인도 글과 숫자를 함께 다룬다.

## 왜 만들었나

말투를 다듬는 도구는 많다. 그런데 수학·공학 글이 읽히지 않는 이유는 대개 말투가 아니다.

- 쓴 사람은 자기가 건너뛴 단계를 보지 못한다.
- 본문의 숫자가 원본 데이터와 다르다.
- 검토를 반영한 뒤 고친 곳을 다시 확인하지 않는다.
- 근거에 없는 '왜'를 그럴듯한 추측으로 채운다.

Nisaba는 이 네 가지를 절차와 스크립트로 막는다.

## 구성

| 종류 | 이름 | 하는 일 |
| --- | --- | --- |
| 스킬 | `nisaba:write-explainer` | 8단계 흐름: 스펙 → 초안 → 결정적 검사 → 독자 검토 → 전문가 검토 → 재검증 → 최종 상태 → 게시 |
| 스킬 | `nisaba:cold-read` | 독자 검토만 따로 돌린다. 독자 요약서에서 기대 답을 빼고 cold-reader 에이전트에게 넘긴다 |
| 스킬 | `nisaba:rubric-review` | 전문가 검토만 따로 돌린다. 숫자 검사를 먼저 돌리고 rubric-reviewer 에이전트에게 넘긴다 |
| 에이전트 | `nisaba:cold-reader` | 독자 요약서에 적힌 독자가 되어 글을 처음부터 읽는다. 막힌 곳과 판단 질문의 답을 보고한다 |
| 에이전트 | `nisaba:rubric-reviewer` | 루브릭(L1–L7, P)과 주장 근거 표로 정확성과 근거를 판정한다 |
| 스크립트 | `check_numbers.py` | 본문의 숫자를 식이나 명령으로 다시 계산해 대조한다. 등록하지 않은 숫자도 찾는다 |
| 스크립트 | `check_terms.py` | 시리즈 용어 사전과 대조해 피할 말을 찾는다 |
| 스크립트 | `check_style.py` | 긴 문장, 쉼표로 이은 절, 코드 표기가 빠진 식별자, 그림 없는 절, 분량 초과를 후보로 뽑는다 |
| 스크립트 | `list_questions.py` | 글이 스스로 던진 질문을 뽑는다. 답했는지 질문 장부로 확인한다 |
| 스크립트 | `review_state.py` | 검토 결과를 파일 해시와 묶어 기록한다. 기록 뒤 파일이 바뀌면 '낡음'으로 보인다 |
| 참고 문서 | `references/*.md` 7개 | 스펙 틀, 근거 상태, 구성, 비유·질문 장부, 한국어 문장, 루브릭, 숫자 목록 형식 |

에이전트는 글을 읽기만 한다. 글을 고치는 일은 작성자가 한다.

에이전트는 `/` 목록에 뜨지 않는다. 사용자가 부를 때는 입구 스킬 `cold-read`, `rubric-review`를 쓴다.

## 설치

```bash
claude plugin marketplace add XsQuare01/nisaba
claude plugin install nisaba@nisaba
```

스크립트는 Python 3.10 이상의 표준 라이브러리만 쓴다.

## 쓰는 법

수학·공학 해설 글이나 기능 개발기를 쓰거나 고쳐 달라고 하면 스킬이 불린다. `/nisaba:write-explainer`로 직접 불러도 된다.

검토만 따로 돌릴 수도 있다.

```text
/nisaba:cold-read <글 파일이나 글 폴더> [독자 설명]
/nisaba:rubric-review <글 파일이나 글 폴더> [근거 자료 경로...]
```

독자 설명을 주지 않으면 글 폴더 `spec.md`의 독자 요약서를 쓴다. 그것도 없으면 누구에게 읽힐지 묻는다.

글마다 폴더 하나를 둔다.

```text
<글 폴더>/
  spec.md            독자 요약서, 목적, 주장 근거 표, 질문 장부, 그림 목록
  numbers.json       본문 숫자 목록 (check_numbers 입력)
  page.md            본문
  figs/              그림과 그림 스크립트
  reviews/<날짜>.md  검토 기록과 후속 처리
  reviews/state.json 검토 상태 (review_state 출력)
```

흐름은 이렇다.

1. **스펙:** 독자 요약서(역할, 상황, 읽은 뒤 할 일)와 목적 한 문장을 쓴다. 독자 요약서는 쓰기 전에 사용자에게 확인받는다. 주장마다 근거 상태를 정한다.
2. **초안:** 숫자를 쓸 때마다 `numbers.json`에 등록한다. 비유를 쓰면 대응표를 채운다.
3. **결정적 검사:** 스크립트 네 개를 돌린다. 숫자 실패는 0이어야 한다.
4. **독자 검토:** cold-reader에게 독자 요약서와 본문만 넘긴다. 판단 질문의 기대 답은 넘기지 않는다.
5. **전문가 검토:** rubric-reviewer에게 루브릭, 스펙, 근거 자료 경로를 넘긴다.
6. **재검증:** 고친 종류에 따라 검사와 검토를 다시 돌린다.
7. **최종 상태:** `review_state.py status`로 통과 · 미해결 · 미검토를 뽑아 기록 끝에 붙인다.
8. **게시:** 사용자 확인 뒤에 올린다. 올린 화면을 다시 불러와 수식, 그림, 글자 크기를 본다.

스크립트는 따로 써도 된다.

```bash
S=<플러그인 폴더>/skills/write-explainer/scripts
python $S/check_numbers.py --doc page.md --numbers numbers.json
python $S/check_terms.py --doc page.md --terms terms.json
python $S/check_style.py --doc page.md --max-len 60
python $S/list_questions.py --doc page.md
python $S/review_state.py status --state reviews/state.json --require check_numbers cold-reader
```

`numbers.json` 형식은 [`references/numbers-format.md`](skills/write-explainer/references/numbers-format.md)에 있다.

## 지키는 원칙

- **근거 상태를 나눈다.** 측정, 계산, 가정값, 코드 사실, 가설, 확인 못 함. 가설은 현상의 원인 설명에만 쓰고 확인 방법을 붙인다. 다른 사람의 설계 이유를 추측으로 채우지 않는다.
- **증명 의무는 논리식에서 정한다.** "A인 경우에만 B"는 B ⇒ A 한 방향이다.
- **횟수를 다 쓴 검토는 통과가 아니다.** 마지막 수정 뒤 다시 보지 못한 검토는 '미검토'로 남긴다.
- **작성자 자료와 독자 본문을 나눈다.** 조사 경위, 커밋 시각, 테스트 이름은 본문이 아니라 참고 절에 모은다.
- **규칙이 있는 저장소에서는 저장소 규칙이 먼저다.** `AGENTS.md` → 작성 정본 → 글별 스펙 → 이 스킬 순서로 따른다.

## 검증

- 단위 테스트: `python -m unittest discover -s tests` (66개)
- 에이전트 시험: [`evals/README.md`](evals/README.md). 공개 보류 시험 4개는 블로그 실제 사례다. 회사 문서로 만든 기본 시험은 저장소에 넣지 않았다.

## 한계

- 한국어 글을 기준으로 만들었다. 문장 규칙과 검사 정규식이 한국어를 가정한다.
- `check_style.py`는 후보만 뽑는다. 고칠지는 사람이 문맥을 보고 정한다.
- 독자 검토 한 회차는 에이전트 한 번이라 수만 토큰이 든다.

## 바탕

- 작성자의 블로그 글쓰기 체계를 일반화했다: [XsQuare01.github.io](https://github.com/XsQuare01/XsQuare01.github.io)의 `docs/writing-rules.md`, `docs/review-rubric.md`.
- 기능 글 구성은 Riot, Figma, 토스, Discord 기술 블로그를 분석해 정했다.
- 문장 연결 규칙은 Gopen·Swan, "The Science of Scientific Writing"(1990)을 따랐다.

## 라이선스

[MIT](LICENSE)
