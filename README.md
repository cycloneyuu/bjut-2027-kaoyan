# 北工大 2027 交通考研资讯 · 微信 H5

以北京工业大学城市交通学院 **082300 交通运输工程（学硕）** 和 **086100 交通运输（专硕）** 为核心的移动端资讯看板。纯静态网页，不需要服务器或数据库；GitHub Actions 每天尝试从公开网页及搜索索引抓取资讯，生成 `data/news.json`，GitHub Pages 负责发布。无需在 ChatGPT 中推送。

## 上线（需要 GitHub 账号）

1. 新建 **Public** GitHub 仓库，例如 `bjut-2027-kaoyan`。
2. 将本 ZIP 的文件（包括隐藏目录 `.github` 和 `.nojekyll`）上传到仓库 **main** 分支的根目录。不要只上传 ZIP 文件。
3. 进入仓库 **Settings → Pages → Build and deployment → Source**，选择 **GitHub Actions**。
4. 进入 **Actions** → **Update news and deploy** → **Run workflow** 手动执行一次，等待两个任务成功。
5. 站点地址通常为 `https://<你的GitHub用户名>.github.io/bjut-2027-kaoyan/`，以 Pages 页面实际显示的 URL 为准。把它分享到微信，微信中打开后可添加到收藏。

## 每日更新

工作流每天北京时间 **08:00** 计划启动，实际执行可能延迟，且 GitHub 可暂停不活跃仓库的计划任务。`data/news.json` 中的 `updated_at` 表示最后一次**执行抓取**的时间，而不是所有来源均已核实或有新增资讯。

官方来源以 `yanzhao.bjut.edu.cn` 为准。公开讨论来自搜索引擎索引，平台可能禁止抓取、隐藏结果或有收录延时，因此**不保证覆盖所有知乎/小红书/贴吧/B站内容**。搜索索引条目均标记“待核实”，不推断发布日期、不从未验证的网页提取招生结论。

## 数据保护与局限

- 书签存于当前浏览器 localStorage，换手机或清理微信缓存会丢失；可用 JSON 导出导入。
- 这个网站是非官方的个人信息聚合工具，不代表北京工业大学。
- GitHub Pages 静态站点无法主动在微信里发服务通知；这个版本提供的是**每日自动更新网页**而不是**微信主动推送**。
- 无法跳过需要账号登录、验证码或受限访问的页面，尊重平台条款。
- 若目标是在微信内置浏览器稳定打开，建议配置符合当地法规要求的 HTTPS 域名，并在实际微信环境测试；部分链接可能需要跳转外部浏览器。

## 常见问题

- **Actions 出现 403 push 失败**：到 Settings → Actions → General → Workflow permissions 启用 `Read and write permissions`，并检查 main 分支保护规则；若组织策略不允许，改用有写入权限的部署方式。
- **Pages 发布失败**：确认 Settings → Pages → Source 选中 `GitHub Actions`，仓库 Pages 功能可用。
- **信息太少**：官网 HTML 结构及搜索 RSS 收录经常变化，需按实际情况维护 `scripts/update.py`。不会伪造没有抓到的资讯。
- **微信分享打不开**：微信可能对特定域名和第三方链接有限制，需在真实手机微信里测试，必要时使用自有合规域名。
