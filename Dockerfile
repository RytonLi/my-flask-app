FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

RUN useradd -m appuser
USER appuser

# 暴露端口
EXPOSE 5000

# 运行应用
# 优先使用环境变量 PORT（Render 等平台会自动注入，默认 10000），
# 本地没有该变量时回退到 5000 端口，保证本地 docker run -p 5000:5000 依然可用。
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-5000} app:app"]
