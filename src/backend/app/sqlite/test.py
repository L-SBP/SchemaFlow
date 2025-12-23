"""
SQLite 连接测试脚本。

用于验证 SQLite 在不同环境下的连接兼容性（仅供开发测试）。
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from config.base import SQLiteConfig
from sqlite.sqlite_database import SQLiteHelper
from sqlite.sqlite_execute import deploy_sqlite_ddl, execute_dql_user, execute_dml_user
from core.config import config
from models.database_instance import DatabaseInstance


async def ddl_execution():
    """测试DDL执行功能"""
    try:
        # 使用配置文件中的SQLite配置
        sqlite_config = config.sqlite

        # 测试用的DDL语句
        test_statements = [
            "CREATE TABLE student (student_id TEXT UNIQUE NOT NULL, name TEXT NOT NULL, age INTEGER NOT NULL CHECK (age > 0), PRIMARY KEY (student_id))",
            "CREATE TABLE course (course_number TEXT UNIQUE NOT NULL, course_name TEXT NOT NULL, credits INTEGER NOT NULL CHECK (credits > 0), lecturer TEXT NOT NULL, class_time TEXT NOT NULL, PRIMARY KEY (course_number))",
            "CREATE TABLE student_courses (student_id TEXT NOT NULL, course_number TEXT NOT NULL, PRIMARY KEY (student_id, course_number), FOREIGN KEY (student_id) REFERENCES student(student_id), FOREIGN KEY (course_number) REFERENCES course(course_number))"
        ]

        print("开始测试SQLite DDL执行...")
        await deploy_sqlite_ddl("test_database", test_statements, sqlite_config, user_id=10086)
        print("DDL执行测试成功完成!")

    except Exception as e:
        print(f"DDL执行测试失败: {e}")
        import traceback
        traceback.print_exc()


async def data_test():
    """测试数据插入和查询功能"""
    try:
        # 使用配置文件中的SQLite配置
        sqlite_config = config.sqlite

        # 创建DatabaseInstance对象用于测试
        instance = DatabaseInstance()
        instance.db_name = "test_database"
        instance.db_username = "test_user"  # SQLite不需要用户名密码，但为了兼容性保留
        instance.db_password = "test_password"
        instance.instance_id = 10086

        # 初始化引擎，使用用户ID进行隔离
        print("初始化SQLite引擎...")
        await SQLiteHelper.init_user_engine(sqlite_config, instance.instance_id, instance.db_name, user_id=10086)
        print("SQLite引擎初始化成功!")

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
            instance = DatabaseInstance()
            instance.instance_id = 10086
            await SQLiteHelper.close_user_engine(instance)
            print("已清理SQLite连接资源")
        except:
            pass


async def main():
    """主测试函数"""
    print("=" * 50)
    print("开始SQLite DDL执行测试")
    print("=" * 50)
    await ddl_execution()

    print("\n" + "=" * 50)
    print("开始SQLite 数据操作测试")
    print("=" * 50)
    await data_test()


if __name__ == "__main__":
    asyncio.run(main())