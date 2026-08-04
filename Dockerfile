FROM python:3.12-slim

# 从 uv 官方镜像拷入 uv / uvx 两个可执行文件
COPY --from=ghcr.io/astral-sh/uv:0.12.1 /uv /uvx /bin/

WORKDIR /app

# 先复制依赖声明，依赖没变时能命中 Docker 层缓存
COPY pyproject.toml uv.lock ./

# --frozen：直接用 uv.lock，不重新解析
# --no-dev：生产镜像不装 pytest 等开发依赖
RUN uv sync --frozen --no-dev

# 再复制全部代码
COPY . .

RUN useradd -m appuser
USER appuser

EXPOSE 5000

CMD ["sh", "-c", "uv run --no-sync gunicorn --bind 0.0.0.0:${PORT:-5000} app:app"]
