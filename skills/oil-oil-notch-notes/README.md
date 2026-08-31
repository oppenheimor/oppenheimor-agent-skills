# oil-oil-notch-notes

通过 Agent 安全管理 macOS 本机 NotchNotes（刘海笔记）中的 Markdown 笔记和待办，支持新增、搜索、读取、修改与删除。

## 安装

```bash
npx skills add https://github.com/oppenheimor/oppenheimor-agent-skills --skill oil-oil-notch-notes
```

使用前请先安装并启动一次 NotchNotes.app。本 Skill 仅支持 macOS，并依赖 Python 3。

## 对 Agent 说

### 新增

```text
记个待办：周五前整理发布清单，需要检查构建、版本号和回滚方案。
```

Agent 会创建一篇独立 Note：

```markdown
- [ ] 周五前整理发布清单

需要检查构建、版本号和回滚方案。
```

### 修改

```text
把 NotchNotes 里“周五前整理发布清单”的说明改成：先确认回滚方案，再检查构建和版本号。
```

Agent 会先读取最新内容和版本号，只修改指定说明，避免覆盖并发变更。

### 删除

```text
删除 NotchNotes 里“周五前整理发布清单”这条待办。
```

Agent 会先展示标题和简短预览，并再次询问是否确认。只有收到“确认删除”后才会真正删除。

## 直接使用 CLI

```bash
python3 scripts/notchnotes.py list
python3 scripts/notchnotes.py list --query "发布清单"
python3 scripts/notchnotes.py read NOTE_UUID
python3 scripts/notchnotes.py create --file /tmp/new-note.md
python3 scripts/notchnotes.py update NOTE_UUID --file /tmp/note.md --if-revision 'sha256:REVISION'
python3 scripts/notchnotes.py delete NOTE_UUID --if-revision 'sha256:REVISION' --confirmed
```

CLI 输出单个 JSON 对象。写操作会处理 NotchNotes 的安全退出、恢复备份、原子写入、版本冲突检测、结果校验和 App 重启。

## 安全边界

- 不直接编辑 NotchNotes 的 `notes.json` 或 plist。
- 修改和删除必须携带刚读取的 revision。
- 删除必须取得二次明确确认。
- 不允许删除最后一篇笔记。
- 不自动勾选、重开、排序或跟踪待办。
