# Image version tagging policy

User's rule: for ancient calligraphy/art, copies ARE the norm — a Tang copy of a Jin
work is often the best surviving version. The caption must state the image's
relationship to the work; it must not claim authenticity it cannot support.

## Tag priority (first match wins)
1. The work's own material field is authoritative: contains 真迹/真跡 → `真迹墨迹`;
   contains 摹本 → `摹本系统（馆藏）`.
2. A later hand's name appears in filename/description and is not the work's author
   (fold traditional→simplified on BOTH sides before comparing) → `<name>临本`
   (e.g. 赵之谦临本, 秦树声临本, 董其昌临本).
3. Filename version words:
   - 唐摹|響拓|冯承素|虞摹|褚摹|神龍本 → 唐摹本
   - 宋摹 → 宋摹本; 明摹|成化|萬曆 → 明代摹刻本; 清摹|乾隆 → 清代摹本
   - 宋拓 → 宋拓本; 明拓 → 明拓本; 清拓 → 清拓本
   - 拓|rubbing|刻帖|法帖|淳化閣帖|大觀帖|三希堂|關中本|碑林 → 刻帖／拓本
   - 碑阳|碑陰|原石|on-site date stamp → 原碑现场影像
   - 墨跡|紙本墨跡|絹本墨跡 → 墨迹本
4. Era + material inference (when the filename is silent):
   - 晋/三国/南北朝/隋 + 纸本/绢本 → `唐（宋）摹本系统` (no originals of this era survive)
   - 青铜/甲骨/简牍/帛 → `原器影像`
   - 石碑/摩崖/刻石 → `拓本／原碑影像`
5. Institutional prefix (NPM-, NDL, SSID-, WUL-, CADAL, NLC) → `馆藏扫描件`
   (mime application/pdf → `馆藏扫描（PDF）`).
6. Fallback: `相关影像` — honest, never blank.

Priority-order note: 唐摹本 outranks 墨迹本 in the preference walk, because a Tang copy
is usually described as 纸本墨迹 in the same breath; ranking 墨迹本 first would mislabel
copies as originals.

## Scoring in the resolver (rank, never reject)
唐摹 +12 · 宋拓/刻帖 +8 · 明清临摹 −6 · later hand −10 · stele rubbing +7 (non-stele +1)
· institutional prefix +3 · tiff +5 · pdf −3.

## Caption wording
Chip text: `影像：<tag>`, top-right of the image box. Page-level note must say that
copies/rubbings are the norm for ancient works and that images are chosen to show the
relationship to the work, not to assert authenticity.
