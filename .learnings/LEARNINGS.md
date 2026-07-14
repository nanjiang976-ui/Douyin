# Learnings

Corrections, insights, and knowledge gaps captured during development.

**Categories**: correction | insight | knowledge_gap | best_practice

---

## [LRN-20260714-005] correction

**Logged**: 2026-07-14T01:38:20+08:00
**Priority**: critical
**Status**: resolved
**Area**: content-system

### Summary
对标账号学习库必须同时沉淀写作机制和可直接检索的精确表层素材，不能把例子、案例、比喻、个人故事、事实、原话或原始顺序排除在资产库之外。

### Details
用户明确废止旧的“只迁移机制、禁止迁移表层素材”规则。为了避免分类漏判造成素材丢失，可靠的回填结构必须是一条文案一条记录，保存完整正文和全部原文段落，再叠加例子、案例、比喻、个人故事、事实数字、原话、概念和方法等多标签索引。写稿检索器必须返回素材ID、段落ID、精确原文、来源和核验状态。

### Suggested Action
新账号拆解默认生成 `07_对标表层素材库.jsonl`；已分析账号运行统一回填脚本；认知脚本生成器每次选择主账号后强制检索1—3条表层素材。事实性内容发布前核验，但不能因为需要核验而不沉淀或不返回。

### Metadata
- Source: user_feedback
- Related Files: C:/Users/NJ/.codex/skills/douyin-benchmark-script-learning/SKILL.md, C:/Users/NJ/.codex/skills/douyin-cognition-script-builder/SKILL.md
- Tags: douyin, benchmark, material-library, exact-reuse, source-trace
- Pattern-Key: content.benchmark_exact_material_capture
- Recurrence-Count: 1
- First-Seen: 2026-07-14
- Last-Seen: 2026-07-14

### Resolution
- **Resolved**: 2026-07-14T01:38:20+08:00
- **Notes**: 两套 skill、注册表、选择器、四个已分析账号和101条素材记录已完成迁移；全量素材与检索验证通过。

---

## [LRN-20260713-002] correction

**Logged**: 2026-07-13T01:20:00+08:00
**Priority**: high
**Status**: resolved
**Area**: content-system

### Summary
用户拥有多个长期方向，不代表当前账号可以自动继承所有方向；账号定位必须独立保存并在选题、对标迁移和写稿检索前优先约束。

### Details
本次把“如果说”的文案机制转译到用户资产库时，错误地把用户长期研究的 AI 方向带入了当前认知类账号，生成了多条 AI 选题和示例。用户明确当前账号主线是认知、个人成长和自我提升；AI 只可在明确服务于认知主题时作为辅助场景，不能成为默认选题或账号标签。

### Suggested Action
为每个账号建立独立定位文件；对标风格检索先读取账号定位，再选择主题和结构。长期用户画像只提供背景，不得覆盖当前账号配置。跨账号迁移主题必须由用户明确授权，或由当前选题明确要求。

### Metadata
- Source: user_feedback
- Related Files: 05_内容资产库/00_认知类账号定位.md, 05_内容资产库/05_对标账号风格库/registry.json
- Tags: account-positioning, cognition-content, benchmark-retrieval, cross-contamination
- Pattern-Key: content.account_positioning_before_retrieval
- Recurrence-Count: 1
- First-Seen: 2026-07-13
- Last-Seen: 2026-07-13

---

## [LRN-20260712-001] best_practice

**Logged**: 2026-07-12T23:10:00+08:00
**Priority**: high
**Status**: pending
**Area**: backend

### Summary
抖音认知类长视频的完整文案不能只依赖单次 ASR；应使用时间戳转录、双模型对照和画面字幕核对。

### Details
`faster-whisper base/small` 能覆盖主要语义，但会系统性误识别古籍、书名、人名、心理学术语和同音词，且可能整段漏掉配乐下的古文引用。对《大脑不追求幸福，只追求控制感》的样本复核显示，`皮质醇`、`西西弗斯`、`《前赤壁赋》`、`《肖申克的救赎》` 等均需二次校订；视频内嵌字幕可用于恢复 ASR 漏句和确认难词。

### Suggested Action
批量转录时保存带时间戳的 `small` 模型结果；将书名、人名、古籍、外文术语和低置信片段列为核验点，并结合平台章节摘要和对应时间点的画面字幕生成校订稿。原始 ASR 稿只作为中间材料，不直接进入长期文案库。

