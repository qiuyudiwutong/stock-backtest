# GitHub 推送指南

## 📤 推送到 GitHub

当前项目已在本地完成 Git 初始化，需要推送到 GitHub 仓库。

### 方法 1: 使用 SSH（推荐）

#### 步骤 1: 生成 SSH 密钥（如果没有）

```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
# 按提示操作，一般直接回车即可
```

#### 步骤 2: 添加 SSH 密钥到 GitHub

1. 复制公钥内容：
   ```bash
   cat ~/.ssh/id_ed25519.pub
   ```

2. 打开 GitHub → Settings → SSH and GPG keys → New SSH key
3. 粘贴公钥内容，保存

#### 步骤 3: 创建 GitHub 仓库

1. 打开 https://github.com/new
2. 仓库名：`stock-backtest`
3. 设为 Public 或 Private
4. **不要**勾选 "Initialize this repository with a README"
5. 点击 Create repository

#### 步骤 4: 推送代码

```bash
cd /root/.openclaw/workspace/stock-backtest

# 添加远程仓库（替换为你的 GitHub 用户名）
git remote add origin git@github.com:YOUR_USERNAME/stock-backtest.git

# 推送
git branch -M main
git push -u origin main
```

---

### 方法 2: 使用 HTTPS + Token

#### 步骤 1: 创建 Personal Access Token

1. 打开 https://github.com/settings/tokens
2. 点击 "Generate new token (classic)"
3. 勾选 `repo` 权限
4. 生成并复制 Token

#### 步骤 2: 推送代码

```bash
cd /root/.openclaw/workspace/stock-backtest

# 添加远程仓库（替换为你的 GitHub 用户名和 Token）
git remote add origin https://YOUR_USERNAME:YOUR_TOKEN@github.com/YOUR_USERNAME/stock-backtest.git

# 推送
git branch -M main
git push -u origin main
```

---

### 方法 3: 手动上传（无需 Git）

1. 下载项目为 ZIP
2. 在 GitHub 创建新仓库
3. 解压后上传所有文件

---

## 🔗 项目信息

- **项目 ID**: `stock-backtest-v1`
- **建议仓库名**: `stock-backtest`
- **描述**: 轻量级股票策略回测系统（参考 backtrader/vnpy/zipline）

---

## ✅ 推送后验证

推送完成后，访问你的 GitHub 仓库确认：

- [ ] 所有代码文件已上传
- [ ] README.md 显示正常
- [ ] 可以在线查看代码

---

## 🔄 后续更新

```bash
# 修改代码后
git add -A
git commit -m "添加新功能：XXX"
git push
```
