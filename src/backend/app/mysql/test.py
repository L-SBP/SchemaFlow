"""
MySQL 连接测试脚本。

用于验证 asyncio 和 aiomysql 在不同环境下的连接兼容性（仅供开发测试）。
"""

# backend/app/mysql/test.py

# import asyncio
# import sys
# import aiomysql
#
# async def test_aiomysql_direct():
#     # 强制切换 Windows 事件循环
#     if sys.platform == 'win32':
#         asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
#
#     # 直接用 aiomysql 连接
#     conn = await aiomysql.connect(
#         host='127.0.0.1',
#         port=3306,
#         user='root',
#         password='root_secure_2025',
#         db='mysql',
#         auth_plugin='mysql_native_password',
#         ssl=False  # 明确禁用 SSL
#     )
#
#     # 执行查询
#     async with conn.cursor() as cur:
#         await cur.execute("SHOW GRANTS;")
#         grants = await cur.fetchall()
#         print("=== Root 用户权限 ===")
#         for g in grants:
#             print(g[0])
#
#     # 关闭连接
#     conn.close()
#     await conn.wait_closed()
#     print("\n=== 连接已关闭 ===")
#
# if __name__ == "__main__":
#     asyncio.run(test_aiomysql_direct())