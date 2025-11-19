import pytest
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.sql import func

from app.models.domain_knowledge import DomainKnowledge
from app.core.database import Base


class TestDomainKnowledgeModel:
    """Test cases for DomainKnowledge model"""

    def test_domain_knowledge_inherits_from_base(self):
        """Test that DomainKnowledge inherits from Base"""
        assert issubclass(DomainKnowledge, Base)

    def test_domain_knowledge_table_name(self):
        """Test that DomainKnowledge has the correct table name"""
        assert DomainKnowledge.__tablename__ == 'domain_knowledge'

    def test_domain_knowledge_table_args(self):
        """Test that DomainKnowledge has the correct table args"""
        table_args = DomainKnowledge.__table_args__
        assert isinstance(table_args, tuple)
        # Check that we have constraints and indexes (exact count may vary)
        assert len(table_args) >= 2
        
        # Check indexes
        indexes = [arg for arg in table_args if isinstance(arg, Index)]
        assert len(indexes) >= 2
        
        # Check comment dict
        comment_dict = [arg for arg in table_args if isinstance(arg, dict)]
        assert len(comment_dict) == 1
        assert 'comment' in comment_dict[0]

    def test_domain_knowledge_columns(self):
        """Test that DomainKnowledge has all the expected columns with correct types and properties"""
        columns = DomainKnowledge.__table__.columns
        
        # Check knowledge_id column
        assert 'knowledge_id' in columns
        knowledge_id_col = columns['knowledge_id']
        assert isinstance(knowledge_id_col.type, Integer)
        assert knowledge_id_col.primary_key is True
        assert knowledge_id_col.autoincrement is True
        assert knowledge_id_col.comment == '知识条目ID'

        # Check project_id column
        assert 'project_id' in columns
        project_id_col = columns['project_id']
        assert isinstance(project_id_col.type, Integer)
        assert project_id_col.nullable is False
        assert project_id_col.comment == '所属项目'
        # Check that it has foreign key (without checking specific table)
        assert len(project_id_col.foreign_keys) >= 1

        # Check term column
        assert 'term' in columns
        term_col = columns['term']
        assert isinstance(term_col.type, String)
        assert term_col.nullable is False
        assert term_col.comment == '业务术语'

        # Check definition column
        assert 'definition' in columns
        definition_col = columns['definition']
        assert isinstance(definition_col.type, Text)
        assert definition_col.nullable is False
        assert definition_col.comment == '术语定义'

        # Check examples column
        assert 'examples' in columns
        examples_col = columns['examples']
        assert isinstance(examples_col.type, Text)
        assert examples_col.comment == '使用示例'

        # Check created_at column
        assert 'created_at' in columns
        created_at_col = columns['created_at']
        assert isinstance(created_at_col.type, DateTime)
        assert created_at_col.server_default is not None
        assert created_at_col.comment == '创建时间'
