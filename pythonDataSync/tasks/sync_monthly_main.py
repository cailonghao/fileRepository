import sys
from core.extractor import ExcelExtractor
from core.transformer import Transformer
from core.loader import Loader
from core.config import settings
import time

import os
import pandas as pd

def sync_monthly(excel_file: str = None, output_csv: str = None):
    start_time = time.time()
    result = {"status": "success", "message": "", "duration": 0}
    
    print("========================================")
    print("开始 Python 模块化 Excel 数据同步任务")
    print("========================================")

    try:
        # 1. 数据提取
        extractor = ExcelExtractor(file_path=excel_file)
        raw_df = extractor.fetch_raw_data()
        
        # 2. 数据转换
        transformer = Transformer()
        transformed_df = transformer.transform(raw_df)
        
        # 3. 处理输出
        if output_csv:
            # 确保目录存在
            os.makedirs(os.path.dirname(output_csv), exist_ok=True) if os.path.dirname(output_csv) else None
            transformed_df.to_csv(output_csv, index=False, encoding="utf-8-sig")
            msg = f"已生成 CSV 文件: {output_csv}"
            print(msg)
            return {"status": "success", "message": msg, "total_records": len(transformed_df)}
        else:
            # 执行原有的入库逻辑
            loader = Loader()
            loader.load_data(transformed_df)
            
            end_time = time.time()
            duration = end_time - start_time
            result["duration"] = round(duration, 2)
            result["message"] = f"同步圆满完成！耗时: {duration:.2f} 秒"
            
            print("========================================")
            print(result["message"])
            print("========================================")
            return result

    except FileNotFoundError as e:
        msg = f"错误: {e}"
        print(msg)
        return {"status": "error", "message": msg}
    except Exception as e:
        import traceback
        traceback.print_exc()
        msg = f"发生意外错误: {e}"
        print(msg)
        return {"status": "error", "message": msg}

def sync_monthly_from_csv(csv_path: str):
    """
    专门用于从已生成的 CSV 文件同步到数据库
    """
    print(f"正在从 CSV 同步月度 KPI 数据: {csv_path}")
    if not os.path.exists(csv_path):
        return {"status": "error", "message": f"找不到文件: {csv_path}"}
        
    try:
        df = pd.read_csv(csv_path, encoding="utf-8-sig")
        loader = Loader()
        loader.load_data(df)
        return {"status": "success", "message": "CSV 数据同步成功", "records_loaded": len(df)}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    sync_monthly()



