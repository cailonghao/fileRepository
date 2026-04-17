import pandas as pd
from sqlalchemy import text
from core.config import settings
from core.loader import Loader
import os
import sys
import os


def sync_daily(csv_file: str = None):
    print("========================================")
    print("开始执行每日数据条件同步 (空表校验模式)")
    print("========================================")

    # 1. 加载映射配置 (针对每日数据表)
    mapping_file = "configs/mapping_config_day.json"
    if not os.path.exists(mapping_file):
        msg = f"错误: 找不到映射文件 {mapping_file}"
        print(msg)
        return {"status": "error", "message": msg}
        
    settings.load_mapping(mapping_file)
    mapping_data = settings.mapping
    target_table = mapping_data.get("table_name", "crm_kpi_shop_emp_day")
    
    # 2. 初始化 Loader 并设置目标表
    loader = Loader()
    loader.table_name = target_table # 动态覆盖为每日表名
    
    try:
        # 3. 检查表是否为空
        print(f"正在检查目标表 {target_table} 是否为空...")
        with loader.engine.connect() as conn:
            result = conn.execute(text(f"SELECT COUNT(*) FROM `{target_table}`"))
            count = result.scalar()
            
        if count > 0:
            msg = f"警告: 目标表 `{target_table}` 非空 (当前记录数: {count})。跳过本次同步任务。"
            print(msg)
            return {"status": "warning", "message": msg, "count": count}
            
        print(f"确认表 `{target_table}` 为空，准备开始同步。")
        
        # 4. 读取 CSV
        input_csv = csv_file or "resources/daily_targets_2026.csv"
        if not os.path.exists(input_csv):
            msg = f"错误: 找不到数据文件 {input_csv}"
            print(msg)
            return {"status": "error", "message": msg}
            
        print(f"正在从 {input_csv} 读取数据...")
        # 显式指定编码，防止 Windows 环境下乱码
        df = pd.read_csv(input_csv, encoding="utf-8-sig")

        
        # 5. 执行入库
        loader.load_data(df)
        
        msg = "同步成功完成！"
        print("========================================")
        print(msg)
        print("========================================")
        return {"status": "success", "message": msg, "records_loaded": len(df)}

    except Exception as e:
        import traceback
        traceback.print_exc()
        msg = f"同步过程中发生错误: {e}"
        print(msg)
        return {"status": "error", "message": msg}

if __name__ == "__main__":
    sync_daily()

