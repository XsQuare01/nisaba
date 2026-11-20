---
name: write-explainer
description: 수학·공학 해설 글이나 기능 개발기를 쓰거나 고칠 때 쓴다. 독자 요약서·주장 근거 표·비유 대응·숫자 재계산·독자 역할 검토로 막히는 곳과 틀린 곳을 줄인다.
---

# 수학·공학 글쓰기

말투만 다듬어서는 독자가 막히는 곳을 못 찾는다. 쓴 사람은 자기 글이 건너뛴 단계를 보지 못한다.
이 스킬은 쓰기 전에 스펙을 세우고, 쓴 뒤에 쓴 사람과 다른 맥락에서 두 번 검토하고, 고친 뒤에 다시 확인하게 한다.

**쓰지 않는 경우:** 원문을 옮기거나 다듬는 일(원문 보존 작업)은 새 글 쓰기가 아니다. 그런 요청이면 멈추고 범위 밖이라고 알린다.

## 산출물

글마다 폴더 하나를 둔다. 위치는 사용자나 프로젝트 규칙을 따른다.

```
<글 폴더>/
  spec.md            1단계 스펙
  numbers.json       수량 목록 (check_numbers 입력)
  page.md            본문 (노션 글이면 노션 마크다운)
  make_figs.py, figs/ 그림과 그림 스크립트
  reviews/<날짜>.md  검토 기록 + 후속 처리 + 최종 상태
  reviews/state.json 검토 상태 (review_state 출력)
```

`<스킬>`은 이 스킬 폴더다. 스크립트는 `python`으로 부른다.

## 흐름 (8단계)

### 1. 스펙
- 읽을 것: `references/spec-template.md`, `references/claims-evidence.md`, `references/structure.md`, `references/explain-devices.md`
- 주제와 출처를 조사한다(코드, 문서, 이력, 데이터).
- 독자 요약서를 사용자에게 확인받는다. 다 쓴 뒤에 독자를 추정해 정하지 않는다.
- 판단 질문 1~2개와 기대 답을 정한다. 기대 답은 cold-reader에게 주지 않는다.
- 주장 근거 표에서 주장마다 근거 상태와 닫을 위치를 정한다. 자리가 없으면 주장을 약하게 고치거나 절을 만든다.
- 근거에서 못 찾은 '왜'와 수치는 지어내지 않는다. 모아서 사용자에게 한 번에 묻는다. 답이 없으면 '확인 못 함'으로 쓴다. 가설은 현상의 원인 설명에만 쓰고 확인 방법을 붙인다.
- 장르 기본형과 모듈, 비유 대응표, 질문 장부 초안, 그림 목록을 쓴다.

### 2. 초안
- 읽을 것: `references/structure.md`, `references/explain-devices.md`, `references/korean-style.md`
- 숫자를 쓸 때마다 `numbers.json`에 등록한다. 형식은 `references/numbers-format.md`.
- 비유를 쓰면 대응표의 '원래 개념으로 돌아오는 문장'까지 본문에 쓴다.

### 3. 결정적 검사
```
python <스킬>/scripts/check_numbers.py --doc page.md --numbers numbers.json
python <스킬>/scripts/check_terms.py --doc page.md --terms <용어 사전.json>
python <스킬>/scripts/list_questions.py --doc page.md
python <스킬>/scripts/check_style.py --doc page.md
```
- check_style은 후보 목록이다. 긴 문장·쉼표 이음은 `references/korean-style.md` 「문장 호흡과 주어·서술어」로, 시각 자료 없는 절·분량은 `references/structure.md`로 판단한다. 맨 식별자는 인라인 코드로 고친다.
- check_numbers 실패는 0이어야 한다. '출처만'은 통과가 아니다. 요약 줄을 검토 기록에 옮긴다.
- 미등록 숫자는 수량이면 등록하고, 수량이 아니면(날짜, 번호, 식별자) `ignore`에 넣는다.
- list_questions가 뽑은 질문마다 질문 장부에 종류와 답한 위치를 적는다.
- 결과를 남긴다:
```
python <스킬>/scripts/review_state.py record --state reviews/state.json --check check_numbers --outcome 통과 --result "<요약 줄>" --files page.md numbers.json
```
  (check_terms도 같은 식으로 남긴다.)

