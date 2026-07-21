from setuptools import setup, find_packages

setup(
    name="SchemaFlow",          # 项目名称（自定义）
    version="1.0.0",            # 版本号（自定义）
    packages=find_packages(where="app"),  # 从 app 目录查找所有包
    package_dir={"": "app"},
)