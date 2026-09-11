# AI 강의 뉴스 큐레이션

생성형 AI 활용 강의의 오프닝용 콘텐츠 모음. 최신 생성형 AI/LLM **뉴스(news)** 와
AI 관련 재미있는 **이야기·사례(story)** 를 조사해 JSON에 쌓고, 스크립트로
월별 정적 웹사이트를 생성한다.

## 구조

```
ai-news-lecture/
├── data/
│   └── entries-YYYY-MM.json   # 월별 1파일. 처음엔 빈 배열 []
├── generate_html.py           # 최초 1회 작성. 이후엔 실행만 (절대 다시 고쳐 쓰지 않음)
├── index.html                 # 최근 30일 카드 + 검색 + 뉴스/이야기/논문 필터 (스크립트가 생성)
├── archive/
│   ├── index.html             # 모든 월 목록 (스크립트가 생성)
│   └── YYYY-MM.html           # 월별 전체 항목 (스크립트가 생성)
├── deploy.sh                  # 재생성 + 배포 훅 (배포처는 추후 설정)
└── README.md
```

## entries 항목 스키마 (절대 변경 금지)

```json
{
  "id": "YYYY-MM-DD-NN",
  "date": "YYYY-MM-DD",
  "category": "news 또는 story 또는 paper",
  "title": "제목",
  "summary": "너의 언어로 쓴 3~4문장 요약 (기사 원문 그대로 베끼지 말 것)",
  "why_interesting": "강의 시작 전에 왜 이 이야기가 흥미를 끄는지 1~2문장 코멘트",
  "source_url": "출처 링크",
  "confidence": "verified 또는 unverified_but_fun"
}
```

## 데이터 저장 규칙 (절대 준수)

- 새 항목은 **오늘 날짜가 속한 달의 파일** `data/entries-YYYY-MM.json`에만 append.
- 해당 월 파일이 없으면 빈 배열 `[]`로 만든 뒤 append.
- 기존 항목은 절대 수정·삭제하지 않는다 (삭제는 별도 정리 작업에서만).
- 파일 전체를 새로 쓰지 말고 항상 append 방식으로 처리한다.
- **모든 항목(news/story/paper) 공통:** 검색 결과·출처에 명확히 나와 있지 않은 구체적 숫자(페이지 수, 메시지 수 등), 인명, 코드네임은 절대 지어내지 않는다. 확인 안 되면 "정확한 수치는 확인되지 않음"처럼 쓰거나 그 부분을 생략한다.
- **논문(paper) 조사는 화요일·금요일에만 진행**한다 (나머지 요일은 뉴스/이야기만).

## 일상 작업 흐름

1. 최신 생성형 AI/LLM 뉴스와 흥미로운 AI 이야기를 조사한다.
2. 위 스키마대로 이번 달 entries JSON에 append 한다.
3. `python3 generate_html.py` 실행 → index.html / archive 갱신.
4. (선택) `git add -A && git commit`으로 변경 이력 남긴다.

## 사이트 재생성

```bash
python3 generate_html.py
```

`data/entries-*.json`을 전부 읽어 index.html(최근 30일), archive/index.html(월 목록),
archive/YYYY-MM.html(월별 전체)을 다시 만든다. news는 파란색, story는 주황색, paper(논문)는 초록색 카드.

## GitHub 원격 저장소

의도적으로 아직 연결하지 않았다. 원격 연결은 별도 지시 시 진행한다.
