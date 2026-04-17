import pandas as pd
from core.config import settings
import os

class ExcelExtractor:
    def __init__(self, file_path: str = None, sheet_name: str = None):
        self.file_path = file_path or settings.EXCEL_FILE_PATH
        self.sheet_name = sheet_name or settings.SHEET_NAME

    def fetch_raw_data(self):
        """
        读取 Excel 文件并返回原始 DataFrame
        """
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"Excel 文件未找到: {self.file_path}")
            
        print(f"正在读取 Excel: {self.file_path} (工作表: {self.sheet_name})")
        # 读取时不指定 header，以便后续自定义处理
        df = pd.read_excel(self.file_path, sheet_name=self.sheet_name, header=None)
        return df

if __name__ == "__main__":
    try:
        extractor = ExcelExtractor()
        df = extractor.fetch_raw_data()
        print(f"数据读取成功，共 {len(df)} 行，{len(df.columns)} 列")
        print("\n前 5 行预览:")
        print(df.head())
    except Exception as e:
        print(f"提取失败: {e}")
