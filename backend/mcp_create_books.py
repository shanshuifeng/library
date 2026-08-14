"""
通过 MCP Client 创建示例图书
"""
import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


server_params = StdioServerParameters(
    command="python",
    args=["mcp_server.py"],
    cwd="D:\\PyCharmProject\\book-manager\\backend"
)

# 示例图书数据（新书，不与已有数据重复）
BOOKS = [
    # 科幻
    {"title": "基地", "author": "艾萨克·阿西莫夫", "isbn": "9787544270601", "publisher": "南海出版公司", "price": 59.00, "stock": 6, "location": "A区-1楼-04架"},
    {"title": "沙丘", "author": "弗兰克·赫伯特", "isbn": "9787544291163", "publisher": "南海出版公司", "price": 68.00, "stock": 5, "location": "A区-1楼-04架"},
    {"title": "银河帝国：基地", "author": "艾萨克·阿西莫夫", "isbn": "9787544259354", "publisher": "江苏文艺出版社", "price": 45.00, "stock": 8, "location": "A区-1楼-05架"},

    # 计算机进阶
    {"title": "深入理解计算机系统", "author": "Randal E. Bryant", "isbn": "9787111544937", "publisher": "机械工业出版社", "price": 139.00, "stock": 4, "location": "B区-2楼-06架"},
    {"title": "算法（第4版）", "author": "Robert Sedgewick", "isbn": "9787115360625", "publisher": "人民邮电出版社", "price": 99.00, "stock": 7, "location": "B区-2楼-06架"},
    {"title": "设计模式", "author": "Erich Gamma", "isbn": "9787111618331", "publisher": "机械工业出版社", "price": 69.00, "stock": 5, "location": "B区-2楼-07架"},

    # 人文
    {"title": "枪炮、病菌与钢铁", "author": "贾雷德·戴蒙德", "isbn": "9787108009822", "publisher": "上海译文出版社", "price": 55.00, "stock": 6, "location": "C区-2楼-01架"},
    {"title": "思考，快与慢", "author": "丹尼尔·卡尼曼", "isbn": "9787508633558", "publisher": "中信出版社", "price": 69.00, "stock": 8, "location": "C区-2楼-02架"},
    {"title": "原则", "author": "瑞·达利欧", "isbn": "9787508684031", "publisher": "中信出版社", "price": 88.00, "stock": 5, "location": "C区-2楼-02架"},

    # 自然科学
    {"title": "时间简史", "author": "史蒂芬·霍金", "isbn": "9787535732309", "publisher": "湖南科学技术出版社", "price": 45.00, "stock": 10, "location": "D区-1楼-01架"},
    {"title": "自私的基因", "author": "理查德·道金斯", "isbn": "9787108005618", "publisher": "中信出版社", "price": 48.00, "stock": 6, "location": "D区-1楼-01架"},
]


async def create_books():
    """通过 MCP 创建图书"""
    print("=" * 60)
    print("通过 MCP Client 创建示例图书")
    print("=" * 60)

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("\n[MCP] 连接成功!")

            # 登录获取 token
            print("\n[1] 登录获取 Token...")
            result = await session.call_tool("login", arguments={
                "username": "admin",
                "password": "admin123"
            })
            login_data = json.loads(result.content[0].text)

            if login_data.get("code") != 200:
                print(f"[ERROR] 登录失败: {login_data.get('message')}")
                return

            token = login_data["data"]["access_token"]
            print("[OK] Token 获取成功!")

            # 创建图书
            print(f"\n[2] 开始创建 {len(BOOKS)} 本图书...")
            success_count = 0
            skip_count = 0
            error_count = 0

            for i, book in enumerate(BOOKS, 1):
                print(f"\n  [{i}/{len(BOOKS)}] {book['title']}")

                result = await session.call_tool("create_book", arguments={
                    "token": token,
                    "title": book["title"],
                    "author": book["author"],
                    "isbn": book["isbn"],
                    "publisher": book["publisher"],
                    "price": book["price"],
                    "stock": book["stock"],
                    "location": book["location"]
                })

                book_result = json.loads(result.content[0].text)

                if book_result.get("code") == 201:
                    print(f"    [OK] 创建成功!")
                    success_count += 1
                elif book_result.get("code") == 400 and "已存在" in book_result.get("message", ""):
                    print(f"    [SKIP] 图书已存在")
                    skip_count += 1
                else:
                    print(f"    [ERROR] {book_result.get('message')}")
                    error_count += 1

            # 统计结果
            print("\n" + "=" * 60)
            print("创建完成!")
            print(f"  成功: {success_count}")
            print(f"  跳过: {skip_count}")
            print(f"  失败: {error_count}")
            print(f"  总计: {len(BOOKS)}")
            print("=" * 60)


if __name__ == "__main__":
    asyncio.run(create_books())
