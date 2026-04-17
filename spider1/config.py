import os

# Target URLs
BASE_URL = "https://gt1989.onbus.cn"
LOGIN_URL = f"{BASE_URL}/login.jsp"
#JAVA_API_BASE_URL = "http://127.0.0.1:10001/main/tps/erp"
JAVA_API_BASE_URL = "https://test-kapok-admin3.guangtaotaoci.com/api/main/sys/user/login"

# File Paths
STATE_FILE = "state.json"
DAILY_RECORD_CSV = "daily_extraction_log.csv"

# Timeouts
DEFAULT_TIMEOUT = 30000  # 30 seconds

# Scheduler
EXECUTION_TIME = "02:00"  # 每日自动执行时间 (24小时制)
EXECUTION_REPORT_FILE = "execution_report.txt"
