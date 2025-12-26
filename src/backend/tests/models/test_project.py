import pytest
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import JSONB

from app.models.project import Project
from app.core.database import Base


class TestProjectModel:
    """Test cases for Project model"""

    def test_project_inherits_from_base(self):
        """Test that Project inherits from Base"""
        assert issubclass(Project, Base)

    def test_project_table_name(self):
        """Test that Project has the correct table name"""
        assert Project.__tablename__ == 'project'

    def test_project_table_args(self):
        """Test that Project has the correct table args"""
        table_args = Project.__table_args__
        assert isinstance(table_args, tuple)
        # Check that we have constraints and indexes (exact count may vary)
        assert len(table_args) >= 3
        
        # Check constraints
        constraints = [arg for arg in table_args if isinstance(arg, CheckConstraint)]
        assert len(constraints) >= 1
        
        # Check indexes
        indexes = [arg for arg in table_args if isinstance(arg, Index)]
        assert len(indexes) >= 3
        
        # Check comment dict
        comment_dict = [arg for arg in table_args if isinstance(arg, dict)]
        assert len(comment_dict) == 1
        assert 'comment' in comment_dict[0]

    def test_project_columns(self):
        """Test that Project has all the expected columns with correct types and properties"""
        columns = Project.__table__.columns
        
        # Check project_id column
        assert 'project_id' in columns
        project_id_col = columns['project_id']
        assert isinstance(project_id_col.type, Integer)
        assert project_id_col.primary_key is True
        assert project_id_col.autoincrement is True
        assert project_id_col.comment == '项目ID'

        # Check user_id column
        assert 'user_id' in columns
        user_id_col = columns['user_id']
        assert isinstance(user_id_col.type, Integer)
        assert user_id_col.nullable is False
        assert user_id_col.comment == '所属用户'
        # Check that it has foreign key (without checking specific table)
        assert len(user_id_col.foreign_keys) >= 1

        # Check instance_id column
        assert 'instance_id' in columns
        instance_id_col = columns['instance_id']
        assert isinstance(instance_id_col.type, Integer)
        assert instance_id_col.nullable is False
        assert instance_id_col.comment == '关联的数据库实例'
        # Check that it has foreign key (without checking specific table)
        assert len(instance_id_col.foreign_keys) >= 1

        # Check project_name column
        assert 'project_name' in columns
        project_name_col = columns['project_name']
        assert isinstance(project_name_col.type, String)
        assert project_name_col.nullable is False
        assert project_name_col.comment == '项目名称，如"我的服装店"'

        # Check description column
        assert 'description' in columns
        description_col = columns['description']
        assert isinstance(description_col.type, Text)
        assert description_col.comment == '业务需求描述'

        # Check schema_definition column
        assert 'schema_definition' in columns
        schema_definition_col = columns['schema_definition']
        assert isinstance(schema_definition_col.type, JSONB)
        assert schema_definition_col.comment == 'AI生成的DDL结构（表、字段、约束等）'

        # Check project_status column
        assert 'project_status' in columns
        project_status_col = columns['project_status']
        assert isinstance(project_status_col.type, Text)
        assert project_status_col.default.arg == 'active'
        assert project_status_col.nullable is False
        assert project_status_col.comment == '项目状态'

        # Check created_at column
        assert 'created_at' in columns
        created_at_col = columns['created_at']
        assert isinstance(created_at_col.type, DateTime)
        assert created_at_col.server_default is not None
        assert created_at_col.comment == '创建时间'

        # Check updated_at column
        assert 'updated_at' in columns
        updated_at_col = columns['updated_at']
        assert isinstance(updated_at_col.type, DateTime)
        assert updated_at_col.server_default is not None
        assert updated_at_col.onupdate is not None
        assert updated_at_col.comment == '最后更新时间'