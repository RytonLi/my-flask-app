# 零基础教程：看懂并部署这个 Flask 项目（Windows + Docker）

> 适用对象：完全不懂 Python Web 开发和 Docker 的新手。
> 学习环境：Windows + Docker Desktop + PowerShell（你已具备）。
> 学完你将能：① 说出每个文件/目录的作用；② 看懂并修改 Flask 代码；③ 掌握 Docker 核心概念和常用命令；④ 把这个项目用 Docker 跑在本地。
> 预计耗时：集中学习半天到一天（含练习）。

---

## 目录

- [第 0 章 开始前的准备](#第-0-章-开始前的准备)
- [第 1 章 这个项目是干嘛的？](#第-1-章-这个项目是干嘛的)
- [第 2 章 项目文件逐个讲](#第-2-章-项目文件逐个讲)
- [第 3 章 Flask 基础](#第-3-章-flask-基础)
- [第 4 章 实战练习（Flask 部分）](#第-4-章-实战练习flask-部分)
- [第 5 章 Docker 基础](#第-5-章-docker-基础)
- [第 6 章 逐行读懂 Dockerfile](#第-6-章-逐行读懂-dockerfile)
- [第 7 章 实战：本地 Docker 部署](#第-7-章-实战本地-docker-部署)
- [第 8 章 实战练习（Docker 部分）](#第-8-章-实战练习docker-部分)
- [第 9 章 顺带搞懂 CI/CD](#第-9-章-顺带搞懂-cicd)
- [第 10 章 常见坑（Windows 专属）](#第-10-章-常见坑windows-专属)
- [第 11 章 验收清单](#第-11-章-验收清单)
- [附录 练习参考答案](#附录-练习参考答案)

---

## 第 0 章 开始前的准备

### 0.1 你需要的东西（你已经基本都有了）

| 工具 | 作用 | 状态 |
| --- | --- | --- |
| Python 3.12 | 运行 Python 代码 | 本项目自带 `venv` 虚拟环境，已装好 |
| VS Code（或任意编辑器） | 看代码、改代码 | 推荐，装 Python 插件体验更好 |
| Docker Desktop | 在本地跑容器 | 你已安装，Windows 上以鲸鱼图标出现在任务栏右下角 |
| PowerShell 或 CMD | 执行命令 | Windows 自带 |

### 0.2 两个先要建立的认知

1. **命令是在"当前目录"下执行的**。教程里所有命令，默认都在项目根目录 `D:\itheima\02_git+CICD\my-flask-app` 下运行。在 VS Code 里按 `Ctrl + `` ` 打开终端，它会自动定位到这个目录。
2. **代码里的 `.\` 开头的命令**是 PowerShell 里"当前目录下的文件"的写法。例如 `.\venv\Scripts\python.exe` 表示"用项目虚拟环境里的 Python"。

### 0.3 本教程的命令约定

- 用 `python` 的地方，你在本项目里应输入 `.\venv\Scripts\python.exe`（因为项目自带虚拟环境，`python` 命令不一定全局可用）。
- 用 Docker 的命令时，Docker 命令是全局的，直接输入 `docker ...` 即可。
- 教程中所有命令我都实测过，你照抄即可；卡住了就看第 10 章。

---

## 第 1 章 这个项目是干嘛的？

**一句话：这是一个极简的 Flask Web 应用——你用浏览器访问它，它返回一段 JSON 数据；同时它配套了一套 CI/CD 流水线，用于演示"代码提交后自动检查、自动测试、自动构建镜像"的完整流程。**

它是为了验证 CI/CD 工作流而存在的，所以代码故意写得非常简单，重点在工程流程。

### 1.1 这个项目的整体流程（先有个画面感）

```text
你在本地写代码/改代码
        │
        ▼
git 提交并推送到 GitHub（push 到 main 分支）
        │
        ▼
GitHub Actions 自动执行 ci-cd.yml 流水线：
  ① lint    —— 代码风格/类型检查
  ② test    —— 跑单元测试、生成覆盖率报告
  ③ build   —— 构建 Docker 镜像并推送到 Docker Hub
  ④ deploy  ——（示例）SSH 到服务器，拉取镜像并运行容器
        │
        ▼
你的服务以 Docker 容器的形式跑在服务器上
```

你的第 4 个学习目标（本地 Docker 部署）就是手动完成流水线里 `build` 那一步要做的事——只不过是在你自己电脑上。

### 1.2 git 历史（这个项目怎么来的）

```text
34a8d74 init: 初始化 Flask 项目
3b57497 ci: 添加 CI/CD 工作流
```

这个项目只有两次提交：先搭好 Flask 应用，再配上 CI/CD。你以后每改一次代码，也会留下一条提交记录。

---

## 第 2 章 项目文件逐个讲

### 2.1 先看整体目录树

```text
my-flask-app/
├── .github/
│   └── workflows/
│       └── ci-cd.yml      ← CI/CD 流水线定义（自动化检查/构建/部署）
├── tests/
│   └── test_app.py        ← 单元测试
├── venv/                  ← Python 虚拟环境（本地开发用，不提交 git）
├── htmlcov/               ← 测试覆盖率网页报告（自动生成）
├── .mypy_cache/           ← 类型检查缓存（自动生成）
├── .pytest_cache/         ← pytest 缓存（自动生成）
├── __pycache__/           ← Python 字节码缓存（自动生成）
├── .coverage              ← 覆盖率数据文件（自动生成）
├── coverage.xml           ← 覆盖率 XML 报告（自动生成）
├── .flake8                ← flake8 代码检查配置
├── .gitignore             ← git 忽略规则
├── app.py                 ← Flask 应用主文件（核心！）
├── Dockerfile             ← 构建 Docker 镜像的"配方"（核心！）
├── pyproject.toml         ← black/mypy/pytest 等工具配置
└── requirements.txt       ← Python 依赖清单
```

### 2.2 每个文件/目录的作用（重点背这张表）

| 路径 | 是什么 | 作用 | 你要不要改 |
| --- | --- | --- | --- |
| `app.py` | Flask 应用入口 | 定义了两个接口 `/` 和 `/health`，返回 JSON | **要**，这是你写业务代码的地方 |
| `requirements.txt` | 依赖清单 | 列出项目需要的 Python 库及版本，`pip install -r requirements.txt` 一键安装 | 加依赖时改 |
| `Dockerfile` | 镜像构建配方 | 告诉 Docker 怎么把项目打包成镜像 | 要能看懂，练习里会改 |
| `.github/workflows/ci-cd.yml` | CI/CD 流水线 | push 到 GitHub 后自动执行：检查代码→测试→构建镜像→部署 | 配置 CI/CD 时改 |
| `tests/test_app.py` | 单元测试 | 验证 `/` 和 `/health` 是否正常返回 | 写测试时改 |
| `pyproject.toml` | 工具配置 | 配置 black（格式化）、mypy（类型检查）、pytest | 按需改 |
| `.flake8` | 工具配置 | 配置 flake8（代码风格检查） | 按需改 |
| `.gitignore` | git 忽略规则 | 告诉 git 哪些文件不要提交（如 venv、缓存） | 新增需忽略的文件时改 |
| `venv/` | 虚拟环境 | 项目独立的 Python 解释器和已安装的库，避免污染系统 | **不要动**，也不要提交 |
| `htmlcov/`、`.coverage`、`coverage.xml` | 测试产物 | 运行带覆盖率测试后自动生成 | **不要动**，已加入 .gitignore |
| `__pycache__/`、`.pytest_cache/`、`.mypy_cache/` | 缓存 | 运行工具时自动生成 | **不要动**，可随时删 |
| `.git/` | git 仓库内部数据 | 记录所有提交历史 | **绝对不要手动改** |

> 记忆口诀：**带 `.` 开头的多是配置文件；带 `_cache`/`pycache`/`cov` 的全是自动生成的垃圾，不用管；真正要用心看的是 `app.py`、`Dockerfile`、`requirements.txt`、`ci-cd.yml` 这四个文件。**

---

## 第 3 章 Flask 基础

### 3.1 Web 应用到底是怎么工作的？

想象一个饭店：

```text
客人（浏览器）                饭店（Flask 应用）
   │  1. 点菜：我要吃" / "       │
   │ ───────────────────────►   │
   │                            │  2. 查菜单（路由表）
   │                            │  3. 后厨做菜（执行视图函数）
   │  4. 上菜：返回 HTML/JSON    │
   │ ◄───────────────────────   │
```

在 Web 世界里：

- **请求（Request）**：浏览器访问 `http://localhost:5000/`，就是发了一个 GET 请求。
- **路由（Route）**：URL 中 `/` 后面的部分，Flask 用它来匹配"该让哪段代码处理"。
- **视图函数（View Function）**：处理请求的 Python 函数，它的返回值就是响应内容。
- **响应（Response）**：服务器返回的数据（这里是一段 JSON）。

### 3.2 逐行读懂 `app.py`

先看完整代码：

```python
from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/")
def hello():
    return jsonify({"message": "Hello, CI/CD!"})


@app.route("/health")
def health():
    return jsonify({"status": "healthy"})


if __name__ == "__main__":
    app.run(debug=True)
```

逐行解释：

| 代码 | 意思 |
| --- | --- |
| `from flask import Flask, jsonify` | 从 Flask 库导入两个东西：`Flask`（创建应用的类）、`jsonify`（把字典转成 JSON 响应的函数） |
| `app = Flask(__name__)` | 创建 Flask 应用实例。`__name__` 是当前模块名，Flask 靠它定位项目文件 |
| `@app.route("/")` | 装饰器：注册路由。意思是"当有人访问 `/` 时，执行下面这个函数" |
| `def hello():` | 视图函数。它的返回值就是浏览器看到的内容 |
| `return jsonify({...})` | 把 Python 字典转成 JSON 字符串返回，并自动带上 `Content-Type: application/json` |
| `if __name__ == "__main__":` | "只有当这个文件被直接运行时才执行"——如果是被别人 import，则不启动服务器 |
| `app.run(debug=True)` | 启动开发服务器，`debug=True` 表示改代码自动重启、出错显示详细页面 |

**怎么理解 `@app.route`？** 它相当于在应用里登记了一张"菜单"：

```text
URL  /       →  hello()   → {"message": "Hello, CI/CD!"}
URL  /health →  health()  → {"status": "healthy"}
```

### 3.3 怎么把项目跑起来（开发模式）

方式一：直接用 Python 运行（最简单）

```powershell
.\venv\Scripts\python.exe app.py
```

方式二：用 Flask 自带的命令行工具（效果一样）

```powershell
.\venv\Scripts\flask.exe run
```

启动后终端会显示 `Running on http://127.0.0.1:5000`，打开浏览器访问：

- `http://127.0.0.1:5000/` → 看到 `{"message":"Hello, CI/CD!"}`
- `http://127.0.0.1:5000/health` → 看到 `{"status":"healthy"}`

我在本机实测的输出（你可以对比）：

```text
GET /       → 200  {"message": "Hello, CI/CD!"}
GET /health → 200  {"status": "healthy"}
```

按 `Ctrl + C` 停止服务器。

### 3.4 小实验（5 分钟，理解"改代码→看效果"）

1. 打开 `app.py`，把 `"Hello, CI/CD!"` 改成 `"Hello, World!"`。
2. 保存（`debug=True` 模式下服务器会自动重启，无需手动重启）。
3. 刷新浏览器，看到内容变了。
4. 改回来，保存。

这就是 Web 开发的日常循环：**改代码 → 保存 → 刷新 → 看效果**。

---

## 第 4 章 实战练习（Flask 部分）

> 每道题先自己写，卡住了再看文末参考答案。做完一道就跑一下测试，形成"写完就验证"的习惯。

### 练习 1：新增一个返回当前时间的接口

在 `app.py` 里新增路由 `/api/time`，访问时返回类似：

```json
{"time": "2026-08-04T09:30:00.123456"}
```

提示：Python 标准库 `datetime` 里的 `datetime.now()` 可以获取当前时间，`isoformat()` 可以转成字符串格式。

### 练习 2：新增一个带参数的接口

新增路由 `/greet/<name>`，访问 `/greet/小明` 时返回：

```json
{"message": "Hello, 小明!"}
```

提示：`<name>` 是 Flask 的"动态路由"，函数接收同名参数。

### 练习 3：为两个新接口写测试

打开 `tests/test_app.py`，照着现有测试的写法，为 `/api/time` 和 `/greet/<name>` 各写一个测试函数，然后运行：

```powershell
.\venv\Scripts\python.exe -m pytest -v
```

预期看到 4 条测试全部通过（原来 2 条 + 新增 2 条）。

---

## 第 5 章 Docker 基础

### 5.1 为什么要用 Docker？

你遇到过这些问题吗？

- "在我电脑上能跑，到你电脑上就不行了"（环境不一致）。
- 部署新服务要手动装 Python、装库、配环境，又慢又容易错。
- 升级依赖后老版本应用挂了，想回滚却回不去。

Docker 的答案：**把"你的代码 + 运行环境"打包成一个独立的"集装箱"，这个集装箱在任何装了 Docker 的机器上跑起来结果完全一样。**

### 5.2 三个核心概念（必须背下来）

| 概念 | 类比 | 一句话定义 | 可以有几个 |
| --- | --- | --- | --- |
| **镜像（Image）** | 安装包 / 光盘 | 只读的"模板"，包含代码、运行环境、配置 | 可以有很多个 |
| **容器（Container）** | 运行中的程序 | 镜像跑起来后的实例，可以启动/停止/删除 | 一个镜像可以跑多个容器 |
| **仓库（Registry）** | 应用商店 | 存放和分享镜像的地方，如 Docker Hub | 公共的/私有的 |

关系链条：

```text
编写 Dockerfile（配方）
        │ docker build
        ▼
    镜像 Image（模板）
        │ docker run
        ▼
    容器 Container（运行中的实例）
```

类比记忆：**Dockerfile 是菜谱，镜像是一份做好的菜的冷冻包装，容器是你从冰箱拿出来加热后端上桌的那份。** 同一份冷冻包装可以加热出很多份。

### 5.3 常用 Docker 命令（先混个脸熟，后面实战会用）

| 命令 | 作用 |
| --- | --- |
| `docker --version` | 查看 Docker 版本 |
| `docker info` | 查看 Docker 是否正常运行 |
| `docker images` | 列出本地已有的镜像 |
| `docker ps` | 列出正在运行的容器 |
| `docker ps -a` | 列出所有容器（包括已停止的） |
| `docker build -t 名字 .` | 根据当前目录的 Dockerfile 构建镜像 |
| `docker run -d --name 名字 -p 宿主机端口:容器端口 镜像` | 运行容器 |
| `docker logs -f 容器名` | 查看容器日志（`-f` 持续跟踪） |
| `docker exec -it 容器名 sh` | 进入容器内部执行命令 |
| `docker stop 容器名` | 停止容器 |
| `docker rm 容器名` | 删除容器（先停止） |
| `docker rmi 镜像名` | 删除镜像 |
| `docker image prune` | 清理悬空镜像 |

### 5.4 Docker Desktop 在 Windows 上是怎么工作的？

关键认知：**Docker 容器基于 Linux 内核，Windows 不能直接跑。** Docker Desktop 的做法是：在你电脑后台悄悄运行一个轻量 Linux 虚拟机，Docker 命令都是发给这个虚拟机的。

所以你不需要关心虚拟机在哪——只需要保证：

1. **Docker Desktop 正在运行**（任务栏右下角有鲸鱼图标）。
2. 在 PowerShell / CMD 里正常输入 `docker` 命令即可。

这也是为什么本项目的 Dockerfile 里用 `gunicorn`（Linux 专属的生产级服务器）而本地开发用 `flask run`——见下一章。

---

## 第 6 章 逐行读懂 Dockerfile

这是项目里的完整 Dockerfile：

```dockerfile
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 暴露端口
EXPOSE 5000

# 运行应用
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
```

逐行解释：

| 指令 | 意思 | 类比 |
| --- | --- | --- |
| `FROM python:3.12-slim` | 以官方 Python 3.12 精简版镜像为基础。`slim` 是精简版，体积更小 | 从"毛坯房"开始装修 |
| `WORKDIR /app` | 设置容器内的工作目录为 `/app`，之后的命令都在这里执行 | 进到房间里干活 |
| `COPY requirements.txt .` | 先把依赖清单复制进镜像 | 先买好材料清单 |
| `RUN pip install --no-cache-dir -r requirements.txt` | 在镜像构建时安装所有依赖。`--no-cache-dir` 不保留 pip 缓存，减小体积 | 按清单进货 |
| `COPY . .` | 把项目所有文件复制进镜像 | 把家具搬进屋 |
| `EXPOSE 5000` | 声明容器监听 5000 端口（仅是"声明"，真正对外暴露靠 `-p`） | 门上贴个标签：服务在 5000 |
| `CMD [...]` | 容器启动时执行的命令。这里是用 gunicorn 启动 Flask 应用 | 按下开机键后自动执行 |

### 6.1 为什么容器里用 `gunicorn`，本地却用 `flask run`？

这是新手最容易困惑的点，重点理解：

| | 本地开发 | 容器（生产） |
| --- | --- | --- |
| 命令 | `flask run` 或 `python app.py` | `gunicorn --bind 0.0.0.0:5000 app:app` |
| 服务器 | Flask 自带开发服务器 | gunicorn 生产级服务器 |
| 特点 | 改代码自动重载，方便调试；**不适合生产** | 稳定、支持多进程并发；**只支持 Linux/Unix** |

我在你的电脑上实测：直接运行 `gunicorn` 会立刻报错退出（它依赖 Linux 系统组件，Windows 本地跑不了）。但没关系——**镜像跑在 Docker Desktop 的 Linux 虚拟机里，所以容器里 gunicorn 能正常工作。**

顺便解释 `CMD` 里那行命令：`gunicorn --bind 0.0.0.0:5000 app:app`

- `--bind 0.0.0.0:5000`：监听所有网络接口的 5000 端口（写 `127.0.0.1` 的话容器外就访问不到了）。
- `app:app`：第一个 `app` 是文件名（`app.py`），第二个 `app` 是文件里那个 Flask 实例（`app = Flask(__name__)`）。意思是"去 app.py 里找 app 这个对象"。

### 6.2 一个隐藏问题：构建时会复制 `venv` 进镜像

注意 `COPY . .` 会复制**当前目录下所有文件**（除了 .git 内部数据可能受限）。也就是说，你那个 200+MB 的 `venv` 也会被塞进镜像，导致构建慢、镜像巨大。

解决办法是加一个 `.dockerignore` 文件（类似 `.gitignore`，专门告诉 Docker 构建时忽略哪些文件）。这是练习 5 的内容。

---

## 第 7 章 实战：本地 Docker 部署

这是你的核心目标。全程约 10 分钟，照做即可。

### 第 1 步：确认 Docker 就绪

打开 PowerShell，运行：

```powershell
docker --version
```

看到类似 `Docker version 29.6.2` 即正常（我的实测版本）。

再运行：

```powershell
docker info
```

如果正常，会输出一大段系统信息。如果报 `permission denied ... docker_engine` 或 `cannot connect to the Docker daemon`，说明 Docker Desktop 没启动——打开它（任务栏右下角点鲸鱼图标），等它显示 "Docker Desktop is running" 再重试。

### 第 2 步：构建镜像

在项目根目录执行：

```powershell
docker build -t my-flask-app .
```

命令分解：

- `docker build`：构建镜像。
- `-t my-flask-app`：给镜像起名 `my-flask-app`（`-t` 是 tag 的缩写）。
- `.`：构建上下文（当前目录），Docker 会在这里找 Dockerfile，并把这里的内容作为"原料"。

第一次构建需要下载 `python:3.12-slim` 基础镜像，可能要等几分钟。看到最后一行类似 `Successfully built xxx` / `Successfully tagged my-flask-app:latest` 即成功。

### 第 3 步：查看镜像

```powershell
docker images
```

应该能看到：

```text
REPOSITORY     TAG       IMAGE ID       CREATED          SIZE
my-flask-app   latest    ...            1 minute ago    ...
```

### 第 4 步：运行容器

```powershell
docker run -d --name my-flask-app -p 5000:5000 my-flask-app
```

命令分解：

- `docker run`：从镜像启动容器。
- `-d`：后台运行（detached），终端不占用。
- `--name my-flask-app`：给容器起名，方便之后用名字操作。
- `-p 5000:5000`：端口映射，**左边是宿主机（你电脑）端口，右边是容器内端口**。
- 最后的 `my-flask-app`：用哪个镜像。

成功后 Docker 会返回一长串容器 ID。

### 第 5 步：验证服务

浏览器访问：

- `http://localhost:5000/` → 看到 `{"message":"Hello, CI/CD!"}`
- `http://localhost:5000/health` → 看到 `{"status":"healthy"}`

或者在 PowerShell 里用命令验证：

```powershell
Invoke-WebRequest -Uri http://localhost:5000/health -UseBasicParsing
```

看到状态码 200 即成功。

### 第 6 步：查看日志（很有用）

```powershell
docker logs -f my-flask-app
```

能看到 gunicorn 的启动日志和每次访问记录。按 `Ctrl + C` 退出跟踪（不影响容器运行）。

### 第 7 步：进入容器内部看看

```powershell
docker exec -it my-flask-app sh
```

进入后可以执行：

```sh
ls /app
cat /app/app.py
exit
```

你会在容器里看到和项目一样的文件——这就是"环境一致"的直观感受。

### 第 8 步：停止并清理

```powershell
docker stop my-flask-app
docker rm my-flask-app
```

`docker stop` 停止容器，`docker rm` 删除容器（镜像还在，随时可以再 `docker run`）。此时 `docker ps` 应该为空。

### 7.1 常见问题速查表

| 现象 | 原因 | 解决 |
| --- | --- | --- |
| `docker run` 报端口被占用 | 5000 端口已被别的程序/容器占用 | 换映射端口：`-p 8000:5000`，然后访问 `localhost:8000` |
| 容器一启动就退出 | 应用启动失败（常见于依赖没装好） | `docker logs my-flask-app` 看报错 |
| 容器在跑但浏览器打不开 | 端口映射写反/写错 | 确认 `-p 左边:右边`，右边必须是容器内实际监听端口 5000 |
| 浏览器显示 `Connection refused` | 容器没在运行，或 Docker Desktop 没启动 | `docker ps` 确认容器存在 |
| 构建很慢 | 网络慢或复制了 venv | 换国内镜像源（见第 10 章），加 `.dockerignore`（练习 5） |
| `docker build` 在第一步就报错（拉取 `python:3.12-slim` 失败/超时） | 国内网络连不上 Docker Hub | 配置国内镜像加速器（见第 10 章坑 8） |

### 7.2 重新 build 会覆盖旧镜像吗？

会"覆盖"，但不是"删除"。用同一个名字反复构建时，发生的事情是这样的：

```text
build 前：my-flask-app:latest ──► 旧镜像 A（还占着磁盘）
build 后：my-flask-app:latest ──► 新镜像 B
          旧镜像 A 失去标签，变成 <none>:<none>（悬空镜像）
```

也就是说，`-t my-flask-app` 只是把 `my-flask-app:latest` 这个**标签**改指向新镜像；旧镜像的数据还留在磁盘上，只是"没人叫它名字了"，等你有空用 `docker image prune` 清理即可。

三个相关的实用结论：

1. **构建失败不影响旧镜像。** Docker 只有在构建成功后才打新标签；失败了，`my-flask-app:latest` 还是指向原来的镜像，你随时可以重试。
2. **正在运行的容器不受影响。** 基于旧镜像启动的容器会继续用旧镜像跑，只有**新启动**的容器才用新镜像。这就是练习 7 里"改了代码必须重新 build + 重新 run"的原因。
3. **查看和清理悬空镜像：**

```powershell
docker images                    # 查看所有镜像（新标签指向新 ID）
docker images -f dangling=true   # 查看悬空镜像（旧镜像）
docker image prune               # 清理所有悬空镜像
```

注意一个例外：**如果重新构建时代码和依赖都没变，BuildKit 会完整命中缓存，产出的镜像 ID 和原来完全一样**——标签本来就指向这个 ID，没有"旧镜像"失去标签，所以不会出现悬空镜像。这很正常，不代表"覆盖"没有发生，而是"内容没变，无需产生新镜像"。

悬空镜像只在**新镜像 ID 与旧镜像 ID 不同**时出现，比如你改了 `app.py` 再构建（练习 7 的场景）。如果改了代码重新构建后 `docker images -a` 里仍然看不到 `<none>` 的悬空镜像，通常是 Docker Desktop 较新版本自动回收了未使用的镜像（或使用了 containerd 存储后端，悬空镜像不按传统方式展示），用 `docker system df` 可以查看整体磁盘占用，同样不影响结论。

---

## 第 8 章 实战练习（Docker 部分）

### 练习 4：换端口运行

用 `-p 8000:5000` 运行容器，然后访问 `http://localhost:8000/`，确认能访问。再访问 `http://localhost:8000/health`。

### 练习 5：添加 `.dockerignore`，让构建更快、镜像更小

在项目根目录新建 `.dockerignore` 文件，内容参考（理解每行的含义再抄）：

```text
venv/
.git/
__pycache__/
.pytest_cache/
.mypy_cache/
htmlcov/
.coverage
coverage.xml
tests/
```

然后重新构建，观察构建时间和镜像大小变化：

```powershell
docker build -t my-flask-app .
docker images
```

> 小思考：为什么可以把 `tests/` 也排除？因为运行时不需要测试代码；测试在构建之前（CI 阶段）已经跑过了。

### 练习 6：体验 `--rm` 参数

运行容器时加 `--rm`：

```powershell
docker run -d --rm --name my-flask-app -p 5000:5000 my-flask-app
```

然后 `docker stop my-flask-app`，再运行 `docker ps -a`——会发现容器**自动被删除**了（`--rm` 的意思就是"停止后自动清理"）。适合临时测试。

### 练习 7：改代码 → 重新部署（完整循环）

1. 在 `app.py` 里新增一个 `/version` 接口，返回 `{"version": "1.0.0"}`。
2. 本地验证：`.\venv\Scripts\python.exe -m pytest`（别忘了补测试）。
3. 重新构建：`docker build -t my-flask-app .`。
4. 重新运行：`docker run -d --name my-flask-app -p 5000:5000 my-flask-app`。
5. 访问 `http://localhost:5000/version`，确认新接口生效。

> 关键认知：**代码是"烤进"镜像里的。改代码后必须重新 `docker build`，再重新 `docker run`，改动才会生效。** 这就是"不可变基础设施"的思想。

### 练习 8（挑战，可选）：在容器里用非 root 用户运行

安全最佳实践是不用 root 运行应用。试着在 Dockerfile 的 `COPY . .` 之后、`CMD` 之前加：

```dockerfile
RUN useradd -m appuser
USER appuser
```

重新构建运行，确认服务正常。想想为什么这样可以提高安全性。

---

## 第 9 章 顺带搞懂 CI/CD

你不需要现在就能写出 `ci-cd.yml`，但应该能看懂它干了什么——毕竟这个项目的存在意义就是验证它。

### 9.1 什么是 CI/CD？

- **CI（持续集成，Continuous Integration）**：每次代码提交后，自动跑检查（格式、类型、测试），尽早发现问题。
- **CD（持续交付/部署，Continuous Delivery/Deployment）**：自动把验证通过的代码构建成镜像、部署到服务器。

本项目的 `ci-cd.yml` 定义了 4 个"job"（任务），按顺序理解：

| 阶段 | 干什么 | 对应命令/工具 |
| --- | --- | --- |
| ① `lint` | 代码质量检查 | `flake8`（风格）、`black --check`（格式）、`mypy`（类型） |
| ② `test` | 单元测试 + 覆盖率 | `pytest --cov=app`，并在 Python 3.9~3.12 四个版本上都跑一遍 |
| ③ `build` | 构建 Docker 镜像并推送到 Docker Hub | Docker Buildx，打 `latest` 和 commit SHA 两个标签 |
| ④ `deploy` | （示例）SSH 到服务器部署 | `docker pull` → `docker stop/rm` → `docker run` → 健康检查 |

### 9.2 流水线的触发条件

```yaml
on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
```

意思是：**只有推送到 `main` 分支、或对 `main` 发起 Pull Request 时，流水线才会触发。**

### 9.3 依赖关系

```yaml
build:
  needs: [lint, test]   # 必须先通过 lint 和 test 才构建
deploy:
  needs: [build]        # 必须先构建成功才部署
```

这就是流水线的"关卡"思想：**上一关不过，下一关不启动。**

### 9.4 GitHub Secrets 是什么？

`ci-cd.yml` 里出现了 `${{ secrets.DOCKER_USERNAME }}`、`${{ secrets.SSH_HOST }}` 等。Secrets 是存在 GitHub 仓库设置里的"加密变量"，用来保存密码、密钥等敏感信息，避免明文写在代码里。

你在 GitHub 仓库页面：`Settings → Secrets and variables → Actions` 里配置。本项目的这些 secrets 目前并没有配置，所以流水线跑到 build 阶段会因登录失败而停止——这是正常的，等你真正想发布时再配置。

---

## 第 10 章 常见坑（Windows 专属）

### 坑 1：PowerShell 不允许运行 `Activate.ps1`

激活虚拟环境时可能报"禁止运行脚本"。两个选择：

- 直接不激活，始终用 `.\venv\Scripts\python.exe`（本教程就采用这种方式，最省事）。
- 或者执行一次（对当前用户生效）：

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 坑 2：`gunicorn` 在本地 Windows 跑不起来

这是正常的。`gunicorn` 只支持 Linux/Unix。本地开发用 `flask run` 或 `python app.py`，容器里才用 gunicorn。

### 坑 3：`docker info` 报权限/连接错误

大概率是 Docker Desktop 没启动。启动它，等右下角鲸鱼图标不再转圈，再重试。

### 坑 4：端口被占用

换一个宿主机端口即可：`-p 8000:5000`，然后访问 `localhost:8000`。

### 坑 5：中文乱码

项目文件都是 UTF-8 编码。用 VS Code 打开编辑（VS Code 默认 UTF-8，不会乱）。在 PowerShell 里看中文文件如果乱码，可以执行：

```powershell
$OutputEncoding = [System.Text.Encoding]::UTF8
```

或者直接用 VS Code 查看文件。

### 坑 6：Docker 构建/拉取镜像特别慢

国内网络访问 Docker Hub 慢是常态。可以在 Docker Desktop 的 `Settings → Docker Engine` 里配置国内镜像加速（例如阿里云、腾讯云镜像加速地址），改完点 Apply & Restart。这一步属于环境优化，不着急做。

### 坑 7：忘了"改代码要重新 build"

容器里运行的代码是构建时复制的快照。改了 `app.py` 只刷新浏览器是看不到变化的，必须：`docker build` → `docker stop` → `docker rm` → `docker run`。

### 坑 8：`docker build` 第一步就失败（拉取基础镜像连不上 Docker Hub）

这是国内网络环境最常遇到的问题。典型报错长这样：

```text
ERROR: failed to solve: failed to fetch oauth token:
Post "https://auth.docker.io/token": dial tcp [2a03:2880:...]:443: connectex: ...
```

意思是：构建镜像的第一步（下载基础镜像 `python:3.12-slim`）需要连 Docker Hub，但国内网络直连 Docker Hub 不稳定，连接超时了。

**解决办法：给 Docker Desktop 配置国内镜像加速器（推荐）**

1. 右键任务栏右下角的 Docker 鲸鱼图标 → **Settings**。
2. 左侧选择 **Docker Engine**。
3. 在右侧 JSON 里新增 `registry-mirrors` 这一项（保留原有内容，只加新项）：

```json
{
  "builder": {
    "gc": {
      "defaultKeepStorage": "20GB",
      "enabled": true
    }
  },
  "experimental": false,
  "registry-mirrors": [
    "https://docker.m.daocloud.io",
    "https://docker.1panel.live",
    "https://docker.xuanyuan.me"
  ]
}
```

4. 点 **Apply & Restart**，等 Docker 重启完成。
5. 验证配置生效：

```powershell
docker info
```

输出中能看到 `Registry Mirrors` 一栏（列出了你配置的地址）即成功。
6. 先单独测试拉取基础镜像：

```powershell
docker pull python:3.12-slim
```

能拉下来，再执行 `docker build -t my-flask-app .`。

几个补充说明：

- 这些公共加速器偶尔会限流或失效，**如果第一个失败就换下一个**；把最稳定的放在列表最前面。
- 追求最稳定的话，可以注册一个免费的阿里云账号，在"容器镜像服务 → 镜像加速器"里拿到专属地址（形如 `https://xxxx.mirror.aliyuncs.com`），把它加到列表第一位。
- 如果你电脑开了 VPN/加速器，也可以先**关掉它再试一次**——报错里的 IPv6 地址（`2a03:2880:...`）有时就是 DNS 被代理污染导致的。
- 临时救急法（不想改 Docker Desktop 配置时）：先把镜像从加速源拉到本地并改名，再构建：

```powershell
docker pull docker.m.daocloud.io/library/python:3.12-slim
docker tag docker.m.daocloud.io/library/python:3.12-slim python:3.12-slim
docker build -t my-flask-app .
```

### 坑 9：`.dockerignore` 能不能直接"引用" `.gitignore`，避免维护两份？

**不能。** Docker 的 `.dockerignore` 不支持任何 `include` / 引用其他文件的语法，它只认自己这个文件里的规则（Docker 社区提过这个需求，但至今没有实现）。语法上它俩确实很像，但**内容并不是一回事**，不能无脑共用。

以本项目为例，两者的差异：

| 规则 | `.gitignore` | 推荐版 `.dockerignore` | 为什么不一样 |
| --- | --- | --- | --- |
| `.git/` | 没有 | 有 | git 天然不管自己的内部目录，不用写；但 Docker 复制构建上下文时会整个带上 `.git`，又大又没必要 |
| `tests/` | 没有 | 有 | 测试代码必须提交进 git；但运行镜像时用不到测试，可以不烤进镜像 |
| `.env` | 有 | 建议也有 | git 是为了不泄露到仓库；Docker 是为了不把密钥烤进镜像（安全习惯） |
| `.vscode/`、`.idea/`、`build/`、`dist/` | 有 | 没有 | 只是开发工具/构建产物，进镜像影响很小，可忽略 |
| `.mypy_cache/` | **没有（漏了）** | 有 | mypy 的缓存目录，git 侧建议也补上这条 |

另外，两者的匹配规则也有细微差别（比如 `*` 在 `.gitignore` 里可以跨目录，在 `.dockerignore` 里不跨目录），所以"复制一份就能用"并不严谨。

**实际建议：接受两份文件、各自维护。** 它们加起来就十几行，而且几乎不会变——真实项目里绝大多数也是这么做的，没必要为了省几行引入额外复杂度。

如果确实想要"只改一处"，可以在构建前用一个小脚本生成 `.dockerignore`（每次改完 `.gitignore` 记得跑一次）：

```powershell
Copy-Item .gitignore .dockerignore
Add-Content .dockerignore @(
  ''
  '# Docker 专属'
  '.git/'
  'tests/'
  '.mypy_cache/'
)
```

> 小提醒：这个脚本只是"生成" `.dockerignore`，它本身不会自动执行；而且每次 `docker build` 前都要先跑它，否则改的规则不会生效。对新手来说，老老实实维护两份反而更不容易出错。

**那用软链接（symlink）让 `.dockerignore` 指向 `.gitignore` 行不行？** 也不建议，原因有三：

1. **Docker 官方不支持这种用法。** BuildKit（Docker Desktop 默认用的构建器）出于安全边界，会拒绝解析指向构建上下文之外的软链接；而且历史上出现过"`.dockerignore` 是软链接时构建直接报 `archive/tar: write too long` 失败"的已知 bug。没有官方文档推荐这么干。
2. **Windows + git 会让它悄悄失效。** Windows 上创建软链接需要管理员权限或开启开发者模式；更麻烦的是 git 在 Windows 默认 `core.symlinks=false`，你提交的软链接在别人 clone 下来后会变成一个"内容是一行路径"的普通文本文件，链接直接失效，ignore 规则全部不生效。
3. **最根本的：两份文件的内容本来就该不同。** 比如 `tests/` 必须提交给 git、但不需要进镜像。如果共用一份文件，写了 `tests/` 则 git 不再跟踪测试代码（CI 直接跑不了），不写则镜像里多带一份测试代码。软链接强制内容一致，必然让某一侧出错。

所以"避免重复维护"的正确做法仍然是：两个文件都很短，各自维护；或者用一个生成脚本（见上文）。

---

## 第 11 章 验收清单

学完对照自查，能做到以下 6 条就算真正掌握：

- [ ] 不看笔记，能说出 `app.py`、`Dockerfile`、`requirements.txt`、`ci-cd.yml`、`venv`、`tests/` 各自的作用。
- [ ] 能用一句话解释路由、视图函数、JSON 响应的关系，并能自己新增一个 Flask 接口。
- [ ] 能用一句话说清镜像、容器、仓库的区别。
- [ ] 能从零执行 `docker build` → `docker run` → 浏览器访问 → `docker logs` → `docker stop` 的完整流程。
- [ ] 改了代码后，知道要"重新构建 + 重新运行"才能生效。
- [ ] 能说出 `ci-cd.yml` 里四个 job 分别在干什么，以及 `needs` 的作用。

---

## 附录 练习参考答案

### 练习 1 答案：新增 `/api/time`

在 `app.py` 顶部 import 处加上 `datetime`：

```python
from datetime import datetime
from flask import Flask, jsonify
```

在 `health()` 函数后面新增：

```python
@app.route("/api/time")
def api_time():
    return jsonify({"time": datetime.now().isoformat()})
```

### 练习 2 答案：新增 `/greet/<name>`

```python
@app.route("/greet/<name>")
def greet(name):
    return jsonify({"message": f"Hello, {name}!"})
```

访问 `http://localhost:5000/greet/小明` 会返回 `{"message": "Hello, 小明!"}`。

### 练习 3 答案：新增测试

在 `tests/test_app.py` 末尾追加：

```python
def test_api_time(client):
    response = client.get("/api/time")
    assert response.status_code == 200
    assert "time" in response.json


def test_greet(client):
    response = client.get("/greet/小明")
    assert response.status_code == 200
    assert response.json["message"] == "Hello, 小明!"
```

运行测试：

```powershell
.\venv\Scripts\python.exe -m pytest -v
```

预期输出 `4 passed`。

### 练习 4 答案：换端口

```powershell
docker stop my-flask-app
docker rm my-flask-app
docker run -d --name my-flask-app -p 8000:5000 my-flask-app
```

访问 `http://localhost:8000/` 和 `http://localhost:8000/health`。

### 练习 5 答案：`.dockerignore`

在项目根目录新建 `.dockerignore`：

```text
venv/
.git/
__pycache__/
.pytest_cache/
.mypy_cache/
htmlcov/
.coverage
coverage.xml
tests/
```

重新构建后对比 `docker images` 里的 SIZE，镜像会明显变小。

### 练习 6 答案：`--rm`

```powershell
docker run -d --rm --name my-flask-app -p 5000:5000 my-flask-app
docker stop my-flask-app
docker ps -a
```

`docker ps -a` 里不再有 `my-flask-app`，说明容器停止时被自动清理了。

### 练习 7 答案：改代码重新部署

`app.py` 新增：

```python
@app.route("/version")
def version():
    return jsonify({"version": "1.0.0"})
```

`tests/test_app.py` 新增：

```python
def test_version(client):
    response = client.get("/version")
    assert response.status_code == 200
    assert response.json["version"] == "1.0.0"
```

然后依次执行：

```powershell
.\venv\Scripts\python.exe -m pytest
docker build -t my-flask-app .
docker stop my-flask-app
docker rm my-flask-app
docker run -d --name my-flask-app -p 5000:5000 my-flask-app
```

访问 `http://localhost:5000/version` 验证。

### 练习 8 答案（挑战）

修改后的 Dockerfile 关键部分：

```dockerfile
COPY . .

# 创建非 root 用户并切换
RUN useradd -m appuser
USER appuser

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
```

原理：`USER appuser` 之后容器内进程以普通用户身份运行。即使应用有漏洞被攻破，攻击者拿到的是普通用户权限，而不是 root——这就是"最小权限原则"。

---

> 最后的小建议：把这个文件重命名为 `README.md` 并提交到 git，它就会显示在 GitHub 仓库首页，随时可以查阅。祝你学习顺利！
