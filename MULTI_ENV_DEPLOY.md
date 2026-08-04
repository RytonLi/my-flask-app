# 多环境部署指南：GitHub Environments + Render（dev → staging，main → production）

> 适用对象：已经跑通"本地提交 → GitHub Actions 自动测试/构建 → 部署到 Render"的 `RytonLi/my-flask-app` 项目。
> 学习目标：模拟真实项目的多环境部署——`dev` 分支对应测试环境（staging），`main` 分支对应生产环境（production），两个环境都部署到 Render，但互不干扰。

---

## 0. 目标与整体架构

改造完成后，流程如下：

```text
本地开发
   │
   ├─ git push origin dev   ──> Actions: lint → test → build ──> 部署到 Render 的 staging 服务
   │                              （只跑 staging，production 不受影响）
   │
   └─ merge dev 到 main（即 push main）─> Actions: lint → test → build ──> 部署到 Render 的 production 服务
                                          （只跑 production，staging 不受影响）
```

| 分支 | GitHub 环境 | Render 服务 | 用途 |
| --- | --- | --- | --- |
| `dev` | `staging` | `my-flask-app-staging` | 测试环境，日常提交直接部署 |
| `main` | `production` | `my-flask-app`（现有） | 生产环境，稳定代码才上线 |

核心思路：

- GitHub **环境（Environment）** 是一套独立的配置空间：每个环境可以有自己的 **secrets**、部署分支限制、人工审批规则，还能在 Actions 页面看到"环境部署记录"。
- 工作流里给 `deploy` 任务声明 `environment: staging` 或 `environment: production`，任务里的 `${{ secrets.RENDER_DEPLOY_HOOK_URL }}` 就会自动解析成**对应环境**里的 secret，从而实现"同一个 secret 名字、不同的值"。
- Render 上创建两个 Web 服务，分别监听 `dev` 和 `main` 分支，都关闭自动部署，统一由 GitHub Actions 的 Deploy Hook 触发（和现在完全一致的触发方式）。

---

## 1. 新建 dev 分支

在项目根目录打开 PowerShell，执行：

```powershell
git checkout -b dev
git push -u origin dev
```

验证：

```powershell
git branch -a
```

应能看到本地和远程都有 `dev`。后续你的日常开发就在 `dev` 分支上进行，`main` 分支只接受经过验证的合并。

---

## 2. 在 Render 创建 staging 服务

测试环境仍采用 Render。有两种方式，推荐 **方案 A（Blueprint）**，与现有 `render.yaml` 管理方式保持一致。

> ⚠️ 前提：第 1 步的 `dev` 分支必须已经推送到 GitHub，因为 staging 服务要从 `dev` 分支构建代码。

### 方案 A：通过 render.yaml（Blueprint）新增服务

1. 编辑仓库根目录的 `render.yaml`，在 `services` 列表里追加第二个服务（完整内容见第 4 章，直接复制替换即可）。
2. 提交并推送到 `main`：

```powershell
git checkout main
git add render.yaml
git commit -m "ci: 新增 staging 服务配置"
git push origin main
```

3. 打开 <https://dashboard.render.com>，进入你的 **Blueprint** 实例页面。
4. 点击 **Sync**（同步）按钮。Render 会读取最新的 `render.yaml`，发现多了一个服务，自动创建 `my-flask-app-staging`。
5. 等服务创建完成后，进入该服务页面，确认 **Events / Logs** 里构建成功。

### 方案 B：手动创建 Web Service（不想动 render.yaml 时）

1. 打开 <https://dashboard.render.com>，点击 **New +** → **Web Service**。
2. 选择仓库 `RytonLi/my-flask-app`，分支选 **`dev`**。
3. 环境选 **Docker**（Render 会自动识别根目录的 Dockerfile）。
4. 实例类型选 **Free**，区域选 **Singapore**。
5. 高级设置里把 **Health Check Path** 填成 `/health`。
6. 点击 **Create Web Service**，等待首次构建完成。

> 方案 B 的缺点：以后服务配置改动只能手动在网页上改，`render.yaml` 里看不到测试环境。学习阶段两者都可以，本指南默认按方案 A 讲解。

### 复制 staging 服务的 Deploy Hook

1. 进入 `my-flask-app-staging` 服务页面。
2. 点 **Settings**，找到 **Deploy Hook** 一栏。
3. 点击复制按钮，得到一串形如 `https://api.render.com/deploy/srv-xxxxxxxx?key=yyyyyyyy` 的地址。
4. 记下这个地址，第 3 章要用。同时记下服务页顶部的公网地址（形如 `https://my-flask-app-staging.onrender.com`，如果名字被占用会自动加随机后缀），第 5 章配置 `url` 要用。