### Metadata
- Source: conversation
- Related Files: 01_工具_采集转写分析/transcribe_series_all.py, 02_账号项目/如果说_高流量视频_20260701/02_转写文本/7641622542096043299.transcript.reviewed.md
- Tags: douyin, transcription, faster-whisper, subtitle-validation
- Pattern-Key: douyin.transcript.asr_subtitle_validation
- Recurrence-Count: 1
- First-Seen: 2026-07-12
- Last-Seen: 2026-07-12

---

## [LRN-20260713-003] best_practice

**Logged**: 2026-07-13T12:00:00+08:00
**Priority**: high
**Status**: resolved
**Area**: content-system

### Summary
对标账号的全量分析必须以人工终审稿正文为唯一内容源，并让分析脚本在归档后仍能优先定位最终文案。

### Details
当转写过程同时存在ASR、OCR、融合稿和人工终审稿时，旧分析脚本若直接读取ASR，会把已纠正的人名、古籍、数字与风险边界重新污染回风格结论。把终审正文放入独立目录后，分析脚本还需要显式解析“完整文案”区段并在归档路径中查找ASR元数据和OCR证据层。

### Suggested Action
后续账号拆解默认使用“终审正文优先、ASR仅作时间与元数据证据”的解析器；归档前后都运行65条数量、ID、正文来源和证据层的对应校验。

### Metadata
- Source: conversation
- Related Files: 01_工具_采集转写分析/build_account_corpus_metrics.py, 01_工具_采集转写分析/build_per_video_teardown_index.py
- Tags: benchmark-analysis, reviewed-transcript, evidence-archive, content-assets
- Pattern-Key: douyin.reviewed_text_before_analysis
- Recurrence-Count: 1
- First-Seen: 2026-07-13
- Last-Seen: 2026-07-13

---

## [LRN-20260713-004] best_practice

**Logged**: 2026-07-13T13:10:00+08:00
**Priority**: medium
**Status**: resolved
**Area**: content-system

### Summary
多对标账号的写稿检索必须先锁定一个账号阶段，再只在该阶段的模型目录中排序，避免跨阶段拼接出不一致的文风。

### Details
账号可同时拥有早期的强执行钩子、过渡期的人物叙事和成熟期的认知重构结构。若模型评分在全账号范围内直接排序，选中的成熟阶段仍可能得到早期模型，造成钩子、论证和情绪收束互相冲突。将阶段路由和模型目录写进每个账号的独立风格指纹后，选择器可对未来新账号使用同一套逻辑。

### Suggested Action
新对标账号完成拆解时，按 `benchmark-library-contract.md` 注册默认阶段、阶段路由、阶段模型和模型检索标签；写稿时先选主账号/阶段，再从该阶段挑选一个主模型和最多两个局部能力。

### Metadata
- Source: conversation
- Related Files: C:/Users/NJ/.codex/skills/douyin-cognition-script-builder/scripts/select_benchmark_styles.py, C:/Users/NJ/.codex/skills/douyin-cognition-script-builder/references/benchmark-library-contract.md
- Tags: benchmark-retrieval, phase-routing, style-fingerprint, anti-mixing
- Pattern-Key: content.phase_before_model_selection
- Recurrence-Count: 1
- First-Seen: 2026-07-13
- Last-Seen: 2026-07-13

---

## [LRN-20260713-005] best_practice

**Logged**: 2026-07-13T13:35:00+08:00
**Priority**: low
**Status**: resolved
**Area**: content-system

### Summary
用户提供 SRT 时，纯文字 Markdown 应兼容“带或不带毫秒”的时间码，并保留原字幕换行，不能依赖标点自动合段。

### Details
平台导出的 SRT 时间码可能是 `00:00:00 --> 00:00:02`，也可能带毫秒。自动字幕也常没有句末标点；若按标点合并会变成难读的超长段落。兼容两种时间码并逐条保留字幕行，能在不改写原文的前提下生成更适合阅读和后续拆解的纯文字稿。

### Suggested Action
后续将用户提供的 SRT 直接转为文案时，清除序号、时间码和字幕标签，只保留文字与原字幕换行；原始 SRT 永远保留。

### Metadata
- Source: error
- Related Files: 01_工具_采集转写分析/convert_srt_folder_to_plain_md.py
- Tags: srt, transcript, plain-text, subtitle-format
- Pattern-Key: transcript.srt_optional_milliseconds_and_line_rhythm
- Recurrence-Count: 1
- First-Seen: 2026-07-13
- Last-Seen: 2026-07-13

