# 生图提示词模板

每张单独生成，替换全部变量。实际传入 `assets/character-reference.png` 的绝对路径；文字中的“attached”不能代替传图。

```text
Generate one standalone horizontal Chinese article illustration, composed for a 16:9 final frame.

Reference role:
The attached character-reference.png is the identity anchor for the recurring Oppenheimor cat, NOT a layout, pose, or background template. Preserve the same character across images.

Character identity:
A rounded charcoal-black cat with a large round head and cheek tufts, triangular ears with golden-yellow interiors, very large golden-yellow eyes with large black pupils and small white highlights, a small coral-red triangular nose, a simple curved black mouth, a red triangular neckerchief with a visible side knot and two ribbon ends, short plump limbs, rounded cat paws, and a thick curved tail. Preserve the reference proportions and recognizable face. Keep the cat naturally charming and focused, not an abstract creature. No white-dot eyes, stick legs, human hands, extra limbs, white belly, or missing scarf.

Visual DNA:
Pure white background, minimalist black hand-drawn scene, slightly wobbly thin pen lines, lots of empty space. Render the cat with its recognizable filled black silhouette and intrinsic golden-yellow/coral/red accents; simplify shading without losing identity. No paper texture, gradients, complex background, realistic UI, commercial vector poster, PPT infographic, or decorative mascot sticker layout.

Theme: {主题}
Core idea: {核心意思}
Structure: {结构类型，仅用于指导，不写在图上}
Composition: {猫的核心动作、位置、物件和信息关系；不要固定照搬参考坐姿}
Props: {1–2 个主物件}
Chinese labels: {最多 5–8 处，每处 2–8 字，可更少或无文字}

Color use:
Keep the cat's golden-yellow eyes and inner ears, coral-red nose, and red neckerchief regardless of annotation colors. Outside the character, use sparse orange for flow, red for emphasis, and blue for secondary notes. Do not recolor the character to fit diagram semantics.

Constraints:
One core concept per image. Main subject around 40–60% of the canvas, at least 35% empty white space. The cat performs the action that explains the idea, rather than watching from a corner. Do not transform its body into machinery. Invent an original metaphor for this article. No top-left title or structure-type heading. Keep all essential content inside the central 16:9 safe area if the tool outputs a taller landscape canvas.
```

## 替换旧角色

同时传入待编辑图和角色锚点，明确图像角色：

```text
Edit the provided illustration (layout source). Replace its old protagonist with the cat from character-reference.png (identity source). Preserve the existing composition, props, labels, arrows, background, and line style except where the new cat's anatomy requires a local adjustment. Keep the new cat's golden eyes and inner ears, coral nose, red neckerchief, rounded paws and thick tail. Adapt its pose to perform the same conceptual action; do not copy the anchor's seated pose automatically. If the old character itself forms a machine or funnel, use a separate prop operated by the cat instead. Do not add unrelated text or decorations.
```

## 局部改图

去标题：只移除指定标题及下划线，用同样白底补齐，保留其他文字、角色、线条和布局。

加强隐喻：修改猫的动作和关键物件，让它承担概念动作；保持角色身份、留白和简短标注，不通过扭曲猫的身体制造荒诞感。
