from pathlib import Path
import tempfile
import os

from app.utils.profile import Profile

class TestProfile:
    """Test cases for Profile utility class"""

    def test_get_project_root(self):
        """Test that get_project_root returns a Path object pointing to the project root"""
        project_root = Profile.get_project_root()
        assert isinstance(project_root, Path)
        # Check that we can find key project files
        assert (project_root / "app").exists()
        assert (project_root / "config.yaml").exists()

    def test_get_project_root_fallback(self, tmp_path, monkeypatch):
        """Test get_project_root fallback mechanism"""
        # Create a temporary directory structure
        temp_project = tmp_path / "project"
        temp_project.mkdir()
        
        # Create the config file
        config_file = temp_project / "config.yaml"
        config_file.write_text("test: config")
        
        # Create nested directories
        deep_path = temp_project / "a" / "b" / "c"
        deep_path.mkdir(parents=True)
        
        # Mock the __file__ attribute to simulate being in the deep path
        mock_file_path = deep_path / "mock_file.py"
        
        # Temporarily patch the __file__ attribute in Profile module
        monkeypatch.setattr("app.utils.profile.__file__", str(mock_file_path))
        
        # Now import Profile after patching
        from app.utils.profile import Profile
        
        # Test that we can find the project root
        project_root = Profile.get_project_root()
        assert project_root == temp_project