import os
import json
from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict
from typing import Dict, Any

# 加载环境变量
load_dotenv()

class Config(BaseModel):
    model_config = ConfigDict(extra='ignore')
    
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", 3306))
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_NAME: str = os.getenv("DB_NAME", "")
    TABLE_NAME: str = os.getenv("TABLE_NAME", "")
    EXCEL_FILE_PATH: str = os.getenv("EXCEL_FILE_PATH", "")
    SHEET_NAME: str = os.getenv("SHEET_NAME", "")
    
    mapping: Dict[str, Any] = {}

    def load_mapping(self, file_path: str = None):
        # 优先使用传参，其次环境变量，最后默认值
        target_path = file_path or os.getenv("MAPPING_FILE", "configs/mapping_config.json")
        if os.path.exists(target_path):
            with open(target_path, 'r', encoding='utf-8') as f:
                self.mapping = json.load(f)
            # print(f"加载映射文件: {target_path}")
        else:
            print(f"警告: {target_path} 未找到。")
        return self.mapping

# 单例模式
settings = Config()
settings.load_mapping()

if __name__ == "__main__":
    print("Config loaded:")
    print(f"DB: {settings.DB_HOST}:{settings.DB_PORT}")
    print(f"Excel: {settings.EXCEL_FILE_PATH}")
    print(f"Mapping entries: {len(settings.mapping.get('mapping', {}))}")