### 4. 독자 검토 (cold-reader)
- 넘길 것: 독자 요약서(판단 질문 포함, 기대 답 제외), `page.md`, 그림 파일. 스펙의 나머지, 작성 메모, 고치기 전후 표시는 넘기지 않는다.
- 결과가 오면 **고치기 전에** `record --check cold-reader --outcome 미해결|통과 --files page.md figs`로 남긴다. 고친 뒤에 남기면 검토한 판과 묶이지 않는다.
- 막힘을 고친다. 판단 질문의 답이 기대 답과 다르면 '오해'(범주 R)로 기록하고 그 답을 낳은 본문을 고친다.

### 5. 전문가 검토 (rubric-reviewer)
- 넘길 것: `references/review-rubric.md`, `references/claims-evidence.md`, spec, page, 그림, check_numbers 출력, 근거 자료 경로.
- 결과가 오면 고치기 전에 `record --check rubric-reviewer --files page.md numbers.json figs`로 남긴다.
- 🔴·🟡을 반영한다. 원래 판정은 고쳐 쓰지 않고, 처리 내역을 검토 기록 끝 「후속 처리」에 적는다.
- 4단계와 5단계를 같은 초안에 동시에 돌려도 된다. 그 경우 두 결과를 함께 반영하고 6단계로 닫는다.

### 6. 재검증
고친 종류에 따라 다시 확인한다.
- 본문·숫자·그림을 하나라도 바꿨다 → 3단계 검사를 다시 돌리고 기록한다.
- 정의나 설명 순서를 바꿨다 → 그 구간을 cold-reader가 다시 읽는다. cold-reader는 한 편에 최대 2회다.
- 주장·수식·코드를 바꿨다 → rubric-reviewer가 그 항목만 다시 본다.

### 7. 최종 상태
```
python <스킬>/scripts/review_state.py status --state reviews/state.json --require check_numbers check_terms cold-reader rubric-reviewer
```
- 출력(통과 · 미해결 · 미검토)을 검토 기록 끝에 붙인다.
- 횟수를 다 써서 멈춘 검토는 통과가 아니다. 마지막 수정 뒤 다시 보지 못한 것은 미검토로 남긴다.
- 미해결이나 미검토가 있으면 게시 보고에 그대로 적는다.

### 8. 게시와 게시 화면 검토
- 게시는 사용자 확인 뒤에 한다.
- 올린 뒤 페이지를 다시 불러와 `references/review-rubric.md`의 범주 P를 본다: 수식 렌더와 긴 식 줄바꿈, 그림 열림과 캡션 위치, 그림 글자 크기, 이해에 꼭 필요한 설명이 접힌 토글 안에 숨지 않았는지.

## 에이전트 부르기

- 플러그인이 설치돼 있으면 `nisaba:cold-reader`, `nisaba:rubric-reviewer`를 쓴다.
- 없으면 이 플러그인의 `agents/cold-reader.md`, `agents/rubric-reviewer.md` 본문(frontmatter 아래)을 general-purpose 서브에이전트 프롬프트로 넘기고, 읽을 파일 경로를 덧붙인다.
- 에이전트는 글을 고치지 않는다. 고치는 일은 작성자가 한다.

## 규칙이 있는 저장소에서 쓸 때

- 우선순위: 저장소의 `AGENTS.md` → 작성 정본 → 포스트별 스펙 → 이 스킬. 충돌하면 저장소 규칙을 따른다.
- 이 스킬은 스펙 칸(판단 질문, 비유 대응표, 질문 장부, 수량 목록)과 독자 검토만 보탠다.
- 판정과 게시 게이트는 저장소의 리뷰 명령(예: 블로그의 `/review-post`)과 빌드 검사에 넘긴다.

## 반목표 (이렇게 되면 실패)

- 짧게 만들려고 조건, 논증 단계, 비유, 자문자답을 지운다.
- 검토자가 확인 범위를 밝히지 않고 "문제없음"만 낸다.
- 고쳐 쓰다가 근거에 없는 사실이 더해지거나 숫자가 바뀐다.
- 모르는 수치나 다른 사람의 설계 이유를 가설로 채운다.
- 실험 질문이나 다음 글로 넘긴 질문까지 '답 없는 질문'으로 지운다.
