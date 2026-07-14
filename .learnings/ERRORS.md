# Errors

Command failures and integration errors.

---

## [ERR-20260713-002] skill_creator_interface_arguments

**Logged**: 2026-07-13T14:20:00+08:00
**Priority**: low
**Status**: resolved
**Area**: config

### Summary
`init_skill.py` requires one repeated `--interface key=value` argument per UI field, and validates the short description length after creating the base skill folder.

### Error
```text
unrecognized arguments: short_description=... default_prompt=...
short_description must be 25-64 characters
```

### Context
- Created a local Codex skill with display name, short description, and default prompt.
- The first invocation supplied multiple interface values after one flag; the second created the folder but rejected a 22-character description.

### Suggested Fix
Pass `--interface` once for each field. Use a 25-64 character short description, and use `generate_openai_yaml.py` to complete UI metadata after partial initialization.

### Metadata
- Reproducible: yes
- Related Files: C:/Users/NJ/.codex/skills/.system/skill-creator/scripts/init_skill.py

### Resolution
- **Resolved**: 2026-07-13T14:20:00+08:00
- **Notes**: Regenerated `agents/openai.yaml` with valid repeated interface values.

---

## [ERR-20260713-003] invalid_workdir_typo

**Logged**: 2026-07-13T14:25:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
一次只读防照搬扫描因工作目录路径拼写错误而未启动。

### Error
```text
Io(Os { code: 267, kind: NotADirectory, message: "目录名称无效。" })
```

### Suggested Fix
在调用前复用已验证的工作区绝对路径；失败后重新运行只读校验，不把失败结果当作验证依据。

### Metadata
- Reproducible: no
- Related Files: none

### Resolution
- **Resolved**: 2026-07-13T14:25:00+08:00
- **Notes**: 使用正确工作目录后，连续原句扫描通过。

---

## [ERR-20260713-001] skill_validator_windows_encoding

**Logged**: 2026-07-13T12:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: config

### Summary
`quick_validate.py` used the Windows default GBK codec and failed to read a UTF-8 Chinese skill file.

### Error
`UnicodeDecodeError: 'gbk' codec can't decode byte ...`

### Context
- Skill validation of a Chinese-language local skill on Windows.
- The skill file was valid UTF-8; the validator used `Path.read_text()` without an explicit encoding.

### Suggested Fix
Run the validator with `PYTHONUTF8=1` in this environment, or update the validator to read UTF-8 explicitly when that tool is locally maintained.

### Metadata
- Reproducible: yes
- Related Files: C:/Users/NJ/.codex/skills/.system/skill-creator/scripts/quick_validate.py

### Resolution
- **Resolved**: 2026-07-13T12:00:00+08:00
- **Notes**: Validation succeeded with `PYTHONUTF8=1`.

---

## [ERR-20260628-001] rg-windowsapps-access-denied

**Logged**: 2026-06-28T09:07:29.6150967+08:00
**Priority**: low
**Status**: resolved
**Area**: config

### Summary
`rg.exe` can fail to start in the Codex desktop WindowsApps runtime with an access denied error.

### Error
```text
Program 'rg.exe' failed to run ... WindowsApps ... 拒绝访问。
```

### Context
- Command attempted: `rg -n "<pattern>" <path>`
- Environment: Codex desktop app on Windows, PowerShell shell.
- Fallback used: PowerShell `Select-String` for text search.

### Suggested Fix
When `rg` is blocked by WindowsApps permissions, use `Select-String -Path <path> -Pattern <pattern>` as the immediate fallback.

### Metadata
- Reproducible: unknown
- Related Files: C:\Users\NJ\.codex\skills\douyin-editing-director\SKILL.md

### Resolution
- **Resolved**: 2026-06-28T09:07:29.6150967+08:00
- **Notes**: Continued the task with `Select-String`; no code or skill output depended on `rg`.

---

## [ERR-20260613-001] skill-quick-validate-encoding

**Logged**: 2026-06-13T18:46:52.3010083+08:00
**Priority**: medium
**Status**: resolved
**Area**: docs

### Summary
`quick_validate.py` can fail on Windows when Python defaults to GBK while reading UTF-8 skill files.

### Error
```text
UnicodeDecodeError: 'gbk' codec can't decode byte ...
```

### Context
- Command attempted: `python C:\Users\NJ\.codex\skills\.system\skill-creator\scripts\quick_validate.py <skill-folder>`
- Affected files were UTF-8 `SKILL.md` files containing Chinese text.
- Setting `PYTHONUTF8=1` before running the same validation command made both skill validations pass.

### Suggested Fix
Run skill validation on Windows with `$env:PYTHONUTF8='1'; python ...` when validating UTF-8 skill files, or update the validator to read text with an explicit UTF-8 encoding.

### Metadata
- Reproducible: yes
- Related Files: C:\Users\NJ\.codex\skills\.system\skill-creator\scripts\quick_validate.py

### Resolution
- **Resolved**: 2026-06-13T18:46:52.3010083+08:00
- **Notes**: Re-ran validation with `PYTHONUTF8=1`; both updated skills passed.

---

## [ERR-20260713-004] local_punctuation_model_install

**Logged**: 2026-07-13T15:10:00+08:00
**Priority**: low
**Status**: resolved
**Area**: infra

### Summary
尝试在 Windows 本地环境安装中文断句模型依赖时，被正在占用的 Python 包文件阻断。