---

## [LRN-20260713-006] correction

**Logged**: 2026-07-13T14:20:00+08:00
**Priority**: high
**Status**: resolved
**Area**: content-system

### Summary
对标文案学习系统应把用户提供的 SRT 当作最终文案、把每个账号当作统一风格，并按账号加结构模型检索，而不是按文本可靠度、事实风险或账号阶段路由。

### Details
用户明确后续提供的 SRT 已完全正确，关注点是观众感受到的情绪价值、说服力、结构和语言习惯，而不是常规事实风险审计或账号阶段差异。原有阶段化选择器会让未来写稿额外选择早期/成熟期，增加不必要的复杂度。新机制统一为：主题、受众、目标、情绪 → 主账号 → 主结构模型 → 最多两项辅助能力。

### Suggested Action
后续对标账号使用 `douyin-benchmark-script-learning` 生成纯文字文案、逐条机制索引、统一风格指纹和模型目录；注册到认知写稿 skill 时只声明 `style_scope: unified_account`，不创建阶段字段。

### Metadata
- Source: user_feedback
- Related Files: C:/Users/NJ/.codex/skills/douyin-benchmark-script-learning/SKILL.md, C:/Users/NJ/.codex/skills/douyin-cognition-script-builder/scripts/select_benchmark_styles.py
- Tags: benchmark-library, unified-style, model-retrieval, srt
- Pattern-Key: content.unified_account_model_retrieval
- Recurrence-Count: 1
- First-Seen: 2026-07-13
- Last-Seen: 2026-07-13

---

## [LRN-20260713-007] correction

**Logged**: 2026-07-13T15:10:00+08:00
**Priority**: high
**Status**: resolved
**Area**: content-system

### Summary
用户提供的 SRT 进入对标文案库时，最终 Markdown 必须是补齐标点、合并字幕碎片并按语义分段的可读稿，不能只保留逐条字幕换行。

### Details
逐 cue 文本虽然便于机械转换，却不适合长文案拆解：钩子、论证链、转折和节奏会被碎行掩盖。对照视频人工终审稿的阅读体验后，用户明确要求 SRT 文案沿用“标题＋完整文案＋自然段”的结构。此规则适用于后续所有对标账号。

### Suggested Action
`douyin-benchmark-script-learning` 先生成可读 Markdown 草稿，再完成语义级句读和分段复核；校验脚本须同时检查无时间码、句末标点和自然分段。

### Metadata
- Source: user_feedback
- Related Files: C:/Users/NJ/.codex/skills/douyin-benchmark-script-learning/SKILL.md, C:/Users/NJ/.codex/skills/douyin-benchmark-script-learning/scripts/convert_srt_folder_to_readable_md.py
- Tags: srt, readable-transcript, punctuation, paragraphing, benchmark-analysis
- Pattern-Key: content.srt_readable_semantic_transcript
- Recurrence-Count: 1
- First-Seen: 2026-07-13
- Last-Seen: 2026-07-13

---

## [LRN-20260713-008] correction

**Logged**: 2026-07-13T16:00:00+08:00
**Priority**: high
**Status**: resolved
**Area**: content-system

### Summary
对标语言学习不能只检索结构模型；写稿前必须加载“正文限定的语言指纹”和一个相关正文锚点，并以成人表达质检约束最终句子。

### Details
用户指出旧写稿结果虽然调用了对标结构，仍频繁出现排比、身份升级、空泛金句和课堂式强调，说明“钩子/论证/节奏”检索不足以迁移字里行间的表达。另行澄清：最终文案 Markdown 必须只保留带标点、自然分段的纯正文；不得保留标题、Markdown 标题、作品信息或校订备注。此前 LRN-20260713-004 的阶段路由已被 LRN-20260713-006 的统一账号规则取代；LRN-20260713-007 中“标题＋完整文案”的表述也以本条为准。

### Suggested Action
为每个可调用账号建立语言指纹：成人关系、段落呼吸、主张如何由场景/因果支撑、转折功能、排比边界和禁止表层习惯。检索器输出语言控制与正文锚点 ID；写稿 skill 在成稿前逐段检查唯一功能、支撑来源、短句用途、重复句式和未赚得的情绪。解析旧终审稿时，仅提取指定“完整文案”正文区段。

