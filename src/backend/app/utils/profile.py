from pathlib import Path

class Profile:
    @staticmethod
    def get_project_root() -> Path:
        """
        获取项目根目录

        :return: 项目根目录
        """
        # More robust way to find project root by looking for key files/directories
        current_path = Path(__file__)
        
        # Traverse up until we find the backend directory (which contains config.yaml)
        for parent in current_path.parents:
            if (parent / "config.yaml").exists():
                return parent
        
        # Fallback - navigate up a fixed number of levels
        # This maintains backward compatibility
        return current_path.parent.parent.parent