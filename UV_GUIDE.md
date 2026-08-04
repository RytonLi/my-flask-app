# uv 使用指南：把 pip 工作流迁移到 uv（零基础版）

> 阅读对象：对 pip / venv 有一点基础、但刚接触 uv 的同学。
> 本文结合当前项目 my-flask-app 的真实情况编写，命令均可在 Windows PowerShell 中直接运行。

## 目录

1. uv 与 pip 的区别
2. uv 的基本操作
3. 当前项目的 pip → uv 改造
4. 常见问题（FAQ）

## 1. uv 与 pip 的区别

### 1.1 它们分别解决什么问题

pip 是 Python 官方自带的包管理器，核心功能只有一个：把第三方库装进某个 Python 环境。它本身不管"项目"这个概念，也不管 Python 版本。

uv 是 Astral 公司用 Rust 写的现代 Python 工具链。它的定位不只是"pip 的加速版"，而是把 pip、venv、pyenv、pip-tools 这些工具的功能合并成了一个命令。

### 1.2 关键区别一览

| 维度 | pip | uv |
| --- | --- | --- |
| 用什么写的 | Python | Rust |
| 安装速度 | 慢，逐包解析、逐包下载 | 快数十倍，依赖解析并行 + 全局缓存 |
| 依赖锁定 | 不锁定，靠手写 requirements.txt | 自动生成 uv.lock，精确锁定所有依赖 |
| 虚拟环境 | 需要自己用 venv 创建并激活 | uv sync 自动创建 .venv，无需激活 |
| Python 版本 | 不管理 | uv python install 可下载和管理多个 Python 版本 |
| 项目模型 | 面向"环境" | 面向"项目"（pyproject.toml 声明） |
| 一键运行工具 | pip install 后再执行 | uvx 临时安装并运行 |
| 兼容旧流程 | — | 提供 uv pip 子命令，语法和 pip 几乎一样 |

### 1.3 用"文件视角"理解两者的工作模式

pip 时代，项目里通常有：

```text
requirements.txt   # 手动维护的依赖清单
venv/              # 手动创建的虚拟环境
```

装依赖：`pip install -r requirements.txt`。问题在于：requirements.txt 只写了"大概要哪些包"，不锁传递依赖；换台电脑、过几个月再装，结果可能不一样。

uv 时代，项目里是：

```text
pyproject.toml     # 声明项目信息和依赖（requirements.txt 的"升级版"）
uv.lock            # 锁文件：精确到每个包的版本，任何机器装出来一致
.venv/             # uv sync 自动创建的虚拟环境
.python-version    # 项目要求的 Python 版本
```

装依赖：`uv sync`。它的意思是"按照 pyproject.toml 的声明和 uv.lock 的锁定结果，把 .venv 环境同步成完全一致的状态"。可以类比 npm 的 package-lock.json 之于 package.json。

### 1.4 两个常见误解

- "装了 uv 就要卸载 pip"：不用。uv 只是接管了工作流，pip 仍然存在，两者可以共存。
- "uv 就是快一点的 pip"：不准确。`uv pip` 子命令才是"快一点的 pip"；uv 本身是一整套项目管理工具。

## 2. uv 的基本操作

### 2.1 安装 uv

Windows（PowerShell）：

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

macOS / Linux：

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

也可以走 winget / scoop：

```powershell
winget install astral-sh.uv
```

安装后确认版本：

```powershell
uv --version
```

升级 uv 本身：

```powershell
uv self update
```

### 2.2 初始化项目：uv init

在项目目录下运行 `uv init`（本项目用的就是 uv 0.12.1 的默认行为），会生成：

| 文件 | 作用 |
| --- | --- |
| pyproject.toml | 项目元数据 + 依赖声明 |
| .python-version | 项目用的 Python 版本 |
| README.md | 空文档（pyproject 里 readme 字段指向它） |
| src/<项目名>/ | 包的脚手架（默认的"包模式"） |

常用参数：

