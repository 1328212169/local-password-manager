# GitHub 上传指南 - 密码管理器 v1.2.4

## 📋 当前状态

✅ Git仓库已初始化并关联远程仓库  
✅ 仓库地址：https://github.com/1328212169/local-password-manager  
✅ 当前版本：v1.2.4（2026-10-29）  

---

## 🚀 上传到GitHub的步骤

### 方法一：使用命令行（推荐）

#### 第1步：在GitHub上创建新仓库

1. 访问 https://github.com/new
2. 填写仓库信息：
   - **Repository name**: `password-manager`（或其他你喜欢的名字）
   - **Description**: `本地密码管理工具，支持AES-256-GCM加密、悬浮窗口快速访问、批量导入导出等功能`
   - **Visibility**: 选择 Public（公开）或 Private（私有）
   - ⚠️ **不要**勾选 "Initialize this repository with a README"
3. 点击 "Create repository"

#### 第2步：配置Git用户信息（如果还没配置）

```bash
git config --global user.name "你的GitHub用户名"
git config --global user.email "你的邮箱@example.com"
```

#### 第3步：关联远程仓库并推送

创建完仓库后，GitHub会显示类似这样的命令：

```bash
# 添加远程仓库（替换为你的仓库地址）
git remote add origin https://github.com/你的用户名/仓库名.git

# 推送到GitHub
git branch -M main
git push -u origin main
```

**完整示例：**
```bash
cd "d:\03_成品库\软件成品\密码管理器开发\密码管理器"
git remote add origin https://github.com/1328212169/local-password-manager.git
git branch -M main
git push -u origin main
```

系统会提示你输入GitHub的用户名和密码（或使用Personal Access Token）。

---

### 方法二：使用GitHub Desktop（图形界面）

如果你不熟悉命令行，可以使用GitHub Desktop：

1. **下载GitHub Desktop**
   - 访问: https://desktop.github.com/
   - 下载并安装

2. **添加现有仓库**
   - 打开GitHub Desktop
   - 点击 "File" → "Add Local Repository"
   - 选择目录: `d:\03_成品库\软件成品\密码管理器开发\密码管理器`
   - 点击 "Add Repository"

3. **发布到GitHub**
   - 点击右上角的 "Publish repository" 按钮
   - 填写仓库名称和描述
   - 选择公开或私有
   - 点击 "Publish Repository"

---

## 📁 上传的文件清单

### ✅ 核心源代码（11个文件）
- `main.py` - 主程序入口
- `main_window.py` - 主窗口界面
- `floating_window.py` - 悬浮窗口
- `about_dialog.py` - 关于对话框与更新检查（v1.2.4新增）
- `crypto.py` - 加密模块
- `batch_importer.py` - 批量导入功能
- `password_generator.py` - 密码生成器
- `settings_dialog.py` - 设置对话框
- `txt_converter.py` - TXT转换工具
- `build.bat` - 打包脚本
- `version_info.txt` - exe版本信息

### ✅ 配置与文档文件
- `requirements.txt` - Python依赖包
- `.gitignore` - Git忽略规则
- `密码管理器.spec` - PyInstaller配置
- `README.md` - 项目说明
- `CHANGELOG.md` - 更新日志
- `LICENSE` - 开源许可证
- `发布说明.txt` - 版本发布说明

### ❌ 不会上传的文件（已在.gitignore中排除）
- `dist/`、`build/` - 打包输出与构建临时文件
- `*.exe` - 可执行文件
- `passwords.json.aes` - 用户密码数据（敏感！）
- `settings.json` - 用户设置（敏感！）
- `启动.txt`、`密码测试.txt` - 本地测试数据（敏感！）
- `test_*.py` - 测试脚本
- `create_release.py`、`Git 同步清单.md` 等内部工具与报告
- `.venv/` - Python虚拟环境
- `__pycache__/` - Python缓存
- `nul`, `con`, `prn`, `aux` - Windows保留文件名

---

## 🔐 安全注意事项

### ⚠️ 重要提醒

1. **不要上传敏感数据**
   - ✅ 已正确配置.gitignore，密码数据文件不会被上传
   - ✅ `passwords.json.aes` 和 `settings.json` 已被排除

2. **检查.gitignore是否生效**
   ```bash
   # 查看哪些文件会被上传
   git status
   
   # 确认没有敏感文件
   git ls-files | findstr "passwords.json.aes"
   # 应该没有任何输出
   ```

3. **如果使用HTTPS推送需要认证**
   - 推荐使用 Personal Access Token (PAT)
   - 在GitHub Settings → Developer settings → Personal access tokens 中生成
   - 权限选择: `repo` (完全控制私有仓库)

---

## 📝 后续更新流程

每次修改代码后，按以下步骤更新GitHub：

```bash
# 1. 查看修改的文件
git status

# 2. 添加修改的文件
git add .

# 3. 提交更改
git commit -m "描述本次修改的内容"

# 4. 推送到GitHub
git push
```

**示例：**
```bash
git add .
git commit -m "修复登录界面的bug"
git push
```

---

## 🎯 v1.2.4 版本更新内容

本次提交包含以下更新：

### 新增功能
- ✅ 新增"关于"按钮（菜单栏"帮助"右侧），显示当前版本号
- ✅ 自动联网检查更新，发现新版本时可一键跳转下载
- ✅ 新增"主窗口始终置顶"设置开关（设置 → 外观设置 → 窗口）
- ✅ 批量导出新增 XLSX 格式（替代 CSV），表头加粗、列宽优化

### 体验改进
- ✅ 勾选条目后整行高亮（浅色/深色主题自适应）
- ✅ 登录窗口、首次设置窗口始终置顶，不再被其他窗口遮挡

### 问题修复
- ✅ 修复点击单元格后出现杂散蓝色残留的问题
- ✅ 修复含逗号、引号等特殊字符的密码导出后列错位的问题

### 更新的文档
- `README.md` - 添加v1.2.4版本说明
- `CHANGELOG.md` - 添加v1.2.4更新日志
- `发布说明.txt` - 更新为v1.2.4发布说明
- `version_info.txt` - 版本号更新为1.2.4.0
- `build.bat` - 版本号更新为1.2.4

---

## 💡 常见问题

### Q1: 推送时要求输入密码怎么办？
A: GitHub已不再支持密码认证，需要使用 Personal Access Token (PAT)：
1. 访问 https://github.com/settings/tokens
2. 生成新的token（选择repo权限）
3. 复制token，在推送时作为密码使用

### Q2: 如何查看已上传的文件？
A: 访问你的GitHub仓库页面，可以看到所有文件和提交历史。

### Q3: 上传后发现错误怎么办？
A: 可以修改后重新提交：
```bash
git add .
git commit -m "修复之前的错误"
git push
```

### Q4: 如何设置分支保护？
A: 在GitHub仓库的 Settings → Branches 中设置分支保护规则。

---

## 📞 需要帮助？

如果在上传过程中遇到问题：
1. 检查网络连接
2. 确认GitHub账号有权限
3. 查看错误提示信息
4. 参考GitHub官方文档: https://docs.github.com/

---

**祝上传顺利！** 🎉
