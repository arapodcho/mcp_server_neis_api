from mcp.server.fastmcp import FastMCP
mcp = FastMCP("neis_org")

@mcp.tool()
async def get_school_info(school_name:str):
    """학교 이름을 입력으로 정보를 조회합니다.
    arg: 
    
    """
    return f"to find {school_name} with neis api"

if __name__ == "__main__":
    print("Start MCP server")
    mcp.run(transport="sse")