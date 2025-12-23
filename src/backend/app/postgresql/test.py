"""
PostgreSQL 连接测试脚本。

用于验证 asyncio 和 asyncpg 在不同环境下的连接兼容性（仅供开发测试）。
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from config.base import PostgresConfig
from postgresql.postgres_database import PostgresHelper
from postgresql.postgres_execute import deploy_postgres_ddl, execute_dql_user, execute_dml_user
from core.config import config
from service.postgresql_service import create_postgresql_user, grant_user_privileges, ensure_user_and_engine
from models.database_instance import DatabaseInstance


async def ddl_execution():
    """测试DDL执行功能"""
    try:
        # 使用配置文件中的PostgreSQL配置
        postgres_config = config.postgresql

        # 初始化root引擎
        print("初始化PostgreSQL root引擎...")
        await PostgresHelper.init_root_engine(postgres_config)
        print("PostgreSQL root引擎初始化成功!")

        # 测试用的DDL语句
        test_statements = [
            "CREATE TABLE student (student_id VARCHAR(255) UNIQUE NOT NULL, name VARCHAR(255) NOT NULL, age INT NOT NULL CHECK (age > 0), PRIMARY KEY (student_id))",
            "CREATE TABLE course (course_number VARCHAR(255) UNIQUE NOT NULL, course_name VARCHAR(255) NOT NULL, credits INT NOT NULL CHECK (credits > 0), lecturer VARCHAR(255) NOT NULL, class_time VARCHAR(255) NOT NULL, PRIMARY KEY (course_number))",
            "CREATE TABLE student_courses (student_id VARCHAR(255) NOT NULL, course_number VARCHAR(255) NOT NULL, PRIMARY KEY (student_id, course_number), FOREIGN KEY (student_id) REFERENCES student(student_id), FOREIGN KEY (course_number) REFERENCES course(course_number))"
        ]

        print("开始测试PostgreSQL DDL执行...")
        await deploy_postgres_ddl("test_database", test_statements)
        print("DDL执行测试成功完成!")

    except Exception as e:
        print(f"DDL执行测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理资源
        try:
            await PostgresHelper.close_root_engine()
            print("已清理PostgreSQL连接资源")
        except:
            pass


async def service_test():
    """测试PostgreSQL服务功能"""
    try:
        # 使用配置文件中的PostgreSQL配置
        postgres_config = config.postgresql

        # 初始化root引擎
        print("初始化PostgreSQL root引擎...")
        await PostgresHelper.init_root_engine(postgres_config)
        print("PostgreSQL root引擎初始化成功!")

        # 测试创建用户
        test_username = "test_user"
        test_password = "test_password"
        test_db_name = "test_database"

        print(f"开始测试创建用户 {test_username}...")
        await create_postgresql_user(test_username, test_password)
        print(f"用户 {test_username} 创建成功!")

        # 测试授予权限
        print(f"开始测试为用户 {test_username} 授予数据库 {test_db_name} 的权限...")
        await grant_user_privileges(test_db_name, test_username)
        print(f"为用户 {test_username} 授予数据库 {test_db_name} 的权限成功!")

        # 测试确保用户和引擎
        print("开始测试ensure_user_and_engine功能...")
        # 创建一个模拟的DatabaseInstance对象
        instance = DatabaseInstance()
        instance.db_name = test_db_name
        instance.db_username = test_username
        instance.db_password = test_password
        instance.instance_id = 1

        result = await ensure_user_and_engine(test_db_name, test_username, test_password, 1)
        print(f"ensure_user_and_engine测试结果: {result}")
        print("ensure_user_and_engine功能测试完成!")

    except Exception as e:
        print(f"Service功能测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理资源
        try:
            await PostgresHelper.close_root_engine()
            print("已清理PostgreSQL连接资源")
        except:
            pass


async def data_test():
    """测试数据插入和查询功能"""
    try:
        # 使用配置文件中的PostgreSQL配置
        postgres_config = config.postgresql

        # 初始化root引擎
        print("初始化PostgreSQL root引擎...")
        await PostgresHelper.init_root_engine(postgres_config)
        print("PostgreSQL root引擎初始化成功!")

        # 创建DatabaseInstance对象用于测试
        instance = DatabaseInstance()
        instance.db_name = "test_database"
        instance.db_username = "test_user"
        instance.db_password = "test_password"
        instance.instance_id = 10086

        # 确保用户和引擎已准备就绪
        await ensure_user_and_engine(instance.db_name, instance.db_username, instance.db_password, instance.instance_id)

        # 再次确保权限正确
        await PostgresHelper.grant_user_privileges(instance.db_name, instance.db_username)

        # 插入测试数据
        print("开始插入测试数据...")

        # 插入学生数据
        insert_student_sql = """
            INSERT INTO student (student_id, name, age)
            VALUES
                ('S001', '张三', 20),
                ('S002', '李四', 21),
                ('S003', '王五', 19)
        """
        await execute_dml_user(insert_student_sql, instance)
        print("学生数据插入完成!")

        # 插入课程数据
        insert_course_sql = """
            INSERT INTO course (course_number, course_name, credits, lecturer, class_time)
            VALUES
                ('C001', '数学', 4, '张教授', '周一 9:00-11:00'),
                ('C002', '物理', 3, '李教授', '周二 14:00-16:00'),
                ('C003', '化学', 3, '王教授', '周三 10:00-12:00')
        """
        await execute_dml_user(insert_course_sql, instance)
        print("课程数据插入完成!")

        # 插入选课数据
        insert_enrollment_sql = """
            INSERT INTO student_courses (student_id, course_number)
            VALUES
                ('S001', 'C001'),
                ('S001', 'C002'),
                ('S002', 'C001'),
                ('S003', 'C003')
        """
        await execute_dml_user(insert_enrollment_sql, instance)
        print("选课数据插入完成!")

        # 测试查询功能
        print("开始测试查询功能...")

        # 查询所有学生
        select_students_sql = "SELECT * FROM student"
        students_result = await execute_dql_user(select_students_sql, instance)
        print("所有学生数据:")
        for student in students_result:
            print(f"  学号: {student['student_id']}, 姓名: {student['name']}, 年龄: {student['age']}")

        # 查询所有课程
        select_courses_sql = "SELECT * FROM course"
        courses_result = await execute_dql_user(select_courses_sql, instance)
        print("所有课程数据:")
        for course in courses_result:
            print(f"  课程号: {course['course_number']}, 课程名: {course['course_name']}, 学分: {course['credits']}, 教师: {course['lecturer']}, 时间: {course['class_time']}")

        # 查询选课情况
        select_enrollments_sql = "SELECT * FROM student_courses"
        enrollments_result = await execute_dql_user(select_enrollments_sql, instance)
        print("选课数据:")
        for enrollment in enrollments_result:
            print(f"  学号: {enrollment['student_id']}, 课程号: {enrollment['course_number']}")

        # 复杂查询：查询学生及其选课信息
        complex_query_sql = """
            SELECT s.name AS student_name, c.course_name, c.credits, c.lecturer
            FROM student s
            JOIN student_courses sc ON s.student_id = sc.student_id
            JOIN course c ON sc.course_number = c.course_number
            ORDER BY s.name, c.course_name
        """
        complex_result = await execute_dql_user(complex_query_sql, instance)
        print("学生选课详情:")
        for record in complex_result:
            print(f"  学生: {record['student_name']}, 课程: {record['course_name']}, 学分: {record['credits']}, 教师: {record['lecturer']}")

        print("数据查询测试完成!")

    except Exception as e:
        print(f"数据测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理资源
        try:
            await PostgresHelper.close_root_engine()
            print("已清理PostgreSQL连接资源")
        except:
            pass


async def main():
    """主测试函数"""
    print("=" * 50)
    print("开始PostgreSQL DDL执行测试")
    print("=" * 50)
    await ddl_execution()

    print("\n" + "=" * 50)
    print("开始PostgreSQL Service功能测试")
    print("=" * 50)
    await service_test()

    print("\n" + "=" * 50)
    print("开始PostgreSQL 数据操作测试")
    print("=" * 50)
    await data_test()


async def clean_user():
    postgres_config = config.postgresql
    # 初始化root引擎
    print("初始化PostgreSQL root引擎...")
    await PostgresHelper.init_root_engine(postgres_config)
    print("PostgreSQL root引擎初始化成功!")

    # 先尝试删除用户（忽略错误）
    try:
        await PostgresHelper.drop_postgresql_user("test_database", "test_user")
    except Exception as e:
        print(f"清理用户时出错（可忽略）: {e}")
    
    # 关闭引擎
    await PostgresHelper.close_root_engine()


if __name__ == "__main__":
    # 先清理旧的用户和数据库
    asyncio.run(clean_user())
    
    # 然后运行主测试
    asyncio.run(main())
    # asyncio.run(clean_user())
