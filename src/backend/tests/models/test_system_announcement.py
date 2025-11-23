import pytest
from sqlalchemy import Column, Text, String, Integer, Index, CheckConstraint, ForeignKey, DateTime
from sqlalchemy.sql import func
from app.models.system_announcement import SystemAnnouncement
from app.core.database import Base

class TestSystemAnnouncementModel:
    """Test cases for SystemAnnouncement model"""

    def test_system_announcement_inherits_from_base(self):
        """Test that SystemAnnouncement inherits from Base"""
        assert issubclass(SystemAnnouncement, Base)

    def test_system_announcement_table_name(self):
        """Test that SystemAnnouncement has the correct table name"""
        assert SystemAnnouncement.__tablename__ == 'system_announcement'

    def test_system_announcement_table_args(self):
        """Test that SystemAnnouncement has the correct table args"""
        table_args = SystemAnnouncement.__table_args__
        assert isinstance(table_args, tuple)
        # Check that we have constraints and indexes (exact count may vary)
        assert len(table_args) >= 3
        
        # Check constraints
        constraints = [arg for arg in table_args if isinstance(arg, CheckConstraint)]
        assert len(constraints) >= 1
        
        # Check indexes
        indexes = [arg for arg in table_args if isinstance(arg, Index)]
        assert len(indexes) >= 1
        
        # Check comment dict
        comment_dict = [arg for arg in table_args if isinstance(arg, dict)]
        assert len(comment_dict) == 1
        assert 'comment' in comment_dict[0]

    def test_system_announcement_columns(self):
        """Test that SystemAnnouncement has all the expected columns with correct types and properties"""
        columns = SystemAnnouncement.__table__.columns

        # Check announcement_id column
        assert 'announcement_id' in columns
        announcement_id_col = columns['announcement_id']
        assert isinstance(announcement_id_col.type, Integer)
        assert announcement_id_col.autoincrement is True
        assert announcement_id_col.primary_key is True
        assert announcement_id_col.comment == '公告唯一ID'

        # Check title column
        assert 'title' in columns
        title_col = columns['title']
        assert isinstance(title_col.type, String)
        assert title_col.nullable is False
        assert title_col.comment == '公告标题'

        # Check content column
        assert 'content' in columns
        content_col = columns['content']
        assert isinstance(content_col.type, Text)
        assert content_col.nullable is False
        assert content_col.comment == '公告内容'

        # Check status column
        assert 'status' in columns
        status_col = columns['status']
        assert isinstance(status_col.type, String)
        assert status_col.default.arg == 'draft'
        assert status_col.nullable is False
        assert status_col.comment == '公告状态：draft(草稿)、published(已发布)、unpublished(已下架)、expired(已过期)'

        # Check created_by column
        assert 'created_by' in columns
        created_by_col = columns['created_by']
        assert isinstance(created_by_col.type, Integer)
        assert created_by_col.nullable is False
        assert created_by_col.comment == '创建人（管理员user_id）'
        # Check that it has foreign key (without checking specific table)
        assert len(created_by_col.foreign_keys) >= 1

        # Check created_at column
        assert 'created_at' in columns
        created_at_col = columns['created_at']
        assert isinstance(created_at_col.type, DateTime)
        assert created_at_col.server_default is not None
        assert created_at_col.comment == '公告发布时间'

        # Check updated_at column
        assert 'updated_at' in columns
        updated_at_col = columns['updated_at']
        assert isinstance(updated_at_col.type, DateTime)
        assert updated_at_col.server_default is not None
        assert updated_at_col.onupdate is not None
        assert updated_at_col.nullable is True
        assert updated_at_col.comment == '最后更新时间'
