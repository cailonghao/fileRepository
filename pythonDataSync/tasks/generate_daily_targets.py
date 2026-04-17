import pandas as pd
import calendar
import math
import os
import sys
from datetime import date
from core.loader import Loader
from core.config import settings

def generate_daily_targets(excel_file: str = None, output_csv: str = None):
    print("========================================")
    print("开始生成销区经理每日业绩目标")
    print("========================================")
    
    try:
        # 1. 加载员工 ID 映射 (复用 loader 模块)
        loader = Loader()
        emp_map = loader.get_employee_mapping()
        
        # 2. 读取 Excel (Sheet 1)
        file_path = excel_file or settings.EXCEL_FILE_PATH
        sheet_index = 1 
        print(f"读取 Excel 文件: {file_path}")
        
        # 读取原始数据
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_index, header=None)
        except Exception as e:
            msg = f"读取 Excel 失败: {e}"
            print(msg)
            return {"status": "error", "message": msg}
        
        # 经理数据从索引 4 开始 (第 5 行)
        # 列 1: 经理姓名
        # 列 2-13: 1月到12月的月度目标 (单位: 万元)
        manager_data = df.iloc[4:]
        
        all_daily_records = []
        year = 2026
        
        print("正在计算每日目标...")
        for _, row in manager_data.iterrows():
            if len(row) < 2: continue
            manager_name = str(row[1]).strip()
            
            # 跳过空行或无效名称
            if pd.isna(row[1]) or manager_name in ["", "nan", "None"]:
                continue
            
            # 过滤显式的汇总项
            if "总计" in manager_name or "全公司" in manager_name:
                print(f"跳过汇总项: {manager_name}")
                continue
            
            # 过滤纯数字 (通常是底部统计值)
            if manager_name.replace('.', '', 1).isdigit():
                print(f"跳过指标值: {manager_name}")
                continue
                
            manager_id = emp_map.get(manager_name)
            
            for month in range(1, 13):
                # 列索引: 2(1月), 3(2月), ..., 13(12月)
                col_idx = month + 1
                if col_idx >= len(row): break
                month_target_raw = row[col_idx]
                
                # 尝试转换为数字，失败则设为 0
                try:
                    month_target = float(month_target_raw) if pd.notna(month_target_raw) else 0
                except (ValueError, TypeError):
                    # 如果是带引号的数字或其他字符串，尝试清理
                    cleaned_val = pd.to_numeric(month_target_raw, errors='coerce')
                    month_target = float(cleaned_val) if pd.notna(cleaned_val) else 0
                
                days = calendar.monthrange(year, month)[1]
                # 精准分配算法 (向下取整分摊 + 末日补差)
                total_yuan = round(month_target * 10000, 2)
                
                # 计算前 N-1 天的每日基础均摊 (向下取整到分)
                daily_yuan_base = math.floor((total_yuan / days) * 100) / 100.0
                # 第 N 天 (最后一天) 补齐差额
                last_day_yuan = round(total_yuan - (daily_yuan_base * (days - 1)), 2)
                
                # 生成该月每一天的记录
                for day in range(1, days + 1):
                    current_date = date(year, month, day)
                    target_of_day = daily_yuan_base if day < days else last_day_yuan
                    
                    all_daily_records.append({
                        "销区经理": manager_name,
                        "经理ID": manager_id,
                        "日期": current_date.strftime("%Y-%m-%d"),
                        "月度总目标(元)": total_yuan,
                        "当日目标(元)": target_of_day,
                        "当日目标(万元)": round(target_of_day / 10000, 6)
                    })
        
        # 导出 CSV
        output_file = output_csv or "resources/daily_targets_2026.csv"
        # 确保目录存在
        if os.path.dirname(output_file):
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        result_df = pd.DataFrame(all_daily_records)
        result_df.to_csv(output_file, index=False, encoding="utf-8-sig")
        
        msg = f"生成成功！输出文件: {output_file}, 总记录数: {len(result_df)}"
        print("========================================")
        print(msg)
        print("========================================")
        return {"status": "success", "message": msg, "total_records": len(result_df), "output_file": output_file}

    except Exception as e:
        import traceback
        traceback.print_exc()
        msg = f"生成失败: {e}"
        print(msg)
        return {"status": "error", "message": msg}

if __name__ == "__main__":
    generate_daily_targets()
