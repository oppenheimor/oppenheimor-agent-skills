# Toolbox Cover

面向 Oppenheimor 工具箱的封面处理工作流：缩略图便于识别，点击后看原始高清图。可用于其他项目，但应先参照目标项目的 `DESIGN.md` 和 `PRODUCT.md` 调整风格；未提供风格文档时先确认，不直接套用海军蓝主题。

## 安装

```sh
npx skills add https://github.com/oppenheimor/oppenheimor-agent-skills --skill toolbox-cover
```

## 使用

告诉 Agent：

> 用 toolbox-cover 处理这几张工具图片，保留品牌构图，生成候选封面，先不要替换。

Agent 会先检查素材，再选择 banner、screenshot、icon 或 poster 模式。程序的 auto 只是比例启发式，不替代视觉判断。

## 脚本

需要支持 ES modules / Node test runner 的现代 Node.js，以及**目标项目中已安装的 `sharp`**。脚本从当前工作目录的 `package.json` 解析依赖；本技能仓库本身不捆绑依赖，也不会静默安装。

从目标项目根目录运行，将 `<skill-dir>` 替换为已安装技能的绝对路径：

```sh
node <skill-dir>/scripts/compose.mjs \
  --source path/to/original.png \
  --output path/to/new-candidate \
  --mode banner

node --test <skill-dir>/scripts/compose.test.mjs
```

输出：

- `cover.webp`：1200×675，quality 92，作为封面缩略图。
- `original.webp`：原生尺寸、方向修正、无损编码，作为完整预览。
- `manifest.json`：源文件哈希、布局、裁切记录、背景来源和警告。

可选 `--background FILE --provenance LABEL`。默认底色来自原图，不需要图像生成服务。

`--crop left,top,width,height` 仅裁切缩略图，必须先获得用户确认。透明图标的完全透明边距可以自动去除。原文件和完整预览不裁切。拒绝覆盖已有输出文件，拒绝隐式丢弃动画／多页图片的其他帧。

## 边界与验证

不放大低清源图，不生成伪造的文字、Logo 或 UI，不添加折角、角标、贴纸和重复网格。极端比例与复杂背景需要人工看图，程序不保证所有素材自动完美。图像生成仅在需要背景且获授权时使用，保留真实 prompt 和来源。

自动测试使用临时生成的图片，不需要下载素材。`evals/evals.json` 的前三个真实案例引用原网站项目中的图片路径；图片未随技能分发，运行这些评审时需从网站项目执行或替换为自有素材。

默认仅生成候选；修改 `cover` / `coverFull` 需批准，发布、提交和 push 是独立权限。
