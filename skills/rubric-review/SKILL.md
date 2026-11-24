---
name: rubric-review
description: 글을 nisaba:rubric-reviewer 에이전트에게 루브릭(L1–L7, P)과 주장 근거 표로 판정받는다. 사용자가 "전문가 검토 돌려 줘", "루브릭으로 봐 줘"라고 하거나 /nisaba:rubric-review로 부를 때 쓴다. write-explainer 흐름 중이면 그 5단계 규칙도 함께 따른다.
argument-hint: <글 파일이나 글 폴더> [근거 자료 경로...]
---

# 전문가 검토 (rubric-reviewer 부르기)

`nisaba:rubric-reviewer`는 에이전트라서 `/` 목록에 뜨지 않는다. 이 스킬은 사용자가 그 에이전트를 직접 부르는 입구다.

독자 검토와 달리 전문가 검토자에게는 자료를 많이 넘길수록 좋다. 근거를 직접 열어 대조해야 판정할 수 있기 때문이다.

## 1. 넘길 자료 모으기

- **글:** 인자가 파일이면 그 파일이다. 폴더면 `page.md`를 찾고, 본문이 여러 페이지면 모두 넘긴다. 인자가 없으면 대화에서 작업 중인 글을 쓰고, 그것도 없으면 묻는다.
- **그림:** 본문이 가리키는 이미지 경로를 절대 경로로 모은다.
- **스펙:** 글 폴더의 `spec.md`(있으면). 주장 근거 표와 판단 질문의 기대 답까지 그대로 넘긴다.
- **루브릭과 근거 기준:** `../write-explainer/references/review-rubric.md`, `../write-explainer/references/claims-evidence.md`. 경로는 이 스킬 폴더 기준이고, 넘길 때는 절대 경로로 바꾼다.
- **숫자 검사 결과:** 글 폴더에 `numbers.json`이 있으면 먼저 검사를 돌린다. 출력은 `reviews/` 폴더가 있으면 거기에, 없으면 임시 폴더에 저장한다.

  ```
  python <이 스킬 폴더>/../write-explainer/scripts/check_numbers.py --doc <글 파일> --numbers numbers.json
  ```

- **근거 자료 경로:** 인자로 받은 경로, 스펙의 주장 근거 표에 적힌 출처, 본문 참고 절의 출처를 모은다. 하나도 없으면 없는 채로 넘기고, 출처 대조(L6)가 `source unavailable`로 나온다고 사용자에게 알린다.
- **게시 화면:** 렌더된 페이지 정보가 있을 때만 넘긴다. 이때만 범주 P를 본다.

## 2. 에이전트 부르기

- `Agent` 도구를 `subagent_type: "nisaba:rubric-reviewer"`로 부른다. 프롬프트에는 1단계 자료의 절대 경로를 종류별로 나눠 적는다.
- 그 에이전트를 쓸 수 없으면 이 플러그인의 `agents/rubric-reviewer.md` 본문(frontmatter 아래)을 general-purpose 서브에이전트 프롬프트 앞에 붙인다.

## 3. 기록하고 보고하기

글 폴더에 `reviews/state.json`이 있거나 write-explainer 흐름 중이면, 글을 고치기 전에 결과를 기록한다.

```
python <이 스킬 폴더>/../write-explainer/scripts/review_state.py record --state reviews/state.json --check rubric-reviewer --outcome 통과|미해결 --result "<🔴·🟡·🟢 개수>" --files <글 파일들> numbers.json <그림 폴더>
```

🔴이나 🟡이 하나라도 있으면 미해결이다.

사용자에게는 이렇게 보고한다.

- 검토 범위: 에이전트가 적은 그대로 옮긴다(읽은 파일, 연 출처, 열지 못한 출처).
- 🔴·🟡 지적: 위치 · 인용 · 문제 · 고칠 방향
- 🟢 개수, 그리고 미검토로 남은 범주와 그 이유

이 스킬은 글을 고치지 않는다. 원래 판정은 고쳐 쓰지 않는다. 반영 내역은 검토 기록 끝 「후속 처리」에 적는다.
