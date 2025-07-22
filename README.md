# 🚀 daily-arXiv-ai-enhanced（每日 AI 增强 arXiv 摘要）

> 用 AI 为你每日精选 arXiv 论文——让科研阅读更智能、更个性化！

本工具通过“自动爬取 + AI 摘要”双剑合璧，彻底革新你追踪 arXiv 论文的方式。

---

## ✨ 核心亮点

🎯 **零基础设施**  
- 完全基于 GitHub Actions + Pages，无需服务器  
- 部署与使用 100% 免费  

🤖 **智能 AI 摘要**  
- 每日自动爬取最新论文，由 DeepSeek 生成中文摘要  
- 超低费用：非高峰时段每天仅约 0.2 元人民币  

💫 **极致阅读体验**  
- 根据关键词 & 作者高亮你感兴趣的文章  
- 桌面 & 移动端自适应  
- 偏好数据仅保存在浏览器本地，保护隐私  
- 支持单日期或日期区间筛选  

👉 **[立即体验！](https://dw-dengwei.github.io/daily-arXiv-ai-enhanced/)** —— 无需安装，点开即用  

---

## 界面速览

- **首页**：高亮你关心的关键词与作者  
  <img src="images/index.png" alt="首页" width="800">

- **设置页**：本地保存关键词与作者  
  <img src="images/setting.png" alt="设置页" width="600">

- **详情页**：点击论文卡片即可查看摘要与链接  
  <img src="images/details.png" alt="详情页" width="500">

- **日期筛选**：单日期 / 日期范围任选  
  ⚠️ 注意：范围过大可能因加载过多论文导致浏览器卡顿  
  <img src="images/single-date.png" alt="单日期" width="300">
  <img src="images/range-date.png" alt="日期范围" width="300">

- **统计页**（开发中）：  
  - 提取所选日期论文关键词  
  - 多日范围展示关键词趋势  
  - 由于不渲染全部论文，大范围也不会卡，仅需几秒完成关键词分析  
  <img src="images/keyword.png" alt="关键词" width="600">
  <img src="images/trends.png" alt="趋势" width="600">

---

## 使用方法

本仓库默认每日爬取 **cs.CV、cs.GR、cs.CL、cs.AI** 四个分类，并用 **DeepSeek** 生成 **中文** 摘要。  
如需自定义分类 / 模型 / 语言，请按以下步骤操作；否则可直接使用官方演示站：[https://dw-dengwei.github.io/daily-arXiv-ai-enhanced/](https://dw-dengwei.github.io/daily-arXiv-ai-enhanced/) ，顺手点个 ⭐ 就是对作者最大的支持 :)

### 完整自建流程

1. **Fork** 本仓库到你的账号  
2. 进入 `你的仓库 -> Settings -> Secrets and variables -> Actions`  
   - **Secrets**（加密，用于敏感信息）  
     - 新建 `OPENAI_BASE_URL`：填写接口 Base URL（如 `https://api.deepseek.com/v1`）  
     - 新建 `OPENAI_API_KEY`：填写你的 API Key  
   - **Variables**（明文，用于非敏感配置）  
     - `CATEGORIES`：如 `cs.CL,cs.CV`（用英文逗号分隔）  
     - `LANGUAGE`：`Chinese` 或 `English`  
     - `MODEL_NAME`：如 `deepseek-chat`  
     - `EMAIL`：用于 Git 提交的邮箱  
     - `NAME`：用于 Git 提交的用户名  
3. 进入 `Actions -> arXiv-daily-ai-enhanced`，手动点击 **Run workflow** 测试（约 1 小时）。默认每日自动触发，可在 `.github/workflows/run.yml` 中修改。  
4. 启用 GitHub Pages：  
   `Settings -> Pages -> Build and deployment`  
   - Source 选 `Deploy from a branch`  
   - Branch 选 `main / (root)`  
   等待几分钟后访问 `https://<你的用户名>.github.io/daily-arXiv-ai-enhanced/`  
   更详细的图文指引可参考 [Issue #14](https://github.com/dw-dengwei/daily-arXiv-ai-enhanced/issues/14)。

---

## 任务清单

- [x] 用 GitHub Pages 前端替换纯 Markdown  
- [ ] 修复：统计页关键词计数错误  
- [ ] 修复：日期选择器星期不对应  
- [ ] 新功能：用 DeepSeek 自动提取关键词  
- [x] 补充 Fork 用户 GitHub Pages 使用说明  

---

## 贡献者

感谢以下特别贡献者：代码、捉虫、献策！

| [JianGuanTHU](https://github.com/JianGuanTHU) | [Chi-hong22](https://github.com/Chi-hong22) | [chaozg](https://github.com/chaozg) | [quantum-ctrl](https://github.com/quantum-ctrl) | [Zhao2z](https://github.com/Zhao2z) |
| :---: | :---: | :---: | :---: | :---: |
| ![JianGuanTHU](https://avatars.githubusercontent.com/u/44895708?v=4&s=100) | ![Chi-hong22](https://avatars.githubusercontent.com/u/75403952?v=4&s=100) | ![chaozg](https://avatars.githubusercontent.com/u/69794131?v=4&s=100) | ![quantum-ctrl](https://avatars.githubusercontent.com/u/16505311?v=4&s=100) | ![Zhao2z](https://avatars.githubusercontent.com/u/141019403?v=4&s=100) |

---

## 鸣谢

诚挚感谢以下个人与组织对项目的推广与支持！

| [GitHub Daily](https://x.com/GitHub_Daily/status/1930610556731318781) | [AIGCLINK](https://x.com/aigclink/status/1930897858963853746) | [阮一峰的网络日志·科技爱好者周刊（第 353 期）](https://www.ruanyifeng.com/blog/2025/06/weekly-issue-353.html) | [HelloGitHub 月刊第 111 期](https://hellogithub.com/periodical/volume/111) |
| :---: | :---: | :---: | :---: |
| ![GitHub Daily](https://pbs.twimg.com/profile_images/1660876795347111937/EIo6fIr4_400x400.jpg) | ![AIGCLINK](https://pbs.twimg.com/profile_images/1729450995850027008/gllXr6bh_400x400.jpg) | ![阮一峰](https://avatars.githubusercontent.com/u/905434?s=100) | ![HelloGitHub](https://github.com/user-attachments/assets/eff6b6dd-0323-40c4-9db6-444a51bbc80a) |

---

## Star 历史

[![Star History Chart](https://api.star-history.com/svg?repos=dw-dengwei/daily-arXiv-ai-enhanced&type=Date)](https://www.star-history.com/#dw-dengwei/daily-arXiv-ai-enhanced&Date)