```powershell
uv init                 # 默认包模式：生成 src/<项目名>/ 脚手架
uv init --no-package    # 应用模式：生成扁平的 main.py，更简单
uv init --bare          # 只生成 pyproject.toml
```

### 2.3 管理依赖：uv add / uv remove

```powershell
uv add flask               # 添加运行时依赖
uv add --dev pytest        # 添加到开发依赖组
uv add flask==3.0.0        # 指定版本
uv remove flask            # 移除依赖
```

`uv add` 一次会做三件事：修改 pyproject.toml、更新 uv.lock、同步 .venv（把新包装进环境）。

### 2.4 同步环境：uv sync

```powershell
uv sync                    # 根据 pyproject.toml + uv.lock 同步 .venv
uv sync --frozen           # 不重新解析，直接用现有 uv.lock
uv sync --no-dev           # 只装生产依赖（部署时用）
```

`uv sync` 是 uv 工作流里最核心的命令：拉下别人的项目，`uv sync` 一下就能跑。

**默认会安装开发依赖（dev 组），不需要加 `--dev`。** 早期版本的 uv 里 dev 依赖不是默认安装的，需要显式 `uv sync --dev`；后来 uv 改为默认安装 dev 组并移除了这个参数（当前 0.12.1 的 `uv sync` 只有 `--no-dev` / `--only-dev`，没有 `--dev`）。所以：

- `--dev` 真正会用到的地方是 `uv add --dev <包>`（把包加进 dev 组）；
- `--no-dev` 是"显式排除 dev 组"，生产环境部署时才用，和默认行为方向相反。

### 2.5 运行命令：uv run

```powershell
uv run python app.py       # 用项目环境运行脚本
uv run pytest              # 运行测试
uv run flask --app app run # 运行任意命令
```

`uv run` 会在项目环境里执行命令，不需要先 `activate`；如果环境不是最新状态，它会自动先同步。

### 2.6 Python 版本管理

```powershell
uv python install 3.12     # 下载并安装 Python 3.12
uv python pin 3.12         # 把项目固定到 3.12（写入 .python-version）
uv python list             # 查看已安装的 Python
```

项目里有 .python-version 时，uv 会自动使用对应版本，找不到会提示或自动下载。

### 2.7 其他常用命令

```powershell
uv lock                                   # 只重新生成 uv.lock，不动环境
uv tree                                   # 查看依赖树
uv export --format requirements.txt       # 从锁文件导出 requirements.txt
uvx ruff check .                          # 临时下载并运行一个工具
```

### 2.8 pip ↔ uv 对照表

| 原来的 pip 操作 | 对应的 uv 操作 |
| --- | --- |
| python -m venv .venv | uv venv（或 uv sync 自动创建） |
| pip install flask | uv add flask（项目模式）/ uv pip install flask（环境模式） |
| pip install -r requirements.txt | uv add -r requirements.txt / uv pip install -r ... |
| pip freeze | uv pip freeze |
| pip list | uv pip list |
| pip uninstall flask | uv remove flask / uv pip uninstall flask |

## 3. 当前项目的 pip → uv 改造

### 3.1 先理解现状：`uv init` 之后目录发生了什么

你删掉旧 pyproject.toml、虚拟环境后运行 `uv init`，目录发生了这些变化（`git status --short` 也能看到）：

| 文件/目录 | 变化 | 说明 |
| --- | --- | --- |
| pyproject.toml | 被 uv 重新生成 | git 里还留着旧版本记录，所以显示为 M（modified） |
| .python-version | 新增 | 内容只有一行：`3.12` |
| README.md | 新增（空文件） | pyproject.toml 里 `readme = "README.md"` 指向它，所以 uv 必须创建一个 |
| src/my_flask_app/ | 新增 | uv init 生成的包脚手架 |
| .venv | 还没有 | uv init 只初始化项目，不安装依赖 |
| uv.lock | 还没有 | 第一次 uv add / uv sync 时才会生成 |

两个值得注意的细节：

**细节 1：作者信息里出现了中文引号“ ”**