> 现有 production 服务的 Deploy Hook 不用动。如果之前没有记录，也可以到 `my-flask-app` 服务 → Settings → Deploy Hook 再复制一次。

---

## 3. 在 GitHub 创建 staging 和 production 两个环境并配置 secrets

### 3.1 创建环境

1. 打开 GitHub 仓库页面 → **Settings** → 左侧 **Environments**。
2. 点击 **New environment**，名字填 `staging`，创建。
3. 重复一次，创建 `production`。

> 说明：之前的工作流已经在用 `environment: production`，这个环境可能已经存在；如果已存在，直接进入配置即可。

### 3.2 给每个环境配置 RENDER_DEPLOY_HOOK_URL

进入 `staging` 环境页面：

1. 找到 **Environment secrets** → 点击 **Add secret**。
2. Name 填 `RENDER_DEPLOY_HOOK_URL`，Value 粘贴 **staging 服务**的 Deploy Hook 地址。
3. 保存。

进入 `production` 环境页面，做同样操作，Value 粘贴 **production 服务**的 Deploy Hook 地址。

效果：

| 位置 | secret 名字 | 值 |
| --- | --- | --- |
| staging 环境 | `RENDER_DEPLOY_HOOK_URL` | staging 服务的 Deploy Hook |
| production 环境 | `RENDER_DEPLOY_HOOK_URL` | production 服务的 Deploy Hook |
| 仓库级（原有，保留不动） | `RENDER_DEPLOY_HOOK_URL` | 原值（备用，优先级低于环境级） |

> 优先级规则：**环境 secrets > 组织 secrets > 仓库 secrets**。当某个任务声明了 `environment: staging`，`${{ secrets.RENDER_DEPLOY_HOOK_URL }}` 会优先取 staging 环境里的值。仓库级的 `DOCKER_USERNAME`、`DOCKER_PASSWORD` 与部署无关，保持仓库级即可。

### 3.3 （推荐）设置部署分支保护

在环境页面找到 **Deployment branches**：

- `staging` 环境：选择 **Selected branches**，填 `dev`。
- `production` 环境：选择 **Selected branches**，填 `main`。

这样即使工作流写错，GitHub 也会拒绝把非指定分支的代码部署到对应环境，等于多了一层保险。

（可选）如果还想模拟真实团队流程，可以给 `production` 环境开启 **Required reviewers**，这样每次生产部署都需要人工审批后才真正触发。

---

## 4. 更新 render.yaml：定义两个服务

把 `render.yaml` 整体替换为下面内容（注释可按需保留或删减）：

```yaml
# Render Blueprint（基础设施即代码）
# 包含两个 Web 服务：
#   my-flask-app          -> 生产环境，监听 main 分支
#   my-flask-app-staging  -> 测试环境，监听 dev 分支
# 两个服务都关闭自动部署，统一由 GitHub Actions 的 Deploy Hook 触发。
services:
  - type: web
    name: my-flask-app
    runtime: docker
    plan: free
    region: singapore
    branch: main
    healthCheckPath: /health
    autoDeployTrigger: "off"

  - type: web
    name: my-flask-app-staging
    runtime: docker
    plan: free
    region: singapore
    branch: dev
    healthCheckPath: /health
    autoDeployTrigger: "off"
```

改动点只有一处：新增了一个 `name` 为 `my-flask-app-staging`、`branch` 为 `dev` 的服务。两个服务都保持 `autoDeployTrigger: "off"`，避免 Render 和 GitHub Actions 双重触发。

---

## 5. 更新 CI/CD 工作流：按分支部署到对应环境

把 `.github/workflows/ci-cd.yml` 整体替换为下面内容：

