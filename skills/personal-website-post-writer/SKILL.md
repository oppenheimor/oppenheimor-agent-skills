---
name: personal-website-post-writer
description: >
  将当前对话、笔记、部署/排障过程、产品调研、AI 工作流或技术经验，整理成适合用户 personal-website 仓库发布的中文文章。当用户说“整理成一篇文章”“写成博客”“落到 personal-website”“沉淀成文章”“公众号文章”“基于上下文写文章”，或要求参考旧文章并提交 push 时，必须使用这个 skill。这个 skill 负责：抽样参考 2026.07 之前的旧文章风格、敏感信息脱敏、使用 renhua 去 AI 味、补齐 Markdown frontmatter、本地校验、git commit 和 push。用户明确说只要草稿时，跳过提交和 push。
---

# 个人网站文章写作器

这个 skill 用来把真实技术经历整理成简洁的中文文章，并发布到用户的个人网站项目：

```text
/Users/paulchess/Desktop/Home/@paulchess/personal-website
```

文章目录是：

```text
/Users/paulchess/Desktop/Home/@paulchess/personal-website/src/pages/posts
```

这个流程有明确偏好：用户要的是可重复发布流程，不是泛泛的写作助手。

## 默认结果

除非用户明确说只要草稿，否则完整执行下面的流程：

1. 根据当前上下文判断文章类型。
2. 从 `src/pages/posts` 中抽样参考 2026.07 之前的同类型文章。
3. 写出清晰、不臃肿的中文初稿。
4. 对敏感信息做脱敏。
5. 按 `$renhua` 规则去掉 AI 味。
6. 将文章保存为 `src/pages/posts` 下的 Markdown 文件。
7. 跑构建校验，或至少检查 Markdown/frontmatter 安全性。
8. 只提交这篇文章相关文件。
9. push 到 `origin/main`。

如果某一步被卡住，保留已经完成的文件，并告诉用户具体停在哪一步。

## 典型触发场景

用户常见提示类似：

```text
我想把它整理成一篇文章，一个很重要的目标是别的读者或者下次我自己再去做的时候能够有一个很清晰但不啰嗦的指南。
注意：去除无关内容、敏感信息脱敏。
参考 personal-website 里 2026.07 之前的文章。
完成后使用 $renhua 润色，落到 posts，提交并 push。
```

把 `xxx`、`基于上下文`、`刚才这件事` 理解为当前对话中的素材。如果上下文里缺少具体经历，先问一个简短问题再写。

## 依赖的 skill

润色文章时，优先加载并遵循 `renhua` skill。当前仓库内置路径是：

```text
../renhua/SKILL.md
```

如果这是安装后的独立 skill，尝试读取已安装位置：

```text
/Users/paulchess/.agents/skills/renhua/SKILL.md
```

如果找不到 `renhua`，使用本文档后面的「Renhua 检查」段作为最低限度替代。`$renhua` 是最后的编辑检查，不替代文章结构。文章仍然需要从上下文里保留事实、命令、取舍、踩坑和作者判断。

## 仓库卫生

动笔前先看工作区：

```bash
git -C /Users/paulchess/Desktop/Home/@paulchess/personal-website status --short
```

规则：

- 不提交无关的脏文件或未跟踪文件。
- 如果工作区里本来就有无关改动，保持原样；只有影响任务时才说明。
- 只显式 stage 新增或修改的文章文件。
- 不运行破坏性 git 命令。
- 保留用户已有的本地改动。

## 风格抽样

用户更信任 2026.07 之前的文章。先根据文章类型，从旧文章里抽样。

先列出候选文件：

```bash
find /Users/paulchess/Desktop/Home/@paulchess/personal-website/src/pages/posts \
  -maxdepth 1 -type f -name '*.md' | sort
```

按类型优先参考这些文章：

- 部署、服务器配置、网络、CLI 指南：`mihomo_github_proxy.md`、`clash_verge_company_domain_dns.md`、`clear-dns-cache.md`、`howto_assign_domain_in_vercel.md`、`vite_build_killed.md`
- 前端构建、工具链、踩坑：`postcss_preset_env_pit.md`、`vite_build_killed.md`、`node_lib_develop.md`、`npm_and_yarn.md`
- 产品体验、AI 工作流：`devv_rag.md`、`cozes_name_maker.md`、`llama_coder_analyse.md`
- 方法论、个人复盘：`okr_work_method.md`、`work_and_meditation.md`、`2025_plan.md`

读取足够内容来学习结构和语气，不要复制句子。抽取这些风格特征：

- 从真实问题或具体背景进入。
- 作者确实做过的事情，用第一人称。
- 有必要时给出可执行命令或精确检查方法。
- 保留一点粗粝感和实用判断。
- 不把常识概念讲成教材。
- 结尾落到具体经验，不写口号式总结。

## 判断文章类型

写作前先判断文章表面形态：

- **指南 / How-to**：读者要复现流程。结构要清楚，命令要能跑。
- **踩坑 / 排查记录**：围绕一个失败现象展开。写症状、分层检查、修复、验证。
- **部署记录**：写环境、产物、服务器步骤、nginx/proxy/config、校验。
- **产品/工具体验**：写测了什么、哪里可用、哪里不行、适合放进哪个工作流。
- **方法论复盘**：写工作流怎么变、保留了哪些判断、去掉了哪些成本。