### Metadata
- Source: user_feedback
- Related Files: C:/Users/NJ/.codex/skills/douyin-benchmark-script-learning/SKILL.md, C:/Users/NJ/.codex/skills/douyin-cognition-script-builder/SKILL.md, 05_内容资产库/05_对标账号风格库/如果说/04_语言风格指纹.json
- Tags: language-fingerprint, adult-voice, benchmark-retrieval, pure-script-markdown
- Pattern-Key: content.language_profile_before_drafting
- Recurrence-Count: 1
- First-Seen: 2026-07-13
- Last-Seen: 2026-07-13
- See Also: LRN-20260713-006, LRN-20260713-007

---
## [LRN-20260713-009] correction

**Logged**: 2026-07-13T18:30:00+08:00
**Priority**: high
**Status**: promoted
**Area**: docs

### Summary
对标文案学习不能只记录钩子类别；每个账号必须建立独立开头表达指纹，并在写稿时检索开头家族、情绪按钮和承接路径。

### Details
前几秒留存依赖的不只是“反常识、提问、结果承诺”等粗标签，还包括第一拍如何截停、第二拍如何让观众照见自己、第三拍留下什么答案或收益，以及正文何时首次兑现。可复用的“固定表达”应保存为带变量槽位的功能骨架，不保存对标原句。真实3秒/5秒留存和完播率必须与点赞、收藏分栏；没有留存数据时只能描述高留存倾向，不能把互动量当作留存因果。

### Suggested Action
未来每个对标账号都产出独立开头表达指纹；逐视频索引记录前3秒功能、前8秒路径、主情绪按钮、共鸣触发、语言锋利来源、答案缺口、正文首次兑现和转译骨架。写稿选择主账号和结构模型后，再选一个开头家族并通过12分质量门槛。

### Metadata
- Source: user_feedback
- Related Files: C:/Users/NJ/.codex/skills/douyin-benchmark-script-learning/SKILL.md, C:/Users/NJ/.codex/skills/douyin-cognition-script-builder/SKILL.md, 05_内容资产库/02_钩子库/高留存开头表达手册.md
- Tags: douyin, opening-retention, hook-family, emotional-value, benchmark-retrieval
- Pattern-Key: content.opening_profile_before_drafting
- Recurrence-Count: 1
- First-Seen: 2026-07-13
- Last-Seen: 2026-07-13
- Promoted: douyin-benchmark-script-learning, douyin-cognition-script-builder

### Resolution
- **Resolved**: 2026-07-13T18:30:00+08:00
- **Notes**: 已新增两账号开头表达指纹、通用开头手册、对标分析契约、检索器开头家族输出和写稿质量门槛，并通过实际检索测试。

---

## [LRN-20260714-001] best_practice

**Logged**: 2026-07-14T00:10:00+08:00
**Priority**: high
**Status**: resolved
**Area**: content-system

### Summary
对标账号必须把“语料与逐视频证据”和“可调用风格包”分开放置，注册表只指向中央风格包。

### Details
“如果说”较早完成，风格包已在内容资产库；“小五狼”后来完成时，说明书和各类指纹仍留在账号项目，造成同类文件的物理位置不一致。虽然绝对路径能让选择器正常工作，但会降低维护效率，也不利于用户理解哪些内容可直接调用。

### Suggested Action
固定目录：`02_账号项目/<账号>` 仅保存原始 SRT、纯正文、逐视频拆解与验收；`05_内容资产库/05_对标账号风格库/<账号>` 保存统一风格指纹、说明书、语言指纹与开头表达指纹。每次迁移后更新注册表和指纹内部路径，并运行语料校验、路径解析与检索测试。

### Metadata
- Source: user_feedback
- Related Files: C:/Users/NJ/.codex/skills/douyin-benchmark-script-learning/SKILL.md, C:/Users/NJ/.codex/skills/douyin-benchmark-script-learning/references/output-contract.md, 05_内容资产库/05_对标账号风格库/registry.json
- Tags: benchmark-library, directory-contract, callable-style-package, evidence-separation
- Pattern-Key: content.central_style_pack_and_local_evidence
- Recurrence-Count: 1
- First-Seen: 2026-07-14
- Last-Seen: 2026-07-14

---

## [LRN-20260714-002] best_practice

**Logged**: 2026-07-14T00:30:00+08:00
**Priority**: high
**Status**: resolved
**Area**: content-system

### Summary
静态语言指纹不足以迁移高级表达；每个可调用账号还需提供逐段语言示范，并在写稿检索时按主题返回对应示范段与正文锚点。

