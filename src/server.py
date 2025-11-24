"""Minimal NEIS (Korean school info & schedule) MCP Server for Small LLMs
=======================================================================

목표(Purpose)
    - 작은 LLM / 제한된 자원 환경에서도 쉽게 붙일 수 있는 Model Context Protocol(MCP) 툴 서버
    - 한국 교육행정정보시스템(NEIS)에서 학교 기본 정보 및 일정(학사일정) 조회 기능 제공

특징(Features)
    - 세 가지 툴(tool) 정의:
            1) get_school_info(school_name): 학교명으로 코드/지역/설립유형 등 기본 정보 조회
            2) get_school_schedule(school_code, org_code, from_date, to_date): 코드 기반 일정 조회
            3) get_school_schedule_by_name(school_name, from_date, to_date): 학교명만으로 일정 조회
    - FastMCP 사용: 간단한 선언형 데코레이터(@mcp.tool)로 툴 노출
    - SSE(Server-Sent Events) transport로 가볍게 실행 (웹소켓 대비 구현 부담↓)
    - 반환 타입은 dict (LLM이 후처리하기 쉬운 구조)

사용 환경(Environment)
    - Python 3.11+
    - 종속성: fastmcp (mcp.server.fastmcp), 로컬 모듈 neis_api
    - 외부 키/토큰 필요 없음 (공개 NEIS API 래퍼를 사용한다고 가정)

실행 방법(Run)
    1) 의존성 설치 (예시)
         pip install fastmcp
         (프로젝트에 맞는 neis_api 래퍼가 이미 포함되어 있다고 가정)
    2) 서버 실행
         python server.py
    3) 기본 바인딩: host=0.0.0.0, port=8051

MCP 클라이언트 예시(Client Integration Example)
    - (개념적) LLM 런타임이 MCP 툴 목록을 질의 후, 다음 형태의 호출을 구성:
        {
            "tool_name": "get_school_schedule_by_name",
            "arguments": {
                "school_name": "서울고등학교",
                "from_date": "20250101",
                "to_date": "20250131"
            }
        }
    - 서버 응답(dict)을 받아서 LLM 프롬프트에 "일정" 컨텍스트로 삽입

curl 로 직접 확인(Quick Check via curl)
    - FastMCP가 SSE endpoint를 /mcp 로 제공한다면 (구현체에 따라 다를 수 있음) 아래와 같이 테스트:
        curl -N http://localhost:8051/mcp 
        (SSE 스트림이 열리고 이벤트가 수신되면 정상)
    - 또는 추후 별도의 HTTP 라우팅을 확장해 REST 형태로 변환 가능

리소스 절약 팁(Resource Tips for Small LLM)
    - 결과 dict는 최소 필드만 유지(불필요한 텍스트 블록 제거)
    - 일정 범위를 좁게(from_date/to_date 최소화) 지정해 토큰 낭비 줄이기
    - 학교명 검색 실패 시 빈 dict 또는 에러 키 반환 → LLM이 재질의(retry) 로직 설계 가능

예상 반환 구조(Expected Response Shapes)
    get_school_info → {"school_name": str, "school_code": str, "org_code": str, ...}
    get_school_schedule → {"items": [{"date": "YYYYMMDD", "event": str, ...}, ...]}
    get_school_schedule_by_name → 동일하게 items 배열 중심

추가 확장 아이디어(Future Extensions)
    - 캐싱(메모리/파일)으로 반복 요청 속도 향상
    - rate limit / simple auth 추가
    - 오류 형식 통일: {"error": {"type": str, "message": str}}

"""

from mcp.server.fastmcp import FastMCP
from neis_api import neis_get_school_info, neis_get_school_schedule, neis_get_school_schedule_by_name

mcp = FastMCP("neis_org",
              host="0.0.0.0",
              port=8051)

@mcp.tool()
def get_school_info(school_name: str) -> object:
    """학교 기본 정보 조회 / Get school metadata

    Parameters
    ----------
    school_name : str
        (KO) 조회할 학교 이름 (완전하거나 대표명 위주)
        (EN) Full or primary Korean school name to look up.

    Returns
    -------
    object (dict | list)
        Typical dict shape (example):
        {
          "school_name": "서울고등학교",
          "school_code": "1234567",
          "org_code"   : "B10",
          "establishment_type": "공립",
          "region": "서울",
          ... (implementation-specific extra fields) ...
        }
        If multiple matches are possible the underlying neis_api may return a list.

    Notes
    -----
    - If no match is found, an empty dict or list may be returned.
    - Callers should handle both dict and list for robustness.
    """
    result = neis_get_school_info(school_name)
    return result

@mcp.tool()
def get_school_schedule(school_code: str, org_code: str, from_date: str, to_date: str) -> object:
    """학교 학사 일정 조회 (코드 기반) / Get school schedule by codes

    Parameters
    ----------
    school_code : str
        (KO) NEIS에서 부여한 학교 고유 코드.
        (EN) Unique NEIS school code.
    org_code : str
        (KO) 관할 교육청 코드.
        (EN) Regional education office (org) code.
    from_date : str
        (KO) 조회 시작 날짜 (YYYYMMDD).
        (EN) Start date inclusive, format YYYYMMDD.
    to_date : str
        (KO) 조회 종료 날짜 (YYYYMMDD).
        (EN) End date inclusive, format YYYYMMDD.

    Returns
    -------
    object (dict)
        Example:
        {
          "items": [
            {"date": "20250103", "event": "개학식"},
            {"date": "20250115", "event": "중간고사"}
          ],
          "school_code": "1234567",
          "org_code": "B10",
          "from": "20250101",
          "to": "20250131"
        }

    Notes
    -----
    - If no events exist in range, items may be an empty list.
    - Validate date strings before calling for better error handling.
    """
    result = neis_get_school_schedule(school_code, org_code, from_date, to_date)
    return result

@mcp.tool()
def get_school_schedule_by_name(school_name: str, from_date: str, to_date: str) -> object:
    """학교 학사 일정 조회 (이름 기반) / Get school schedule by school name

    Parameters
    ----------
    school_name : str
        (KO) 조회할 학교 이름.
        (EN) Korean school name to search.
    from_date : str
        (KO) 시작 날짜 (YYYYMMDD).
        (EN) Start date inclusive, format YYYYMMDD.
    to_date : str
        (KO) 종료 날짜 (YYYYMMDD).
        (EN) End date inclusive, format YYYYMMDD.

    Returns
    -------
    object (dict)
        Same structure as get_school_schedule(), but school_code/org_code resolved internally.
        Example:
        {
          "items": [
            {"date": "20250103", "event": "개학식"}
          ],
          "school_name": "서울고등학교",
          "resolved_school_code": "1234567",
          "resolved_org_code": "B10",
          "from": "20250101",
          "to": "20250131"
        }

    Notes
    -----
    - If the name is ambiguous, underlying neis_api may choose the first match or return multiple.
    - For disambiguation, prefer calling get_school_info() first to get exact codes.
    """
    result = neis_get_school_schedule_by_name(school_name, from_date, to_date)
    return result
    
if __name__ == "__main__":
    print("Start MCP server")
    mcp.run(transport="sse")

