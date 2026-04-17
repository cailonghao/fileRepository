import pandas as pd
from core.config import settings

class Transformer:
    def __init__(self):
        self.mapping = settings.mapping.get('mapping', {})
        self.fixed_values = settings.mapping.get('fixed_values', {})

    def transform(self, df: pd.DataFrame):
        """
        执行行转列变换逻辑
        """
        print("正在进行数据转化及行转列处理...")
        
        # 原始逻辑参考: ratioRow = rawData[3], data rows start from 4
        # pandas 读取时无 header，索引对齐
        ratio_row = df.iloc[3]
        data_rows = df.iloc[4:]
        
        month_start_col = 19
        col_step = 9
        records = []

        for _, row in data_rows.iterrows():
            # 跳过空行（基于客户号或名称）
            if pd.isna(row[1]) and pd.isna(row[2]):
                continue

            base_data = {
                '客户号': row[1],
                '客户名称': row[2],
                '客户督导': row[3],
                '新老客户区分': row[4]
            }

            for m in range(12):
                offset = month_start_col + (m * col_step)
                
                # 辅助函数: 仿 getSource 逻辑
                def get_source(idx_old, idx_new):
                    val_new = row[offset + idx_new]
                    val_old = row[offset + idx_old]
                    is_new = pd.notna(val_new) and str(val_new).strip() != ""
                    
                    return {
                        'name': val_new if is_new else val_old,
                        'ratio': ratio_row[offset + idx_new] if is_new else ratio_row[offset + idx_old]
                    }

                invite = get_source(1, 2)
                deal = get_source(3, 4)
                manage = get_source(6, 7)

                # 构建中间记录（与 Excel 键对应）
                excel_record = {
                    **base_data,
                    '月份': f"{m + 1}月",
                    '信息入口督导': row[offset + 0],
                    '信息入口占比': ratio_row[offset + 0],
                    '邀约到店督导': invite['name'],
                    '邀约到店占比': invite['ratio'],
                    '成交率提升督导': deal['name'],
                    '成交率提升占比': deal['ratio'],
                    '门店经营规划督导': manage['name'],
                    '门店经营规划占比': manage['ratio'],
                    'GL100落地督导': row[offset + 5],
                    'GL100落地占比': ratio_row[offset + 5],
                    '招聘督导': row[offset + 8],
                    '招聘占比': ratio_row[offset + 8]
                }

                # 映射到数据库字段
                db_record = self.fixed_values.copy()
                for excel_key, db_key in self.mapping.items():
                    val = excel_record.get(excel_key)
                    
                    # 特殊处理
                    if db_key == 'month':
                        val = int(str(val).replace('月', '')) if pd.notna(val) else 0
                    elif db_key.endswith('_pct'):
                        # 转换占比为百分比数值 (例如 0.8 -> 80.0)
                        try:
                            val = float(val) * 100 if pd.notna(val) else 0
                        except:
                            val = 0
                    
                    # 清理空值
                    db_record[db_key] = None if pd.isna(val) or val == "" else val
                
                records.append(db_record)

        return pd.DataFrame(records)

if __name__ == "__main__":
    from core.extractor import ExcelExtractor
    try:
        ext = ExcelExtractor()
        raw_df = ext.fetch_raw_data()
        trans = Transformer()
        final_df = trans.transform(raw_df)
        print(f"转换完成，共生成 {len(final_df)} 条月度记录")
        print("\n转换结果预览 (前 3 条):")
        print(final_df.head(3).to_string())
    except Exception as e:
        print(f"转换失败: {e}")
