# Python Data Sync Service

这是一个基于 FastAPI 的数据同步服务，支持月度 KPI 考核数据转换、每日业绩目标生成以及自动化数据同步功能。

## 1. 本地运行 (Local Run)

### 环境安装
建议使用 Python 3.12+。首先安装依赖：
```bash
pip install -r requirements.txt
```

### 启动服务
```bash
python api_main.py
```
服务默认运行在端口 `30001`。

---

## 2. Docker 部署 (Docker Deployment)

项目中已包含完整的 `Dockerfile` 和 `.dockerignore`。

### 构建镜像
```bash
docker build -t python-datasync:v1.0 .
```

### 运行容器
```bash
docker run -d \
  -p 30001:30001 \
  --name datasync-service \
  --restart always \
  python-datasync:v1.0
```

### (推荐) 挂载资源目录
如需在本地查看生成的 CSV 文件，请挂载 `resources` 目录：
```bash
docker run -d \
  -p 30001:30001 \
  -v ${PWD}/resources:/app/resources \
  --name datasync-service \
  python-datasync:v1.0
```

---

## 3. 接口说明 (API Documentation)

服务启动后，您可以通过以下地址访问接口及文档：

- **交互式文档 (Swagger UI)**: `http://localhost:30001/docs`
- **自定义 JSON 文档**: `http://localhost:30001/doc`

### 核心接口列表
1.  **生成月度考核 CSV**: `POST /api/v1/generate/monthly`
2.  **生成每日目标 CSV**: `POST /api/v1/generate/daily`
3.  **同步月度考核入库**: `POST /api/v1/sync/monthly`
4.  **同步每日目标入库**: `POST /api/v1/sync/daily`