### Error
```text
WinError 32: another process was using a numba package file.
```

### Context
- 目的：为长 SRT 补齐标点和自然段。
- 后续尝试已发现自动模型还需要与当前 Torch 版本匹配的音频依赖。

### Suggested Fix
不把临时模型安装作为对标文案流程的必需依赖；优先使用无依赖的可读稿预处理和语义复核。若未来需要模型批处理，在隔离环境中安装版本匹配的完整依赖。

### Metadata
- Reproducible: unknown
- Related Files: C:/Users/NJ/.codex/skills/douyin-benchmark-script-learning/scripts/convert_srt_folder_to_readable_md.py

### Resolution
- **Resolved**: 2026-07-13T15:10:00+08:00
- **Notes**: 保留无外部模型依赖的工作流；原始 SRT 未受影响。

---

## [ERR-20260713-005] rg_windowsapps_access

**Logged**: 2026-07-13T16:10:00+08:00
**Priority**: low
**Status**: resolved
**Area**: infra

### Summary
当前 Codex Desktop 环境中的 `rg.exe` 因 WindowsApps 权限被拒绝启动。

### Error
```text
Program 'rg.exe' failed to run ... 拒绝访问。
```

### Context
- 目的：复查风格资产中遗留的排比、身份升级等旧字段。
- 环境：Windows PowerShell，工作目录为 Douyin 工作区。

### Suggested Fix
文本检索优先尝试 `rg`；若 WindowsApps 权限阻断，立即改用 PowerShell `Get-ChildItem ... | Select-String`，不阻塞内容资产复核。

### Metadata
- Reproducible: unknown
- Related Files: C:/Users/NJ/.codex/skills/douyin-cognition-script-builder/SKILL.md

### Resolution
- **Resolved**: 2026-07-13T16:10:00+08:00
- **Notes**: 已使用 `Select-String` 完成复查，并将旧指纹标记为不可调用。

---

## [ERR-20260714-006] skill_validator_windows_encoding

**Logged**: 2026-07-14T00:30:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
Windows 默认 GBK 环境下，skill-creator 的格式校验器读取 UTF-8 中文 SKILL.md 会报解码错误。

### Error
```text
UnicodeDecodeError: 'gbk' codec can't decode byte ...
```

### Suggested Fix
运行 `quick_validate.py` 前设置 `PYTHONUTF8=1`，再以 UTF-8 重跑；不要把该报错误判为 skill 内容损坏。

### Metadata
- Related Files: C:/Users/NJ/.codex/skills/.system/skill-creator/scripts/quick_validate.py
- Tags: windows, encoding, skill-validation

### Resolution
- **Resolved**: 2026-07-14T00:30:00+08:00
- **Notes**: 使用 UTF-8 环境后，两套自定义 skill 均通过格式校验。

---

## [ERR-20260714-007] broad_workspace_search_timeout

**Logged**: 2026-07-14T01:10:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
对整个工作区递归检索历史引用会超时，且不能提高当前可调用链的验证质量。

### Suggested Fix
检索引用时只覆盖资产库、注册表和两套相关 skill；账号项目历史归档按需单独检查。

### Resolution
- **Resolved**: 2026-07-14T01:10:00+08:00
- **Notes**: 已改用范围受控的检索完成风格包、旧指纹和转换脚本的引用校验。

---

## [ERR-20260714-008] subprocess_utf8_test_encoding

**Logged**: 2026-07-14T01:10:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
Windows Python 子进程默认编码会让 UTF-8 JSON 检索测试或 skill-creator 元数据生成器解码失败。

### Suggested Fix
需要在 Python 中读取子进程中文 JSON 时，向子进程传入 `PYTHONUTF8=1` 并显式指定 UTF-8。

### Metadata
- Reproducible: yes
- Related Files: C:/Users/NJ/.codex/skills/.system/skill-creator/scripts/generate_openai_yaml.py
- Pattern-Key: windows.python_utf8_subprocess
- Recurrence-Count: 2
- Last-Seen: 2026-07-14

### Resolution
- **Resolved**: 2026-07-14T01:10:00+08:00
- **Notes**: 五类选题路由测试与两套 skill 的 openai.yaml 生成均在设置 `PYTHONUTF8=1` 后通过。

---

## [ERR-20260714-009] bundled_rg_access_denied

**Logged**: 2026-07-14T01:38:20+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
Codex Desktop 捆绑的 `rg.exe` 在当前 Windows 环境中启动时报“拒绝访问”。

### Error
`Program 'rg.exe' failed to run ... 拒绝访问。`

### Context
- 尝试列出两个本地 skill 目录的文件。
- 失败发生在 Codex 应用 WindowsApps 路径下的捆绑可执行文件。

### Suggested Fix
先尝试 `rg`；遇到该权限错误时，立即改用 PowerShell `Get-ChildItem` 和 `Select-String`，并继续保持检索范围受控。

### Metadata
- Reproducible: yes
- Related Files: C:/Users/NJ/.codex/skills/douyin-benchmark-script-learning, C:/Users/NJ/.codex/skills/douyin-cognition-script-builder
- Pattern-Key: windows.codex_bundled_rg_access_denied
- Recurrence-Count: 1

### Resolution
- **Resolved**: 2026-07-14T01:38:20+08:00
- **Notes**: 已使用 PowerShell 原生检索完成全部盘点和冲突规则清理。

---
