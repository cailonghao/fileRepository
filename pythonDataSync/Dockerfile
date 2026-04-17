# 使用 Python 3.12 slim 版本作为基础镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量，确保 Python 输出不被缓存
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 安装系统依赖 (如果需要编译某些库)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# 先复制依赖文件并安装，利用 Docker 缓存层
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY . .

# 创建临时上传目录并设置权限
RUN mkdir -p temp_uploads resources && chmod 777 temp_uploads resources

# 暴露 FastAPI 运行的端口
EXPOSE 30001

# 启动服务
CMD ["python", "api_main.py"]
