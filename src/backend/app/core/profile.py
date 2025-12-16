# backend/app/core/profile.py

from pathlib import Path

class Profile:
    """
    项目配置辅助类。
    
    用于获取项目相关的路径信息。
    """
    @staticmethod
    def get_project_root() -> Path:
        """
        获取项目根目录。

        通过向上查找 config.yaml 文件来确定项目根目录。
        如果未找到，则回退到基于当前文件位置的相对路径。

        Returns:
            Path: 项目根目录路径。
        """
        current_path = Path(__file__)
        
        for parent in current_path.parents:
            if (parent / "config.yaml").exists():
                return parent
        
        return current_path.parent.parent.parent