```yaml
name: Python 项目 CI/CD

on:
  push:
    branches: [ main, dev ]
  pull_request:
    branches: [ main, dev ]

env:
  PYTHON_VERSION: '3.12'

jobs:
  # ========== 第一阶段：代码检查（main / dev 都执行）==========
  lint:
    name: 代码检查
    runs-on: ubuntu-latest

    steps:
      - name: 检出代码
        uses: actions/checkout@v5

      - name: 设置 Python
        uses: actions/setup-python@v6
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: 设置 uv
        uses: astral-sh/setup-uv@v9.0.0
        with:
          enable-cache: true

      - name: 安装依赖（含开发依赖）
        run: uv sync --frozen

      - name: 运行 Ruff（代码检查）
        run: uv run ruff check .

      - name: 运行 mypy（类型检查）
        run: uv run mypy . || echo "⚠️ 类型检查有警告"

  # ========== 第二阶段：单元测试（main / dev 都执行）==========
  test:
    name: 单元测试
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.12']

    steps:
      - name: 检出代码
        uses: actions/checkout@v5

      - name: 设置 Python ${{ matrix.python-version }}
        uses: actions/setup-python@v6
        with:
          python-version: ${{ matrix.python-version }}

      - name: 设置 uv
        uses: astral-sh/setup-uv@v9.0.0
        with:
          enable-cache: true

      - name: 安装依赖
        run: uv sync --frozen

      - name: 运行测试
        run: uv run pytest --cov=app --cov-report=xml --cov-report=html -v

      - name: 上传覆盖率报告
        uses: codecov/codecov-action@v5
        with:
          files: ./coverage.xml
          fail_ci_if_error: false

      - name: 上传 HTML 覆盖率报告
        uses: actions/upload-artifact@v6
        if: always()
        with:
          name: coverage-report-${{ matrix.python-version }}
          path: htmlcov/

  # ========== 第三阶段：构建 Docker 镜像（main / dev 的 push 都构建）==========
  build:
    name: 构建 Docker 镜像
    runs-on: ubuntu-latest
    needs: [lint, test]
    # 只有 push 才构建；PR 只做 lint/test，不构建不部署
    if: github.event_name == 'push'

    steps:
      - name: 检出代码
        uses: actions/checkout@v5

      - name: 设置 Docker Buildx
        uses: docker/setup-buildx-action@v4

      - name: 登录 Docker Hub
        uses: docker/login-action@v4
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}

      - name: 构建并推送 Docker 镜像
        uses: docker/build-push-action@v7
        with:
          context: .
          push: true
          tags: |
            ${{ secrets.DOCKER_USERNAME }}/my-flask-app:latest
          cache-from: type=registry,ref=${{ secrets.DOCKER_USERNAME }}/my-flask-app:buildcache
          cache-to: type=registry,ref=${{ secrets.DOCKER_USERNAME }}/my-flask-app:buildcache,mode=max

  # ========== 第四阶段：部署到 Render（多环境）==========
  # dev 分支 -> staging 环境；main 分支 -> production 环境
  # 两个任务各自声明 environment，从而读取对应环境的 RENDER_DEPLOY_HOOK_URL

  deploy-staging:
    name: 部署到 Render（staging）
    runs-on: ubuntu-latest
    needs: [build]
    if: github.event_name == 'push' && github.ref_name == 'dev'
    environment:
      name: staging
      # 换成 Render 控制台里 staging 服务的实际地址
      url: https://my-flask-app-staging.onrender.com

    steps:
      - name: 触发 Render 部署
        env:
          RENDER_DEPLOY_HOOK_URL: ${{ secrets.RENDER_DEPLOY_HOOK_URL }}
        run: |
          curl --fail "$RENDER_DEPLOY_HOOK_URL"

      - name: 提示查看部署进度
        run: |
          echo "已触发 staging 部署，请到 Render Dashboard 查看 Events 和日志："
          echo "https://dashboard.render.com"
          echo "部署完成后访问：https://my-flask-app-staging.onrender.com/health"

  deploy-production:
    name: 部署到 Render（production）
    runs-on: ubuntu-latest
    needs: [build]
    if: github.event_name == 'push' && github.ref_name == 'main'
    environment:
      name: production
      url: https://my-flask-app-iy7n.onrender.com

    steps:
      - name: 触发 Render 部署
        env:
          RENDER_DEPLOY_HOOK_URL: ${{ secrets.RENDER_DEPLOY_HOOK_URL }}
        run: |
          curl --fail "$RENDER_DEPLOY_HOOK_URL"

      - name: 提示查看部署进度
        run: |
          echo "已触发 production 部署，请到 Render Dashboard 查看 Events 和日志："
          echo "https://dashboard.render.com"
          echo "部署完成后访问：https://my-flask-app-iy7n.onrender.com/health"
```

和原来相比，只改了 4 处：