### Details
仅记录句长、转折和禁用语，仍容易让写稿停留在泛化的“克制、有节奏”描述。逐段示范把每段承担的推进动作、信息密度、句子呼吸和转折时机变成可执行校准对象。写稿时先用结构模型搭建论证，再逐段对照示范完成第二遍语言修订，才能学到表达的质感而不是表层句式。

### Suggested Action
今后每个对标账号的中央风格包必须含 `06_代表正文逐段语言示范.md`，指纹声明该路径，校验器检查文件和正文锚点，选择器按主题排序并返回示范段与正文锚点；认知类写稿 skill 必须把它们写进对标能力调用记录。

### Metadata
- Source: user_feedback
- Related Files: C:/Users/NJ/.codex/skills/douyin-benchmark-script-learning/SKILL.md, C:/Users/NJ/.codex/skills/douyin-cognition-script-builder/SKILL.md, C:/Users/NJ/.codex/skills/douyin-cognition-script-builder/scripts/select_benchmark_styles.py
- Tags: benchmark-language, paragraph-rhythm, style-retrieval, adult-voice
- Pattern-Key: content.paragraph_demo_before_drafting
- Recurrence-Count: 1
- First-Seen: 2026-07-14
- Last-Seen: 2026-07-14

### Resolution
- **Resolved**: 2026-07-14T00:30:00+08:00
- **Notes**: 已为“如果说”和“小五狼”补齐代表正文逐段语言示范，接入统一指纹、语料校验和主题检索。

---

## [LRN-20260714-003] best_practice

**Logged**: 2026-07-14T01:10:00+08:00
**Priority**: high
**Status**: resolved
**Area**: content-system

### Summary
每个可调用结构模型必须绑定代表语言示范和正文锚点，不能只让写稿器按主题从全部样本中猜选。

### Details
同一账号会有多种有效结构。若模型与正文锚点没有强制对应，写稿器即使选对账号，也可能借错段落推进，从而重新滑向泛化模板。用 `representative_demo_coverage` 将模型 ID 映射到语言指纹锚点，并让选择器优先返回该锚点，能让“结构选择—语言学习—段落修订”成为一条连续链路。

### Suggested Action
未来每个对标账号在可调用前，必须补齐所有模型的覆盖映射；校验器检查模型、锚点和示范段三者完整对应，写稿选择器优先返回模型指定锚点。

### Metadata
- Source: audit
- Related Files: C:/Users/NJ/.codex/skills/douyin-benchmark-script-learning/scripts/validate_benchmark_corpus.py, C:/Users/NJ/.codex/skills/douyin-cognition-script-builder/scripts/select_benchmark_styles.py
- Tags: benchmark-model, language-anchor, retrieval, paragraph-demo
- Pattern-Key: content.model_to_language_demo_coverage
- Recurrence-Count: 1
- First-Seen: 2026-07-14
- Last-Seen: 2026-07-14

### Resolution
- **Resolved**: 2026-07-14T01:10:00+08:00
- **Notes**: “如果说”5个模型和“小五狼”4个模型均已完成锚点映射，并通过五类选题路由测试。

---

## [LRN-20260714-004] best_practice

**Logged**: 2026-07-14T01:10:00+08:00
**Priority**: high
**Status**: resolved
**Area**: content-system

### Summary
当用户声明 SRT 是终审原文时，转写工具只能恢复标点和分段，且默认不得覆盖已有 Markdown。

### Details
任何“高概率纠错”都会把用户确认过的原文重新变成机器猜测；无提示覆盖则可能直接毁掉人工整理的最终文案。两者都会污染后续风格学习。

### Suggested Action
转换器保持零词语替换，并要求显式 `--overwrite` 才能重建已有 Markdown；不带标点的旧转换器不得保留在可调用脚本目录。

### Metadata
- Source: audit
- Related Files: C:/Users/NJ/.codex/skills/douyin-benchmark-script-learning/scripts/convert_srt_folder_to_readable_md.py
- Tags: srt, transcript, source-preservation, overwrite-protection
- Pattern-Key: content.final_srt_preservation
- Recurrence-Count: 1
- First-Seen: 2026-07-14
- Last-Seen: 2026-07-14

### Resolution
- **Resolved**: 2026-07-14T01:10:00+08:00
- **Notes**: 已移除词语替换和旧的无标点转换器；安全覆盖测试通过。

---