打开 pyproject.toml 会看到：

```toml
authors = [
    { name = "“liyudong”", email = "“liyudong@pcitech.com”" },
]
```

这不是 uv 的 bug。uv init 会读取 git 配置（`git config user.name / user.email`）来填作者信息，而你的 git 配置里名字/邮箱本身带了中文引号（可能是在聊天工具或 Word 里复制进去的）。TOML 语法上能解析，但数据是错的，建议改掉。

**细节 2：uv 把项目初始化成了"可安装包"模式**

因为 pyproject.toml 里有：

```toml
[project.scripts]
my-flask-app = "my_flask_app:main"

[build-system]
requires = ["uv_build>=0.12.1,<0.13.0"]
build-backend = "uv_build"
```

这是 uv 默认"包模式"的产物：它认为 src/my_flask_app 是一个可安装的 Python 包，并配了一个命令行入口（`uv run my-flask-app` 会打印 "Hello from my-flask-app!"）。

但这个项目真正的 Flask 入口是根目录的 app.py，脚手架和这个入口并不是必须的。**保留它不影响任何功能**；想要更干净的话，可以删掉 src/ 目录以及上面两段配置（见 3.2 的可选清理）。

### 3.2 第一步：修正 pyproject.toml

保留原结构，只修正数据：

```toml
[project]
name = "my-flask-app"
version = "0.1.0"
description = "一个使用 Flask 实现的 CI/CD 演示应用"
readme = "README.md"
authors = [
    { name = "liyudong", email = "liyudong@pcitech.com" },
]
requires-python = ">=3.12"
dependencies = []
```

可选清理（不是必须）：如果想让项目回到最朴素的"应用"形态，可以删掉 [project.scripts] 整段、[build-system] 整段和 src/ 目录，这样 `uv sync` 就不会构建/安装本地包。不删也没问题。

**重要：别忘了旧 pyproject.toml 里的工具配置。** 本项目旧版 pyproject.toml 里有 pytest、black、mypy 的配置，删掉旧文件后它们也一起丢了。其中最关键的是这一段——没有它，`uv run pytest` 会因为找不到根目录的 `app.py` 而报 `ModuleNotFoundError: No module named 'app'`：

```toml
[tool.pytest.ini_options]
pythonpath = ["."]
```

这段配置的作用是把项目根目录加进 `sys.path`，让 `tests/test_app.py` 里的 `from app import app` 能找到根目录的 `app.py`（uv 运行命令时不会自动把当前目录放进 `sys.path`）。如果旧文件里还有 black / mypy 配置，也一并恢复，否则 CI 里的 `black --check` / `mypy` 行为会变：

```toml
[tool.black]
line-length = 100
target-version = ['py310']
exclude = '''
/(
    \.git
    | venv
    | build
    | dist
)/
'''

[tool.mypy]
python_version = "3.12"
ignore_missing_imports = true
```

### 3.3 第二步：把 requirements.txt 的依赖迁到 pyproject.toml

原 requirements.txt：

```text
flask==3.0.0
gunicorn==21.2.0
pytest==7.4.0
pytest-cov==4.1.0
```

其中 flask 和 gunicorn 是运行应用需要的（生产环境），pytest 和 pytest-cov 是开发和测试用的。uv 把它们分成两组：

```powershell
uv add flask gunicorn
uv add --dev pytest pytest-cov
```

如果希望和原来版本完全一致（保守迁移），显式写版本号：

```powershell
uv add flask==3.0.0 gunicorn==21.2.0
uv add --dev pytest==7.4.0 pytest-cov==4.1.0
```

也可以直接读 requirements.txt 导入：

```powershell
uv add -r requirements.txt
```

（但这样 pytest 会进"运行时依赖"，不推荐，除非之后手动拆分。）

执行后 pyproject.toml 会多出：

```toml
dependencies = [
    "flask>=3.0.0",
    "gunicorn>=21.2.0",
]

[dependency-groups]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
]
```

