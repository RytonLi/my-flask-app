# 零基础教程：把 Flask 服务部署到 Render（代替自建服务器）

> 适用对象：完全没接触过 Render 的新手。
> 学习环境：Windows + Docker Desktop + GitHub（你都已具备）。
> 学完你将能：① 在本地用 Docker 验证这个 Flask 服务；② 说清楚这次的代码改动；③ 在 Render 上免费托管服务；④ 让 GitHub Actions 第四阶段自动触发 Render 部署。

---

## 目录

- [第 0 章 先搞懂三件事](#第-0-章-先搞懂三件事)
- [第 1 章 本地验证（Windows）](#第-1-章-本地验证windows)
- [第 2 章 这次改了什么代码](#第-2-章-这次改了什么代码)
- [第 3 章 Render 注册与创建服务（一次性手动步骤）](#第-3-章-render-注册与创建服务一次性手动步骤)
- [第 4 章 配置 GitHub Secrets（一次性手动步骤）](#第-4-章-配置-github-secrets一次性手动步骤)
- [第 5 章 提交到 GitHub 验证（由你手动执行）](#第-5-章-提交到-github-验证由你手动执行)
- [第 6 章 以后每次更新代码的流程](#第-6-章-以后每次更新代码的流程)
- [第 7 章 常见问题排查](#第-7-章-常见问题排查)
- [附录 费用与免费额度说明](#附录-费用与免费额度说明)

---

## 第 0 章 先搞懂三件事

### 0.1 为什么第四阶段会失败

原来的 `ci-cd.yml` 第四阶段用 SSH 登录一台服务器，然后执行 `docker pull`、`docker run`。
你没有服务器，GitHub Actions 自然连不上，所以这一阶段必然失败：

```text
github.ref == 'refs/heads/main'
        ↓
SSH 连接 your-server.com  →  连不上 → 第四阶段失败 ❌
```

### 0.2 Render 是什么

Render 是一家云平台公司，它替你提供了"服务器"。你的代码推到 GitHub 后，Render 会：

1. 读取你仓库里的 `Dockerfile`，自动构建 Docker 镜像（你不需要把镜像手动传给它）；
2. 在它的服务器上运行这个镜像；
3. 给你一个公网地址，例如 `https://my-flask-app.onrender.com`。

你不需要购买服务器、不需要懂 SSH，只需要在 Render 网站上点几次鼠标，把 GitHub 仓库和 Render 连起来。

### 0.3 本教程的整体流程

```text
你在本地改代码并验证（第 1 章，已帮你跑通）
        ↓
提交改动到 GitHub（第 5 章，你手动执行）
        ↓
GitHub Actions 自动执行：lint → test → build → deploy
        ↓
deploy 阶段向 Render 的 Deploy Hook 发一个请求（第 4 章配置好之后）
        ↓
Render 读取仓库里的 Dockerfile，构建并运行服务
        ↓
你通过 https://my-flask-app.onrender.com 访问服务
```

---

## 第 1 章 本地验证（Windows）

> 本教程对应的代码改动我已经在本机完整验证过一遍，下面的命令照抄即可复现。

### 1.1 前提

- Docker Desktop 已启动（任务栏右下角鲸鱼图标处于运行状态）。
- PowerShell 打开在项目根目录 `D:\itheima\02_git+CICD\my-flask-app`。

### 1.2 构建镜像

```powershell
docker build -t my-flask-app .
```

`-t my-flask-app` 是给镜像起名字，末尾的 `.` 表示使用当前目录的 `Dockerfile`。
看到 `naming to docker.io/library/my-flask-app:latest done` 即构建成功。

### 1.3 运行容器

```powershell
docker run -d --name my-flask-app -p 5000:5000 my-flask-app
```

含义：`-d` 后台运行；`--name my-flask-app` 给容器起名；`-p 5000:5000` 把本机 5000 端口映射到容器 5000 端口。

### 1.4 访问接口

> Windows PowerShell 里要用 `curl.exe`，直接写 `curl` 会被当成别的命令。

```powershell
curl.exe http://localhost:5000/
curl.exe http://localhost:5000/health
curl.exe http://localhost:5000/api/time
curl.exe http://localhost:5000/greet/Codex
curl.exe http://localhost:5000/version
```

实测结果：

| 接口 | 返回 |
| --- | --- |
| `/` | `{"message":"Hello, CI/CD!"}` |
| `/health` | `{"status":"healthy"}` |
| `/api/time` | `{"current_time":"2026-08-04T03:22:13..."}` |
| `/greet/Codex` | `{"message":"Hello, Codex!"}` |
| `/version` | `{"version":"1.0.0"}` |

### 1.5 模拟 Render 的端口行为（重点）

Render 会给服务注入一个环境变量 `PORT`（默认值是 `10000`），要求服务监听 `0.0.0.0:10000`。
修改后的 Dockerfile 支持这个变量。下面用 `-e PORT=10000` 模拟：

```powershell
docker run -d --name my-flask-app-port -p 10001:10000 -e PORT=10000 my-flask-app
curl.exe http://localhost:10001/health
```

实测返回 `{"status":"healthy"}`，且容器日志显示 `Listening at: http://0.0.0.0:10000`，
说明服务在 Render 上也能正确监听。

### 1.6 验证完清理

```powershell
docker stop my-flask-app my-flask-app-port
docker rm my-flask-app my-flask-app-port
```

---

## 第 2 章 这次改了什么代码

只改了 3 个文件，新增 1 个文档，共涉及 3 处改动：

| 文件 | 改动 | 为什么 |
| --- | --- | --- |
| `Dockerfile` | 启动命令改为监听 `$PORT` | Render 默认要求服务监听端口 10000（由环境变量 `PORT` 指定） |
| `render.yaml` | 新增 | 告诉 Render 创建什么样的服务，这是 Render 的"蓝图"配置 |
| `.github/workflows/ci-cd.yml` | 第四阶段由 SSH 改为 Deploy Hook | 不再需要自己的服务器 |

### 2.1 Dockerfile 改动

```dockerfile
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-5000} app:app"]
```

- `${PORT:-5000}` 的意思是：如果环境变量 `PORT` 存在就用它，否则用 5000。
- 本地运行时没有 `PORT`，所以照旧监听 5000，`docker run -p 5000:5000` 不受影响；
- Render 运行时注入 `PORT=10000`，gunicorn 自动改监听 10000。

### 2.2 render.yaml（新增）

这是 Render 的 Blueprint（基础设施即代码）。Render 靠它知道你想要的服务的全部配置：

| 字段 | 值 | 含义 |
| --- | --- | --- |
| `type` | `web` | 对外提供 HTTP 访问的 Web 服务 |
| `name` | `my-flask-app` | 服务名，会出现在网址里 |
| `runtime` | `docker` | 用仓库里的 Dockerfile 构建镜像 |
| `plan` | `free` | 免费实例 |
| `region` | `singapore` | 部署区域，离国内相对近 |
| `branch` | `main` | 监听 main 分支 |
| `healthCheckPath` | `/health` | Render 用它检查服务是否健康 |
| `autoDeployTrigger` | `"off"` | 关闭"push 即自动部署"，改由 GitHub Actions 触发，避免重复部署 |

### 2.3 ci-cd.yml 第四阶段改动

删掉了 SSH 部署，换成一个 HTTP 请求：

```yaml
deploy:
  name: 部署到 Render
  runs-on: ubuntu-latest
  needs: [build]
  if: github.ref == 'refs/heads/main'
  environment:
    name: production
    url: https://my-flask-app.onrender.com

  steps:
    - name: 触发 Render 部署
      env:
        RENDER_DEPLOY_HOOK_URL: ${{ secrets.RENDER_DEPLOY_HOOK_URL }}
      run: |
        curl --fail "$RENDER_DEPLOY_HOOK_URL"
```

- `RENDER_DEPLOY_HOOK_URL` 是一个 GitHub Secret（第 4 章配置），值是 Render 生成的秘密网址；
- 向这个网址发一个 GET 请求，Render 就开始构建并部署；
- 前三阶段（lint / test / build）全部通过后才会执行本阶段，保证"代码没问题才上线"。

---

## 第 3 章 Render 注册与创建服务（一次性手动步骤）

> 接下来的操作只在第一次做一次。之后每次 push 都会自动走完整个流程。

### 3.1 注册账号

1. 打开 <https://render.com>；
2. 点击 **Sign up**，推荐选择 **Continue with GitHub**（后面连接仓库最省事）；
3. 按提示完成注册（可能要求手机验证码，正常填写即可）。

### 3.2 连接 GitHub

注册后 Render 会引导你连接 GitHub：授权 Render 安装一个 GitHub App，并允许它访问你的仓库。
如果没看到授权页面，进入 Dashboard 后点 **New +**，选择 **Blueprint Instance** 时也会提示连接。

### 3.3 创建 Blueprint Instance（推荐方式）

1. 打开 Render Dashboard：<https://dashboard.render.com>；
2. 点击右上角 **New +** → **Blueprint Instance**；
3. 选择你的仓库 `RytonLi/my-flask-app`（如果没有，先按提示给 Render 授权该仓库）；
4. Render 会自动读取仓库根目录的 `render.yaml`，并显示将要创建的服务：

```text
my-flask-app  (Web Service, Docker, Free, Singapore)
```

5. 确认无误后点击 **Apply**（有的界面叫 **Create Blueprint**）。

### 3.4 首次部署

1. 创建完成后，进入该服务（点服务名进入服务页）；
2. 如果页面显示 **Not deployed** 或提示尚未部署，点击右上角 **Deploy** 按钮手动触发首次部署；
3. 在 **Events** 标签页查看构建进度，首次构建一般需要 2～5 分钟；
4. 构建完成后在 **Logs** 标签页应该能看到：

```text
Listening at: http://0.0.0.0:10000
```

### 3.5 记录服务地址

服务页顶部会显示公网地址，形如：

```text
https://my-flask-app.onrender.com
```

> 如果这个名字已被别人占用，Render 会自动加随机后缀（例如 `my-flask-app-ab12.onrender.com`），以控制台显示的地址为准。

### 3.6 备选方式：手动创建 Web Service（不想用 render.yaml 也可以）

1. Dashboard → **New +** → **Web Service**；
2. 选择仓库 `RytonLi/my-flask-app`，分支 `main`；
3. 环境选择 **Docker**（Render 会自动识别根目录的 Dockerfile）；
4. 实例类型选 **Free**，区域选 **Singapore**；
5. 高级设置里把 **Health Check Path** 填成 `/health`；
6. 点击 **Create Web Service**。

这种方式不依赖 `render.yaml`，但每次修改服务配置都要在网页上手动改，所以本教程默认用 Blueprint 方式。

---

## 第 4 章 配置 GitHub Secrets（一次性手动步骤）

GitHub Actions 需要一个秘密值 `RENDER_DEPLOY_HOOK_URL`，用来触发 Render 部署。

### 4.1 在 Render 里复制 Deploy Hook 地址

1. 进入你的服务页 → **Settings**（设置）；
2. 找到 **Deploy Hook** 一栏；
3. 点击复制按钮，得到一串形如下面的网址：

```text
https://api.render.com/deploy/srv-xxxxxxxx?key=yyyyyyyy
```

> 这串网址相当于你服务的"启动钥匙"，务必保密，不要提交到代码里或发到公开渠道。

### 4.2 在 GitHub 里添加 Secret

1. 打开你的 GitHub 仓库页面；
2. **Settings** → 左侧 **Secrets and variables** → **Actions**；
3. 点击 **New repository secret**：
   - Name：`RENDER_DEPLOY_HOOK_URL`
   - Secret：粘贴上面复制的网址
4. 点击 **Add secret**。

仓库里已有的 `DOCKER_USERNAME`、`DOCKER_PASSWORD` 不用动（第三阶段构建镜像仍在用）。

---

## 第 5 章 提交到 GitHub 验证（由你手动执行）

### 5.1 提交并推送

在项目根目录打开 PowerShell，执行：

```powershell
git add Dockerfile render.yaml .github/workflows/ci-cd.yml RENDER_DEPLOY.md
git commit -m "ci: 第四阶段改为部署到 Render"
git push origin main
```

### 5.2 观察 GitHub Actions

1. 打开仓库 → **Actions** 标签页；
2. 看到最新一次运行包含 4 个阶段：`代码检查` → `单元测试` → `构建 Docker 镜像` → `部署到 Render`；
3. 前三个阶段应该全部通过，第四个阶段应该显示绿色（它只是向 Render 发了一个请求）。

### 5.3 观察 Render 部署

1. 打开 <https://dashboard.render.com>，进入 `my-flask-app` 服务；
2. 在 **Events** 里能看到一次新的部署记录（由 Deploy Hook 触发）；
3. 等状态变成 **Live**。

### 5.4 验证线上服务

在浏览器或 PowerShell 里访问：

```powershell
curl.exe https://my-flask-app.onrender.com/health
curl.exe https://my-flask-app.onrender.com/
```

返回 `{"status":"healthy"}` 和 `{"message":"Hello, CI/CD!"}` 即部署成功。

---

## 第 6 章 以后每次更新代码的流程

以后你只需要：

```powershell
git add .
git commit -m "你的修改说明"
git push origin main
```

剩下的全部自动完成：Actions 跑检查 → 触发 Render → 新版本上线。

---

## 第 7 章 常见问题排查

| 现象 | 原因与解决办法 |
| --- | --- |
| Actions 第四阶段报 `401` / `404` | Deploy Hook 地址不对或已重新生成。回到 Render 服务 Settings 重新复制，更新 GitHub Secret。 |
| Render 构建失败 | 打开服务页 **Events** / **Logs** 看报错。常见：`pip install` 依赖下载失败（网络原因，重试即可）、Dockerfile 路径不对。 |
| 服务反复重启 | 健康检查不过。确认日志里 gunicorn 监听在 `0.0.0.0:10000`，并访问 `/health` 是否返回 200。 |
| 服务一直处于 `Not deployed` | `render.yaml` 里关了自动部署，首次需要手动点一次 **Deploy**。之后都由 Actions 触发。 |
| 免费实例访问很慢 | 免费实例 15 分钟无请求会休眠，下次访问要等几十秒唤醒。这是免费额度的正常现象。 |
| 从国内访问不稳定 | `onrender.com` 没有国内节点，这是平台限制。本教程已选新加坡区域，相对稍好。 |
| 想 push 后不经过 Actions 直接自动部署 | 把 `render.yaml` 的 `autoDeployTrigger` 改成 `commit`，然后删掉 workflow 里的 deploy 阶段（否则会重复部署）。 |
| 第三阶段（Docker Hub）能删吗 | 能。Render 直接读 Dockerfile 构建，不依赖 Docker Hub。想简化就把 build 阶段删掉，并把 deploy 的 `needs` 改成 `[test]`。 |
| 本地 `curl` 报错 | Windows PowerShell 里用 `curl.exe`，不要用 `curl`（它被系统别名成别的命令）。 |

---

## 附录 费用与免费额度说明

- Render 免费 Web Service 不需要付费，注册时一般也不需要绑定信用卡；
- 免费额度：每月约 750 小时运行时长（一个实例 24 小时全开约等于 720 小时/月，够用）、15 分钟无请求自动休眠、无持久化磁盘；
- 本项目是无状态 Flask 服务，完全适合免费实例；如果以后需要数据库或定时任务，再按需升级；
- 如果注册时系统要求绑定支付方式，通常是因为选了付费实例，改回 **Free** 即可。

---

> 本教程对应的代码改动已在本机验证通过（第 1 章），接下来按第 5 章提交到 GitHub 即可。
