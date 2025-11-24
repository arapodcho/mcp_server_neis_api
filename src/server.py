from mcp.server.fastmcp import FastMCP
from neis_api import neis_get_school_info, neis_get_school_schedule, neis_get_school_schedule_by_name

mcp = FastMCP("neis_org")

@mcp.tool()
def get_school_info(school_name:str)->dict:
    """학교 이름을 입력으로 정보를 조회합니다."""
    result = neis_get_school_info(school_name)
    return result

@mcp.tool()
def get_school_schedule(school_code:str, org_code:str, from_date:str, to_date:str)->dict:
    """학교 코드와 교육청 코드를 입력으로 일정을 조회합니다."""
    result = neis_get_school_schedule(school_code, org_code, from_date, to_date)
    return result

@mcp.tool()
def get_school_schedule_by_name(school_name:str, from_date:str, to_date:str, grade:list=[1,2,3], target_org=None)->dict:
    """학교 이름을 입력으로 일정을 조회합니다.(일정: YYYYMMDD)"""
    result = neis_get_school_schedule_by_name(school_name, from_date, to_date, grade, target_org)
    return result
    
if __name__ == "__main__":
    print("Start MCP server")
    mcp.run(transport="sse")