同时 uv 会立即生成 uv.lock、创建 .venv 并装好依赖。

### 3.4 第三步：同步环境并验证

```powershell
uv sync
uv run pytest
uv run python app.py
```

- `uv sync`：确保 .venv 与声明一致（一般 uv add 已经做过，这步是保险）。
- `uv run pytest`：跑测试（等价于原来激活环境后执行 pytest）。
- `uv run python app.py`：启动 Flask 应用。

测试全部通过、应用能启动，迁移的核心部分就完成了。

### 3.5 第四步：处理 requirements.txt

迁移完成后 requirements.txt 已经没有用处，删除它：

```powershell
Remove-Item requirements.txt
```

如果某些环节（比如外部平台）仍然要求 requirements.txt，可以用 uv 生成一份等价文件：

```powershell
uv export --format requirements.txt
```

但既然用了 uv，主流程就不要手动维护 requirements.txt 了，避免两处依赖不一致。

### 3.6 第五步：更新 Dockerfile

现在的 Dockerfile 还是 pip 流程：

```dockerfile
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
```

改成 uv 流程：

```dockerfile
FROM python:3.12-slim

# 从 uv 官方镜像拷入 uv / uvx 两个可执行文件
COPY --from=ghcr.io/astral-sh/uv:0.12.1 /uv /uvx /bin/

WORKDIR /app

# 先复制依赖声明，依赖没变时能命中 Docker 层缓存
COPY pyproject.toml uv.lock ./

# --frozen：直接用 uv.lock，不重新解析
# --no-dev：生产镜像不装 pytest 等开发依赖
# --no-install-project：不安装本地包（入口是根目录的 app.py）
RUN uv sync --frozen --no-dev --no-install-project

# 再复制全部代码
COPY . .

RUN useradd -m appuser
USER appuser

EXPOSE 5000

CMD ["sh", "-c", "/app/.venv/bin/gunicorn --bind 0.0.0.0:${PORT:-5000} app:app"]
```

同时建议在 .dockerignore 里加上 `.venv/`，避免把本机的 .venv 复制进镜像（现有文件只忽略了 venv/）：

```text
.venv/
```

### 3.7 第六步：更新 CI 工作流

`.github/workflows/ci-cd.yml` 里有两处 pip 用法要改：lint 和 test 两个 job。

公共改动：把 `pip install` 换成 setup-uv + `uv sync --frozen`。

lint job 改成：

```yaml
- name: 检出代码
  uses: actions/checkout@v5

- name: 设置 Python
  uses: actions/setup-python@v6
  with:
    python-version: ${{ env.PYTHON_VERSION }}
    cache: 'uv'

- name: 设置 uv
  uses: astral-sh/setup-uv@v6

- name: 安装依赖（含开发依赖）
  run: uv sync --frozen

- name: 运行 flake8
  run: uv run flake8 .

- name: 运行 black（检查格式）
  run: uv run black --check .

- name: 运行 mypy（类型检查）
  run: uv run mypy . || echo "⚠️ 类型检查有警告"
```

注意：flake8、black、mypy 之前是 CI 里临时 `pip install` 的，现在要变成项目的正式开发依赖：

```powershell
uv add --dev flake8 black mypy
```

test job 的"安装依赖"和"运行测试"改成：

```yaml
- name: 设置 Python ${{ matrix.python-version }}
  uses: actions/setup-python@v6
  with:
    python-version: ${{ matrix.python-version }}
    cache: 'uv'

- name: 设置 uv
  uses: astral-sh/setup-uv@v6

- name: 安装依赖
  run: uv sync --frozen

- name: 运行测试
  run: uv run pytest --cov=app --cov-report=xml --cov-report=html -v
```

**两个坑，务必处理：**

