"""
MCP Client 测试脚本
用于验证 MCP Server 是否正常工作
"""
import asyncio
import json
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

_TEST_PWD = os.environ.get('TEST_PASSWORD', 'admin123')
_WRONG_PWD = os.environ.get('TEST_WRONG_PASSWORD', 'wrong_password')
_REG_PWD = os.environ.get('TEST_REG_PASSWORD', 'test123456')


# MCP Server 配置
server_params = StdioServerParameters(
    command="python",
    args=["mcp_server.py"],
    cwd="D:\\PyCharmProject\\book-manager\\backend"
)


async def test_mcp_server():
    """测试 MCP Server"""
    print("=" * 60)
    print("大学图书管理系统 - MCP Server 测试")
    print("=" * 60)

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # 初始化连接
            await session.initialize()
            print("\n[1] 连接成功!")

            # 列出所有工具
            tools = await session.list_tools()
            print(f"\n[2] 可用工具数量: {len(tools.tools)}")
            print("\n工具列表:")
            for i, tool in enumerate(tools.tools, 1):
                print(f"  {i:2d}. {tool.name}")

            # 测试登录
            print("\n" + "=" * 60)
            print("[3] 测试登录接口")
            print("=" * 60)
            result = await session.call_tool("login", arguments={
                "username": "admin",
                "password": _TEST_PWD
            })
            print(f"登录结果: {result.content[0].text[:200]}...")

            # 解析 token
            login_data = json.loads(result.content[0].text)
            if login_data.get("code") == 200:
                token = login_data["data"]["access_token"]
                print(f"\n获取 Token 成功!")

                # 测试获取个人信息
                print("\n" + "=" * 60)
                print("[4] 测试获取个人信息")
                print("=" * 60)
                result = await session.call_tool("get_profile", arguments={
                    "token": token
                })
                print(f"个人信息: {result.content[0].text[:200]}...")

                # 测试获取图书列表
                print("\n" + "=" * 60)
                print("[5] 测试获取图书列表")
                print("=" * 60)
                result = await session.call_tool("get_books", arguments={
                    "token": token,
                    "page": 1,
                    "per_page": 5
                })
                print(f"图书列表: {result.content[0].text[:200]}...")

                # 测试获取分类
                print("\n" + "=" * 60)
                print("[6] 测试获取分类树")
                print("=" * 60)
                result = await session.call_tool("get_categories", arguments={
                    "token": token
                })
                print(f"分类树: {result.content[0].text[:200]}...")

                # 测试系统概览
                print("\n" + "=" * 60)
                print("[7] 测试系统概览")
                print("=" * 60)
                result = await session.call_tool("get_overview", arguments={
                    "token": token
                })
                print(f"系统概览: {result.content[0].text[:200]}...")

                # 测试借阅记录
                print("\n" + "=" * 60)
                print("[8] 测试借阅记录")
                print("=" * 60)
                result = await session.call_tool("get_borrow_list", arguments={
                    "token": token,
                    "page": 1,
                    "per_page": 5
                })
                print(f"借阅记录: {result.content[0].text[:200]}...")

            else:
                print(f"\n登录失败: {login_data.get('message')}")

            print("\n" + "=" * 60)
            print("测试完成!")
            print("=" * 60)


async def test_without_token():
    """测试不需要 token 的接口"""
    print("\n" + "=" * 60)
    print("测试公开接口（不需要 Token）")
    print("=" * 60)

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 测试登录（不需要 token）
            print("\n[1] 测试登录（不需要 Token）")
            result = await session.call_tool("login", arguments={
                "username": "admin",
                "password": _WRONG_PWD
            })
            print(f"登录结果: {result.content[0].text[:200]}...")

            # 测试注册（不需要 token）
            print("\n[2] 测试注册（不需要 Token）")
            result = await session.call_tool("register", arguments={
                "username": "test_user",
                "password": _REG_PWD
            })
            print(f"注册结果: {result.content[0].text[:200]}...")


async def main():
    """主函数"""
    try:
        # 测试公开接口
        await test_without_token()

        # 测试完整流程
        await test_mcp_server()

    except Exception as e:
        print(f"\n测试出错: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
