# mcp_server_neis_api

NEIS(나이스) 교육정보 개방 포털 API를 Model Context Protocol(MCP) Server로 노출하는 SSE 기반 서버입니다.

## 특징
- 전송 방식: Server-Sent Events(SSE)
- 기본 포트: `8000`
- 제공 도구(Tools):
	- `get_school_info(school_name)` : 학교 기본 정보(학교명/학교코드/교육청 등)
	- `get_school_schedule(school_code, org_code, from_date, to_date)` : 학교코드+교육청코드 기반 일정(학사일정)
	- `get_school_schedule_by_name(school_name, from_date, to_date, grade=[1,2,3], target_org=None)` : 학교명으로 바로 일정 조회 (학년 필터 포함)
- 환경변수에 NEIS 서비스 키가 없으면 강등(degraded) 모드로 동작: 각 조회 결과를 최대 5개까지만 반환

## 환경 설정 (.env)
`.env` 파일(또는 환경변수)에 다음을 지정하세요:

```
NEIS_SERVICE_KEY=당신의_서비스_키
```

대안 변수명: `SERVICE_KEY` (둘 중 하나만 있어도 됨)

키가 없으면:
- 결과는 최대 5개로 제한되고 `message` 필드에 `Success (degraded mode: key missing, limited to 5)`가 표시됩니다.
- 교육청/학교 일정 API 호출 파라미터에서 페이지 크기(`pSize`)가 5로 강제됩니다.

## 설치 & 실행

```bash
git clone <repo-url>
cd mcp_server_neis_api
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt  # (requirements.txt가 있다면)
python src/server.py  # 기본 8000 포트에서 SSE 서버 시작
```

서버 실행 시 출력 예:
```
Start MCP server
```

기본 포트는 FastMCP 내부에서 8000으로 구동됩니다(별도 설정 없을 경우).

## MCP Inspector로 테스트하기

MCP Inspector를 사용해 서버를 직접 탐색할 수 있습니다.

시작 명령:
```bash
npx @modelcontextprotocol/inspector python ./server.py
```

그 후 Inspector UI에서 SSE로 연결되어 툴 목록 및 호출을 직접 확인할 수 있습니다.

## 클라이언트 설정 JSON 예시

MCP 클라이언트(예: VS Code 확장 또는 커스텀 런처)에서 사용할 설정 예시:

```json
{
	"mcpServers": {
		"neis_org": {
			"type": "python",
			"command": "python",
			"args": ["./src/server.py"],
			"transport": {
				"type": "sse",
				"port": 8000
			},
			"env": {
				"NEIS_SERVICE_KEY": "${env:NEIS_SERVICE_KEY}"  
			}
		}
	}
}
```

> `port`를 생략하면 기본값(8000)을 사용합니다. 환경변수는 OS 또는 런처 설정에서 주입하도록 구성하세요.

## 툴 상세

### `get_school_info`
입력: `school_name` (예: `진관초등학교`)
반환: `{ valid, message, school_num, school_name[], school_code[], org_name[], org_code[] }`

### `get_school_schedule`
입력: `school_code`, `org_code`, `from_date`, `to_date` (YYYYMMDD)
반환: `{ valid, message, schedule_num, event_date[], event_name[], event_type[], event_content[], valid_grade[6][] }`

### `get_school_schedule_by_name`
입력: `school_name`, `from_date`, `to_date`, 선택 `grade`(기본 [1,2,3]), 선택 `target_org`
반환: 일정 항목 리스트 `[ { school_name, event_date, event_name, event_type, event_content, grade } ... ]`

강등 모드(degraded)에서 `school_info`와 `schedule` 관련 조회 모두 최대 5개 결과만 반환합니다.

## 날짜 형식
현재 서버 함수는 입력 날짜(`from_date`, `to_date`)를 그대로 NEIS API에 전달하므로 YYYYMMDD 형식 사용을 권장합니다.

## 에러 처리
- NEIS API 오류 시 `valid=False`와 함께 `message` 필드에 원인 메시지 반환
- 파싱 오류 시 `Error parsing ...` 메시지

## 개발 팁
- `.env` 변경 후 서버를 재시작해야 새 키가 반영됩니다.
- 향후 확장: 캐시 적용, 일정 중복 제거, 타임아웃/리트라이 로직 추가 가능

## 라이선스
본 프로젝트의 라이선스는 저장소 내 LICENSE 파일을 참조하세요.