1. **触发分支**：`push` 和 `pull_request` 的分支从 `[main]` 扩成 `[main, dev]`。
2. **build 任务**：条件从 `github.ref == 'refs/heads/main'` 改成 `github.event_name == 'push'`，让 `main` 和 `dev` 的推送都构建镜像；PR 不构建。
3. **deploy 任务拆成两个**：`deploy-staging` 和 `deploy-production`，各自用 `if` 判断分支，各自声明 `environment`。
4. **secrets 自动分流**：因为每个任务声明了不同的 `environment`，同一个 `${{ secrets.RENDER_DEPLOY_HOOK_URL }}` 会分别读到 staging / production 环境的 secret，代码里不需要任何分支判断。

> 小提示：`deploy-staging` 里的 `url` 是占位地址，如果 Render 分配的实际地址带了随机后缀（例如 `my-flask-app-staging-xxxx.onrender.com`），记得改成实际地址。

---

## 6. 提交并验证

### 6.1 推送 dev，验证 staging 部署

```powershell
git checkout dev
git add .
git commit -m "ci: 支持多环境部署"
git push origin dev
```

1. 打开 GitHub 仓库 → **Actions**，应看到一次运行，包含：`代码检查` → `单元测试` → `构建 Docker 镜像` → `部署到 Render（staging）`，且只有 staging 部署任务出现。
2. 打开 <https://dashboard.render.com>，进入 `my-flask-app-staging`，在 **Events** 里应看到一次由 Deploy Hook 触发的新部署，状态变为 **Live**。
3. 访问 `https://my-flask-app-staging.onrender.com/health`，应返回 `{"status":"healthy"}`。
4. 同时确认 `my-flask-app`（production）的 Events 没有任何新部署——两个环境互不影响。

### 6.2 合并到 main，验证 production 部署

模拟一次正式发版：把 `dev` 合并进 `main` 并推送。

```powershell
git checkout main
git merge dev
git push origin main
```

1. Actions 里应出现新运行，部署任务显示为 `部署到 Render（production）`。
2. Render 的 `my-flask-app` 服务出现新部署，状态变 **Live**。
3. 访问 `https://my-flask-app-iy7n.onrender.com/health` 验证生产环境。
4. 在 GitHub **Actions 页面 → 左侧 Environment**（或仓库首页右侧的 Environments 卡片），能看到 `staging` / `production` 各自的部署历史和当前部署的 commit。

### 6.3 以后日常流程

```powershell
# 日常开发：提交到 dev，自动部署测试环境
git checkout dev
git add .
git commit -m "你的修改说明"
git push origin dev

# 验证通过后：合并到 main，自动部署生产环境
git checkout main
git merge dev
git push origin main
```

---

## 7. 常见问题与注意事项

| 现象 / 问题 | 说明与处理 |
| --- | --- |
| 免费额度不够 | Render 免费版**所有免费实例共享每月约 750 小时**。两个免费服务 24 小时全开会超额度，月底可能被暂停或休眠。学习项目影响不大；如果想长期跑两个环境，建议其中一个升级到付费（如 `starter`）。 |
| Deploy Hook 报 `401` / `404` | Hook 地址失效或复制错服务了。回到对应 Render 服务 → Settings → Deploy Hook 重新复制，更新到对应 GitHub 环境的 secret。 |
| 部署到了错误的环境 | 检查任务 `if` 里的分支判断，以及环境页面的 **Deployment branches** 限制是否配置正确。 |
| 环境 secret 没生效 | 确认任务声明了 `environment:`，且 secret 加在**该环境**下而不是仓库级。环境级优先级更高，同名时以环境级为准。 |
| 修改 render.yaml 后没看到新服务 | Blueprint 需要手动点 **Sync**（同步），且 render.yaml 要推送在 Blueprint 监听的分支（默认 main）上。 |
| 中文字符乱码 | 用 VS Code 编辑 `.yml` 文件，保存编码选 **UTF-8**（现有文件本身就是 UTF-8）。 |
| dev 推送也往 Docker Hub 推了 `latest` | 当前 Render 直接从仓库 Dockerfile 构建，不依赖 Docker Hub 镜像，所以不影响部署。如果以后想让 staging 和生产镜像分开，可以把 build 阶段按分支打不同 tag（如 `:dev` 和 `:latest`）。 |
| 想要生产环境人工审批 | 在 GitHub `production` 环境页面开启 **Required reviewers**，之后每次生产部署会先等待审批。 |

---

## 8. 下一步建议

- 把 `dev` 设为仓库默认分支，团队直接在 `dev` 上开发、通过 PR 合并到 `main`。
- 给 `production` 环境加上人工审批，模拟真实发布流程。
- 在 `staging` 环境跑一轮"上线前检查"（例如把 lint/test 也复制到 staging 环境做冒烟测试），再合并到 `main`。
