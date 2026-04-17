from sqlalchemy import create_engine, text
from core.config import settings
import pandas as pd

class Loader:
    def __init__(self):
        # 构建 SQLAlchemy 连接字符串
        # 格式: mysql+mysqlconnector://user:password@host:port/dbname
        self.conn_str = (
            f"mysql+mysqlconnector://{settings.DB_USER}:{settings.DB_PASSWORD}"
            f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
        )
        self.engine = create_engine(self.conn_str)
        self.table_name = settings.TABLE_NAME

    def get_employee_mapping(self):
        """
        从数据库获取员工姓名到 ID 的映射
        """
        print("正在获取员工 ID 映射...")
        query = "SELECT id, name FROM crm_shop_emp WHERE status = 1"
        with self.engine.connect() as conn:
            df = pd.read_sql(query, conn)
        
        # 处理可能的空格
        df['name'] = df['name'].str.strip()
        return dict(zip(df['name'], df['id']))

    def load_data(self, df: pd.DataFrame):
        """
        将数据写入数据库
        """
        if df.empty:
            print("没有数据需要写入。")
            return

        # 1. 映射字段名称 (根据配置中的 mapping 进行重命名)
        mapping = settings.mapping.get('mapping', {})
        df = df.rename(columns=mapping)
        
        # 2. 注入固定值 (如 status, year 等)
        fixed_values = settings.mapping.get('fixed_values', {})
        for col, val in fixed_values.items():
            df[col] = val

        # 3. 填充员工 ID
        emp_map = self.get_employee_mapping()
        print("正在根据姓名填充员工 ID...")
        def map_id(name):
            if not name: return None
            return emp_map.get(str(name).strip())

        # 检查配置中定义的 ID 映射关系
        # 我们寻找 mapping 中对应关系，如果目标是 _id 且源是 _name
        # 或者直接硬编码常见的对应关系
        name_to_id_fields = {
            'shop_emp_name': 'shop_emp_id',
            'valid_customer_shop_emp_name': 'valid_customer_shop_emp_id',
            'go_shop_shop_emp_name': 'go_shop_shop_emp_id',
            'sale_ok_amount_shop_emp_name': 'sale_ok_amount_shop_emp_id',
            'manage_shop_emp_name': 'manage_shop_emp_id',
            'gl100_shop_emp_name': 'gl100_shop_emp_id',
            'hr_shop_emp_name': 'hr_shop_emp_id'
        }

        for name_col, id_col in name_to_id_fields.items():
            if name_col in df.columns and id_col in df.columns:
                df[id_col] = df[name_col].apply(map_id)
                df[id_col] = pd.to_numeric(df[id_col], errors='coerce').astype('Int64')

        # 4. 格式化百分比列
        pct_cols = [c for c in df.columns if c.endswith('_pct')]
        for col in pct_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).round(2)

        # 5. 单位转换 (已在生成阶段处理，此处仅格式化)
        if 'sale_ok_amount_plan' in df.columns:
            df['sale_ok_amount_plan'] = pd.to_numeric(df['sale_ok_amount_plan'], errors='coerce').fillna(0).round(2)

        # 6. 只保留数据库表中存在的列，防止 to_sql 报错
        # 获取目标表的列清单
        print(f"检查表 `{self.table_name}` 的结构...")
        with self.engine.connect() as conn:
            res = conn.execute(text(f"DESC `{self.table_name}`"))
            db_cols = [r[0] for r in res]
        
        # 过滤掉不在表中的 DataFrame 列
        final_cols = [c for c in df.columns if c in db_cols]
        df = df[final_cols]
        
        print(f"准备写入 {len(df)} 条记录到表 {self.table_name}...")
        
        try:
            df.to_sql(
                name=self.table_name,
                con=self.engine,
                if_exists='append',
                index=False,
                chunksize=500
            )
            print("数据同步成功！")
        except Exception as e:
            print("数据写入失败！")
            if hasattr(e, 'orig'):
                print(f"源错误: {e.orig}")
            else:
                print(f"详细错误: {e}")
            raise

if __name__ == "__main__":
    # 测试连接
    try:
        loader = Loader()
        mapping = loader.get_employee_mapping()
        print(f"成功获取 {len(mapping)} 个员工映射")
    except Exception as e:
        print(f"数据库连接失败: {e}")
