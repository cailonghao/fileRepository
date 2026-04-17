from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Any
import uvicorn
import os
import shutil
from datetime import datetime

# 导入任务函数
from tasks.sync_monthly_main import sync_monthly, sync_monthly_from_csv
from tasks.generate_daily_targets import generate_daily_targets
from tasks.sync_daily_to_db import sync_daily
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings

app = FastAPI(title="Python Data Sync API", description="数据同步项目 FastAPI 服务")

# 添加跨域支持
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法 (GET, POST, etc.)
    allow_headers=["*"],  # 允许所有请求头
)

# 确保临时目录存在
TEMP_DIR = "temp_uploads"
os.makedirs(TEMP_DIR, exist_ok=True)

# 接口文档数据
API_DOCS = [
    {
        "url": "/api/v1/generate/monthly",
        "method": "POST",
        "params": {"file": "UploadFile (Excel)"},
        "description": "上传 Excel，读取默认工作表，执行 KPI 转换并返回月度考核 CSV 文件 (不操作数据库)"
    },
    {
        "url": "/api/v1/generate/daily",
        "method": "POST",
        "params": {"file": "UploadFile (Excel)"},
        "description": "上传 Excel，读取第 2 个工作表，计算每日目标分摊并返回 CSV 文件 (不操作数据库)"
    },
    {
        "url": "/api/v1/sync/monthly",
        "method": "POST",
        "params": {"file": "UploadFile (CSV)"},
        "description": "上传已分解的月度考核 CSV 文件，将其同步到数据库 (crm_kpi_shop_month)"
    },
    {
        "url": "/api/v1/sync/daily",
        "method": "POST",
        "params": {"file": "UploadFile (CSV)"},
        "description": "上传已生成的每日目标 CSV 文件，将其同步到数据库 (crm_kpi_shop_emp_day)"
    },
    {
        "url": "/api/v1/config/status",
        "method": "GET",
        "params": {},
        "description": "获取当前系统配置状态及数据库连接信息"
    },
    {
        "url": "/doc",
        "method": "GET",
        "params": {},
        "description": "返回系统接口文档 JSON"
    }
]

class syncResponse(BaseModel):
    status: str
    message: str
    data: Any = None

@app.get("/")
async def root():
    return {"status": "running", "project": "Python Data Sync API"}

@app.get("/doc")
async def get_docs():
    """返回所有接口的文档信息"""
    return {
        "title": "Python Data Sync API Documentation",
        "version": "1.3.0",
        "endpoints": API_DOCS
    }

# --- 生成类接口 ---

@app.post("/api/v1/generate/monthly")
async def generate_monthly_csv(file: UploadFile = File(...)):
    """上传 Excel 生成月度考核 CSV"""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="请上传 Excel 文件")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_input = os.path.join(TEMP_DIR, f"in_monthly_{timestamp}_{file.filename}")
    temp_output = os.path.join(TEMP_DIR, f"out_monthly_{timestamp}.csv")
    
    try:
        with open(temp_input, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        result = sync_monthly(excel_file=temp_input, output_csv=temp_output)
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])
            
        return FileResponse(
            path=temp_output, 
            filename=f"monthly_kpi_{timestamp}.csv",
            media_type='application/octet-stream'
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/generate/daily")
async def generate_daily_csv(file: UploadFile = File(...)):
    """上传 Excel 生成每日目标 CSV"""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="请上传 Excel 文件")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_input = os.path.join(TEMP_DIR, f"in_daily_{timestamp}_{file.filename}")
    temp_output = os.path.join(TEMP_DIR, f"out_daily_{timestamp}.csv")
    
    try:
        with open(temp_input, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        result = generate_daily_targets(excel_file=temp_input, output_csv=temp_output)
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])
            
        return FileResponse(
            path=temp_output, 
            filename=f"daily_targets_{timestamp}.csv",
            media_type='application/octet-stream'
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- 同步类接口 ---

@app.post("/api/v1/sync/monthly", response_model=syncResponse)
async def sync_monthly_data(file: UploadFile = File(...)):
    """上传 CSV 同步月度 KPI 到数据库"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="请上传 CSV 文件")
    
    temp_path = os.path.join(TEMP_DIR, f"sync_monthly_{datetime.now().timestamp()}.csv")
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        result = sync_monthly_from_csv(temp_path)
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])
            
        return {"status": "success", "message": result["message"], "data": {"records": result.get("records_loaded")}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/sync/daily", response_model=syncResponse)
async def sync_daily_data(file: UploadFile = File(...)):
    """上传 CSV 同步每日目标到数据库"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="请上传 CSV 文件")
    
    temp_path = os.path.join(TEMP_DIR, f"sync_daily_{datetime.now().timestamp()}.csv")
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        result = sync_daily(csv_file=temp_path)
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])
            
        return {"status": "success", "message": result["message"], "data": {"records": result.get("records_loaded")}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/config/status")
async def get_config_status():
    """获取配置状态"""
    return {
        "db_host": settings.DB_HOST,
        "db_name": settings.DB_NAME,
        "excel_path": settings.EXCEL_FILE_PATH,
        "mapping_entries": len(settings.mapping.get("mapping", {}))
    }

if __name__ == "__main__":
    # 使用新端口
    uvicorn.run(app, host="0.0.0.0", port=30001)