通常不要在正文里宣布这个分类，除非它能帮助读者理解。

## 素材抽取

写作前把上下文拆成四类：

```text
facts       命令、路径、日期、工具、版本、观测输出
judgment    作者最后的判断、选择和不确定性
experience  实际做过、失败过、修过、验证过的过程
action      读者可以复用或避开的动作
```

文章要扎在这四类素材里。删掉聊天中的协调过程、无关寒暄、只在原对话里有意义的细节。

## 敏感信息脱敏

保存前脱敏，保存后再扫一遍。

把真实值换成占位符：

```text
<server_user>
<server_host>
<domain>
<repo_path>
<project_name>
<token>
<api_key>
<internal_domain>
<internal_ip>
<container_name>
```

如果路径能帮助读者理解结构，可以保留泛化后的项目路径；涉及个人身份、服务器、公司内部系统时要脱敏。

不要发布：

- 真实公网 IP
- SSH 示例里的真实用户名
- access token、API key、cookie、订阅地址
- 用户没有明确说可公开的私有域名
- 公司内部域名、DNS IP、Git remote、镜像仓库地址
- `.env`、shell history、日志、浏览器会话里的密钥

用类似命令扫描：

```bash
rg -n "([0-9]{1,3}\.){3}[0-9]{1,3}|sk-|token|api[_-]?key|password|passwd|cookie|secret|118\\.|heqi|真实域名" <article-file>
```

命中后人工检查。`<token>` 这种占位符可以保留。

## Markdown 格式

在 `src/pages/posts` 下创建一个 Markdown 文件。

frontmatter：

```markdown
---
title: 文章标题
date: YYYY-MM-DDT00:00:00.000+00:00
lang: zh
duration: Nmin
author: 沈佳棋
---
```

文件名：

- 使用小写英文 snake_case。
- 稳定、可读、描述清楚。
- 例如：`docker_static_site_deploy.md`、`github_proxy_server.md`、`agent_workflow_review.md`。

阅读时长：

- 短笔记：2-5 min。
- 实操指南：6-10 min。
- 长分析：10+ min。

## 起草规则

正文写中文。中文 AI/工程写作里常用的英文技术词保留英文，例如 Docker、nginx、SSH、CI、Agent、LLM eval、API、token、cache。

指南类文章优先使用这个结构：

```markdown
## 背景
## 需要提前准备的信息
## 第一步：...
## 第二步：...
## 踩到的点
## 最后保留的流程
```

排障类文章优先使用这个结构：

```markdown
## 背景
## 问题现象
## 排查过程
## 解决方法
## 验证
## 这次保留的判断
```

文章要清楚但不啰嗦：

- 保留读者能直接执行的命令。
- 只解释实际卡住过的一两个概念。
- 删除仪式感解释、泛泛的 Docker/Git/npm 入门和空泛意义拔高。
- 上下文里有不确定性时保留下来。
- 使用占位符，并说明需要替换。

## Renhua 检查

初稿完成后，按 `$renhua` 的硬规则检查。重点扫描：

```text
不是.*而是
不在于.*在于
不只是
不仅
别急着
先别
顺序别反了
别搞反了
记住这句话
真正
其实
本质上
核心在于
关键在于
说白了
归根结底
更重要的是
东西
这件事
几个方向
差距会
分水岭
```

用 `rg` 找可疑表达，再手工改句子：

```bash
rg -n "不是.*而是|不在于.*在于|不只是|不仅|别急着|先别|顺序别反了|别搞反了|记住这句话|真正|其实|本质上|核心在于|关键在于|说白了|归根结底|更重要的是|东西|这件事|几个方向|差距会|分水岭" <article-file>
```

不要机械删除每个命中词。改写时让判断更具体。

## 校验

能跑构建时就跑构建。

这个仓库可能存在旧的 `packageManager` 值和较新的全局 `pnpm`。如果 `pnpm build` 在进入项目构建前就试图清理 `node_modules` 或失败，不要动依赖目录，改用项目本地二进制：

```bash
cd /Users/paulchess/Desktop/Home/@paulchess/personal-website
./node_modules/.bin/vite-ssg build
```

如果构建里出现和新文章无关的旧 warning，可以接受，但要在最终回复里说明。

如果没有依赖或构建成本太高，至少完成：

- 读一遍保存后的 Markdown。
- 检查 frontmatter。
- 扫描敏感信息。
- 扫描 `$renhua` 硬规则里的可疑表达。

## 提交和推送

文章确认后执行：

```bash
git -C /Users/paulchess/Desktop/Home/@paulchess/personal-website add src/pages/posts/<file>.md
git -C /Users/paulchess/Desktop/Home/@paulchess/personal-website commit -m "docs: add <topic> post"
git -C /Users/paulchess/Desktop/Home/@paulchess/personal-website push origin main
```

提交前确认暂存区只包含目标文章：

```bash
git -C /Users/paulchess/Desktop/Home/@paulchess/personal-website diff --cached --stat
git -C /Users/paulchess/Desktop/Home/@paulchess/personal-website diff --cached -- src/pages/posts/<file>.md
```

用户要求“只要草稿”时，跳过 commit 和 push。

## 最终回复

最终回复保持简短，包含：

- 文章文件路径
- commit hash 和 commit message，如果已提交
- push 状态
- 校验命令和结果
- 保持未动的无关脏文件

除非用户要求，不要把整篇文章贴回对话。