1. **Python 版本矩阵冲突**。pyproject.toml 声明 `requires-python = ">=3.12"`，但 test job 的矩阵是 `['3.9', '3.10', '3.11', '3.12']`。uv 会严格遵守 requires-python，在 3.9/3.10/3.11 上 `uv sync` 会直接失败。二选一：
   - 矩阵改成 `['3.12']`（推荐，与项目声明一致）；
   - 或者把 requires-python 改成 `">=3.9"`（前提是确认代码和依赖都兼容老版本 Python）。

2. **flake8 会扫 .venv**。.flake8 的 exclude 只写了 venv/，没有 .venv/。CI 里 `uv run flake8 .` 可能报出一堆 .venv 里的错误。把 .flake8 改成：

   ```ini
   [flake8]
   max-line-length = 100
   exclude = .git,venv,.venv,__pycache__,build,dist
   ignore = E203, W503
   ```

### 3.8 第七步：提交到 git

提交前先想清楚哪些文件该进版本库：

| 文件 | 是否提交 | 原因 |
| --- | --- | --- |
| pyproject.toml | 是 | 依赖声明 |
| uv.lock | 是 | 锁文件，团队保持一致的关键 |
| .python-version | 是 | 固定 Python 版本 |
| .venv/ | 否 | 本地环境，.gitignore 已忽略 |
| requirements.txt | 删除 | 已由 pyproject.toml 取代 |

命令示例：

```powershell
git rm requirements.txt
git add pyproject.toml uv.lock .python-version .github/workflows/ci-cd.yml Dockerfile .dockerignore .flake8
git commit -m "chore: 使用 uv 替代 pip 管理依赖"
```

### 3.9 迁移完成后的目录

```text
my-flask-app/
├── .github/workflows/ci-cd.yml
├── .python-version          # 3.12
├── .venv/                   # uv 创建的虚拟环境（不提交）
├── Dockerfile               # 已改用 uv
├── pyproject.toml           # 依赖声明
├── uv.lock                  # 锁文件
├── app.py                   # Flask 入口
├── src/my_flask_app/        # uv init 脚手架（可删）
└── tests/                   # 测试
```

## 4. 常见问题（FAQ）

**Q1：uv 下载包太慢 / 想用国内镜像？**

设置环境变量即可，例如清华源：

```powershell
$env:UV_DEFAULT_INDEX = "https://pypi.tuna.tsinghua.edu.cn/simple"
```

之后再执行 uv add / uv sync 就会走该镜像（当前终端有效）。

**Q2：.venv 里没有 pip，正常吗？**

正常。uv 创建的虚拟环境不需要 pip，uv 自己负责安装。想临时用 pip 兼容命令就写 `uv pip ...`。

**Q3：uv run 和 activate 有什么区别？**

activate 是"切换当前终端默认 Python"；uv run 是"只在这条命令里用项目环境"，不污染终端，也不怕忘了激活。

**Q4：uv.lock 合并冲突怎么办？**

最省事的做法：确认 pyproject.toml 合并正确后，删掉 uv.lock，重新执行 `uv sync` 或 `uv lock` 重新生成。

**Q5：控制台里中文显示乱码？**

项目文件本身是 UTF-8，不乱。是 PowerShell 老代码页（GBK）显示问题。用 VS Code 或 Windows Terminal 打开文件，或在 PowerShell 里先执行 `chcp 65001`。不要因此去改文件编码。

**Q6：迁移后还想保留 requirements.txt？**

可以临时用 `uv export --format requirements.txt --no-dev` 生成一份给外部流程用，但日常维护以 pyproject.toml + uv.lock 为准。

**Q7：pip 和 uv 能混用吗？**

过渡期可以（uv pip 兼容 pip 语法），但别长期混用：uv sync 默认会把环境"同步"成声明里的样子，可能会清掉用 pip 手动装的多余包。本项目建议一步到位全用 uv。

## 5. 参考链接

- uv 官方文档：https://docs.astral.sh/uv/
- uv GitHub 仓库：https://github.com/astral-sh/uv
- astral-sh/setup-uv（CI 用）：https://github.com/astral-sh/setup-uv
- uv Docker 镜像：https://github.com/astral-sh/uv/pkgs/container/uv
