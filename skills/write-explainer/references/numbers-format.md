# 수량 목록(numbers.json)과 용어 사전 형식

## numbers.json

본문(page.md)에 나오는 숫자마다 한 항목을 둔다. `check_numbers.py`가 읽는다.

```json
{
  "ignore": ["`[^`]*`", "\\d{4}년 \\d{1,2}월 \\d{1,2}일"],
  "items": [
    {"id": "C1-length", "claim": "C1", "kind": "측정", "shown": "약 3.05 m", "unit": "m",
     "value": 3.054, "tol": 0.005, "cmd": ["python", "figdata.py", "length_m"], "source": "측정 데이터 파일 경로"},
    {"id": "C6-ratio", "claim": "C6", "kind": "계산", "shown": "1.1배", "value": 1.1, "tol": 0.001, "expr": "55/50"},
    {"id": "C17-pytest", "kind": "측정", "shown": "55개 테스트", "source": "reviews/pytest.txt"},
    {"id": "C3-tilt", "kind": "가정값", "shown": "10°", "note": "설명용 각도"}
  ]
}
```

| 필드 | 필수 | 뜻 |
| --- | --- | --- |
| `id` | 예 | 항목 이름. 겹치면 입력 오류 |
| `claim` | | 스펙 주장 근거 표의 ID |
| `kind` | 예 | `계산` · `측정` · `가정값` · `코드 사실` (`claims-evidence.md`의 근거 상태) |
| `shown` | 예 | 본문에 적힌 그대로의 표기. 본문에 이 문자열이 있어야 한다. 앞뒤에 숫자·부호·천 단위 쉼표·단위 글자가 붙어 다른 수량이 되면 없는 것으로 친다 |
| `value`, `tol` | expr·cmd가 있으면 예 | 기대값과 허용 오차. 다시 계산한 값이 `value ± tol` 안이어야 통과 |
| `expr` | | 다시 계산하는 식. 숫자, `+ - * / ** %`, `vars`의 이름, 함수 `sqrt sin cos tan asin acos atan atan2 radians degrees hypot exp log log10 floor ceil abs min max round`, 상수 `pi e`만 쓴다 |
| `cmd` | | 다시 계산하는 명령(문자열 목록). `numbers.json`이 있는 폴더에서 실행하고, 표준 출력의 마지막 비어 있지 않은 줄을 실수로 읽는다. 120초 안에 끝나야 한다 |
| `vars` | | `expr`에서 쓸 이름과 값 |
| `source` | 측정·코드 사실이면 예 | 근거 위치(파일 경로, 커밋, 로그) |
| `anchor` | | `true`이면 `shown`의 숫자와 `value`를 대조하지 않는다. 예: "60 Hz"라는 문구를 기준점으로 50 ms를 확인할 때 |
| `unit`, `note` | | 메모 |

규칙:
- `expr`와 `cmd`는 함께 둘 수 없다. `kind`가 `계산`이면 둘 중 하나가 있어야 한다.
- `anchor`가 아니면 `shown`에 적힌 숫자 가운데 하나가 `value`와 표기 자릿수 안에서 맞아야 한다("약 3.05 m"이면 3.045~3.055). 본문 숫자를 고치고 `value`를 그대로 두면 실패한다.
- 다시 계산하지 않는 항목(측정·코드 사실·가정값에 expr·cmd 없음)은 '출처만'으로 따로 센다. 통과로 세지 않는다.
- 다른 사람이 만든 `numbers.json`의 `cmd`는 열어 본 뒤 돌린다. 임의 명령이 실행된다.

`ignore`는 줄마다 적용하는 정규식 목록이다. 날짜(`YYYY-MM-DD`), 절·편 번호(`3절`), 줄 첫머리 번호 목록(`1. `)은 기본으로 빠진다. 펜스 코드와 `$$` 블록, `<...>` 태그, 마크다운 링크 주소 안의 숫자도 빠진다. 노션 글이면 보통 다음을 더한다: 인라인 코드 `` `[^`]*` ``, 한국어 날짜, 시각, 제목 번호 `^#+\s*\d+\.`, 수식 첨자 `[_^]\{[^}]*\}`.

## 용어 사전(terms.json)

시리즈마다 하나를 두고 `check_terms.py --terms`로 넘긴다.

```json
{"terms": [{"use": "좌표 변환", "avoid": ["좌표계 변환"], "note": "시리즈 편 제목과 맞춘다"}]}
```

- `use`: 쓸 말. `avoid`: 피할 말 목록. 펜스 코드, 인라인 코드, 쓸 말 안에 든 피할 말은 지적하지 않는다.
