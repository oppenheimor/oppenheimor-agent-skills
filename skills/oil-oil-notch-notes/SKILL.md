---
name: oil-oil-notch-notes
description: >
  管理本机 NotchNotes（刘海笔记）中的 Markdown 笔记与待办。用户提到 NotchNotes、Notch Notes、刘海笔记，或明确要在本地 NotchNotes 中记待办、查看笔记、搜索笔记、修改待办、删除笔记时必须使用。通过随 Skill 提供的 CLI 安全执行新增、列表、读取、修改和删除；删除前必须再次取得明确确认。用户明确指定 Obsidian、备忘录或其他应用时不要使用。
compatibility: 仅支持安装了 NotchNotes.app 的 macOS；需要 Python 3。
---

# NotchNotes 笔记管理

通过本 Skill 自带的 CLI 管理本机 NotchNotes。每个待办对应一篇独立 Note，不要把多个待办追加到共享待办清单。

## 核心安全规则

不要直接编辑 `notes.json`、NotchNotes plist 或图片存储。所有读写都通过 `scripts/notchnotes.py` 完成，让 App 退出、快照选择、备份、原子写入、冲突检查和重新启动保持为一个完整操作。

开始前，先根据当前 `SKILL.md` 的实际路径定位同目录下的 CLI，并保存为绝对路径：

```bash
NOTCHNOTES_CLI="<本 Skill 的绝对路径>/scripts/notchnotes.py"
```

CLI 每次输出一个 JSON 对象。退出码非零或结果中的 `ok` 为 `false` 都表示失败。

## 执行流程

1. 判断用户要新增、列表、读取、修改还是删除。
2. 操作已有笔记时，先解析出唯一的 Note UUID；标题可能重复，不能把标题当唯一标识。
3. 准备完整 Markdown，不补写用户没有提供的事实。
4. 删除前展示标题和简短预览，并等待用户再次明确确认。
5. 每次用户指令只执行一次 CLI 写操作。
6. 检查结果中 `ok: true`，并向用户报告标题和 Note UUID。

## 新增笔记或待办

新增待办前先读取 [`references/markdown-syntax.md`](references/markdown-syntax.md)。把未勾选任务放在第一条有意义的内容中，用户给了说明时再写到下方：

```markdown
- [ ] 完成 NotchNotes Skill

先实现安全的本地 CLI，再由 Skill 调用。
```

用户只给标题时，不要自行编造正文。一次用户指令默认只新建一篇 Note。新增不需要二次确认。

把 Markdown 写入临时 UTF-8 文件后执行：

```bash
python3 "$NOTCHNOTES_CLI" create --file /tmp/notchnotes-note.md
```

执行后删除临时文件。

### 新增示例

用户：

```text
记个待办：周五前整理发布清单，需要检查构建、版本号和回滚方案。
```

写入内容：

```markdown
- [ ] 周五前整理发布清单

需要检查构建、版本号和回滚方案。
```

## 列表、搜索和读取

```bash
python3 "$NOTCHNOTES_CLI" list
python3 "$NOTCHNOTES_CLI" list --query "发布清单"
python3 "$NOTCHNOTES_CLI" read NOTE_UUID
```

没有匹配项时直接说明。多个结果都可能是目标时，读取必要的候选项并让用户选择，不要猜测。除非用户要求读取完整内容，或消除歧义确实需要，否则不要展示私人笔记全文。

## 修改笔记

修改会替换整篇 Note 的 Markdown，因此写入前必须读取最新内容：

1. 找到唯一的 Note UUID。
2. 立即执行 `read`，取得 `content` 和 `revision`。
3. 只修改用户指定的内容，保留无关 Markdown；不要自行改变勾选状态。
4. 将修改后的完整 Markdown 写入临时 UTF-8 文件。
5. 携带刚读取的版本号执行更新：

```bash
python3 "$NOTCHNOTES_CLI" update NOTE_UUID \
  --file /tmp/notchnotes-note.md \
  --if-revision 'sha256:REVISION'
```

执行后删除临时文件。

如果返回 `REVISION_CONFLICT`，重新读取、在新内容上再次应用用户要求，并最多重试一次。若此时用户意图不再明确，停止并询问；不要用旧版本强行覆盖。

### 修改示例

用户：

```text
把“周五前整理发布清单”的说明改成：先确认回滚方案，再检查构建和版本号。
```

先搜索并读取唯一目标，再保留标题、只替换说明：

```markdown
- [ ] 周五前整理发布清单

先确认回滚方案，再检查构建和版本号。
```

## 删除笔记

删除必须分成两轮：

1. 解析并读取目标，向用户展示标题和简短预览。
2. 询问是否确认删除。初始的“删除某笔记”请求本身不算确认。
3. 用户确认后再次读取最新版本号，再执行：

```bash
python3 "$NOTCHNOTES_CLI" delete NOTE_UUID \
  --if-revision 'sha256:REVISION' \
  --confirmed
```

如果确认后笔记内容发生变化，展示变化后的目标并重新确认。NotchNotes 不允许删除最后一篇笔记。

### 删除示例

用户：

```text
删除 NotchNotes 里“周五前整理发布清单”这条待办。
```

Agent 先回复：

```text
找到待办“周五前整理发布清单”，预览为“先确认回滚方案，再检查构建和版本号”。确认删除吗？
```

只有用户明确回复“确认删除”后，才携带最新 `revision` 和 `--confirmed` 执行删除。

## 错误处理

按稳定错误码处理，不要匹配错误文案：

- `ARCHIVE_NOT_FOUND`：请用户先启动一次 NotchNotes，初始化本地存储。
- `NOTE_NOT_FOUND`：刷新列表，不要改为操作其他笔记。
- `REVISION_CONFLICT`：重新读取后再判断能否重试。
- `LAST_NOTE_DELETE_FORBIDDEN`：说明 NotchNotes 必须保留至少一篇笔记。
- `CONFIRMATION_REQUIRED`：取得明确删除确认。
- `APP_QUIT_TIMEOUT`：请用户结束正在进行的 App 操作后重试。
- `APP_LAUNCH_FAILED`：写入可能已成功；重试新增前先执行 `list` 或 `read`，避免重复创建。
- `VERIFY_FAILED`：用 `read` 检查结果，不要直接重复新增。

## 禁止行为

- 不维护共享的 `# Todos` 笔记。
- 不引入任务 ID、todo 子命令、append 子命令或隐藏 Markdown 元数据。
- 不自动完成、重开、排序或跟踪待办。
- 多个候选项存在时，不只按标题选择。
- App 重启或校验失败时，不盲目重复 `create`。
- 常规成功回复不回显完整笔记正文。

## 交付前检查

- 一条用户待办只创建了一篇 Note。
- 新待办第一行以 `- [ ] ` 开始，并保留用户给出的全部说明。
- 修改和删除使用刚读取到的 UUID 与 revision。
- 删除已经获得用户二次明确确认。
- CLI 返回 `ok: true`。
- 临时 Markdown 文件已经删除。
