# JUnit5 SpotBugs 指导文档验证

验证日期：2026-11-12（Asia/Shanghai）。

## 结论

**文档不能直接套用于 junit5；补充构建系统适配及源码路径规范化后，扫描、私有插件检出、OIDC、OBS、回调链路已实测通过。** 主要缺口是 Maven 前提未充分突出、缺少 Gradle 多模块示例，以及“自动补齐代码片段”在同名文件下缺少准确性保证。

最终运行：[43181767000](https://github.com/openlibing-test/junit5/actions/runs/43181767000)，实测工作流提交 `de64575779d04cdd59a5aec409f1d0e0c038314c`。

| 验收项 | 实测结果 |
| --- | --- |
| Gradle 生产代码编译 | 成功，19 个 main 源集模块，20 个非空 Java/Kotlin 字节码目录 |
| SpotBugs | 4.10.2，FindSecBugs 1.14.0 扩展已加载 |
| SARIF | JSON 基本结构与 2.1.0 版本字段检查通过，379 条结果、43 类规则；未执行完整 JSON Schema 校验 |
| 结果级别 | 1 error、30 warning、348 note；未人工确认是否为真实缺陷 |
| 私有插件 | 组织级 PRIVATE_ACTIONS_READ_TOKEN 可用，固定提交检出成功 |
| OIDC/STS 与 OBS | 成功 |
| APIG 回调 | `code:200,msg:success,data:6af577194d68030f7694a627` |
| 源码片段 | 329/329 条有效源码行号结果完全匹配，零缺失或错误 |
| 位置质量限制 | 47 条无行号，3 条 Kotlin 行号超出源文件，原样保留并披露 |
| openLiBing 页面 | 未验证 UI 最终展示 |

## 验证对象与方法

- 指导文档：<https://gitcode.com/openlibing/docs/tree/github-static-analysis/static-code-analysis/solutions/full-analysis/tools/spotbugs>
- 文档固定提交：`69df05f3c175d0e10710df253ba9931d5dda431f`。
- 目标仓库：<https://github.com/openlibing-test/junit5>。
- 目标初始提交：`13e10545e`，Gradle 9.9.0，多模块，默认 Java toolchain/Gradle daemon Java 25。
- 验证分支：`validation/spotbugs-docs`。
- 用户确认先用组织 Secret `PRIVATE_ACTIONS_READ_TOKEN` 检出私有上传插件；插件公开后可移除这一临时步骤。
- 上传插件固定提交：`0fd322c74908e464f6df593b0a914f66fc287482`。

验证区分原文命令的可直接使用性、Gradle 适配后的字节码扫描与 SARIF、OIDC/OBS/回调三个层次。Gradle 适配结果不等价于 Maven 插件配置经过验证。

## 已确认的原文问题和适用范围

1. **补充 Maven 前提及 Gradle 分支。** 文档以 Java 集成指南命名，但工作流要求根目录 `pom.xml`。在 junit5 执行 `mvn -B clean package -DskipTests` 实际报 `The goal you specified requires a project to execute but there is no POM in this directory`。这是构建系统不匹配，不能靠增加 Maven 或 JDK 修复。应明确该示例适用于 Maven 项目，并提供 Gradle 多模块编译、依赖类路径和报告输出方式。
2. **JDK 版本应按项目要求。** 示例 Java 21 不是适用于所有 Java 仓库的固定值。本仓构建守护进程和默认 toolchain 为 25，适配工作流使用 Java 25。
3. **多模块产物及源码根目录不能固定为根目录 target/classes、src/main/java。** Gradle 适配扫描生产模块 main 源集，依赖通过 compileClasspath 导出；聚合模块可能没有 main 源集。应列出模块范围、字节码目录和辅助类路径，并避免同名源文件兜底匹配产生误定位。
4. **if: always() 不检查报告是否存在。** GitHub 示例在编译或扫描失败后仍尝试上传。建议扫描后校验 JSON/版本/runs 并设输出标志，再用 `if: ${{ !cancelled() && steps.verify.outputs.ready == 'true' }}` 控制上传；构建失败日志独立归档。
5. **上传成功不等于平台问题已可见。** 插件回调失败只 WARN，不能凭 Actions 绿色判断平台入库完成。验收需分别记录 SARIF 生成、OBS 上传、回调响应、平台展示。文档 FAQ 已提到回调只告警，但主流程验收标准应同步强调。
6. **临时私有仓访问说明。** 组织 Secret 必须授予 junit5 使用范围，token 必须具有上传插件仓读取权限。checkout 到独立目录后 `uses: ./...` 调用，设置 `persist-credentials: false`。插件公开后恢复直接引用。OIDC 上传权限与检出私有仓权限是两个独立要求。
7. **PR OIDC 说明需要准确区分事件 subject。** 默认 `pull_request` subject 与普通分支 push subject 不同；同仓 PR 也不能仅因非 fork 就认定符合仅接受分支 subject 的策略。本次验证通过同仓分支 push 执行，不声称验证过 PR 或定时触发。依据：[GitHub 官方 OIDC subject 说明](https://docs.github.com/en/actions/reference/security/oidc#example-subject-claims)。
8. **代码片段“已补齐”需要校验实际源码。** `source_path: .` 在本仓存在同名文件时触发 basename 兜底，首轮成功上传的 379 条结果中：329 条具备有效源码行号，322 条片段正确、4 条片段错误、3 条片段未补齐。例如 `org/junit/jupiter/api/MediaType.java:122` 被补成另一 `MediaType.java` 的 `}`，实际应为构造器声明。应在上传前把包相对 URI 解析为唯一的仓库相对路径，并在上传后逐条核对片段与源码行。
9. **无行号/跨语言字节码映射应作为数据质量限制披露。** 实测 47 条没有 `startLine`，3 条 Kotlin `Assertions.kt` 的行号超出当前源文件范围。源码可读不代表所有结果都能补上下文。379 是工具结果数，不等于人工确认的缺陷数；本次覆盖 main 源集的 Java/Kotlin 字节码，不包含测试源集。

## 运行证据

| 运行 | 版本 | 已确认结果 |
| --- | --- | --- |
| [43180496640](https://github.com/openlibing-test/junit5/actions/runs/43180496640) | `937cccbef` | 原文 Maven 编译因缺少 POM 失败；适配脚本误纳入无 main 源集聚合模块而失败，属于验证脚本自身问题，已单独修正。 |
| [43180856442](https://github.com/openlibing-test/junit5/actions/runs/43180856442) | `a7a5df38c` | 整体成功。19 个生产 Java 模块、20 个非空字节码目录，SpotBugs 4.10.2 输出 SARIF 2.1.0，379 条结果、43 类规则。组织 Secret 检查、私有 action 检出、OIDC/STS、OBS 上传、回调均成功。回调返回 `code:200,msg:success`。后续产物审计发现 7 条有效行号结果的片段缺失/错误。 |
| [43181767000](https://github.com/openlibing-test/junit5/actions/runs/43181767000) | `de6457577` | 整体成功。上传前规范化源码路径、上传后检查所有有效行号对应片段；379 条结果保持不变，329 条有效源码片段全部正确。OBS 上传成功、回调 `code:200`，无回调 WARN。 |

首轮失败日志：`run-43180496640-failed.log`。首个完整成功运行日志及元数据：`run-43180856442.log`、`run-43180856442.json`。下载产物：`artifacts-43180856442/`。

最终日志、元数据：`run-43181767000.log`、`run-43181767000.json`；最终 SARIF 和统计：`artifacts-43181767000/reports/spotbugs/spotbugs.sarif`、`summary-after-upload.json`；模块和字节码目录清单位于 `artifacts-43181767000/spotbugs-inputs/`。以上均保存在工作区 `validation-results/junit5-spotbugs/`，GitHub 运行页亦保留同名 `spotbugs-verification` artifact。

离线复核直接使用固定提交上传插件中的源码补齐函数，没有执行认证/上传入口。对首次上传产物执行 `verify-sarif.py --after-upload`，稳定检出上述 7 条不匹配；URI 规范化后，再运行同一个插件函数和校验器，329/329 条有效行号的源码片段全部正确，且未触发 basename 兜底。

## 当前验收边界

- 原版 Maven 工作流在 junit5 不能直接运行，此结论已有实际失败日志。
- Gradle 适配验证的是同版本 SpotBugs 核心及 FindSecBugs 扩展，不是 Maven 插件 `4.9.8.3` 的全部参数或 `spotbugs:check` 门禁语义；本仓没有因此新增业务 `pom.xml`。
- 回调 `code:200` 证明接口接受本次结果，未登录 openLiBing UI 核实 379 条问题的最终展示，不声称已完成前端验收。
- 本次使用 GitHub 托管 Ubuntu runner 和同仓分支 push，不验证 GitCode runner、PR、fork PR、schedule 或本地 pre-commit。
- 原文对照在最终工作流中通过显式断言“预期缺少 POM 导致失败”作为成功条件；这不代表原文 Maven 构建成功。第一次原文实际失败运行始终保留可追溯。

## 已交付配置及后续使用

- [工作流](https://github.com/openlibing-test/junit5/blob/validation/spotbugs-docs/.github/workflows/spotbugs-java.yml)：GitHub 托管 Ubuntu、Java 25、原文 Maven 对照与 Gradle 适配两个作业。
- [Gradle init 脚本](https://github.com/openlibing-test/junit5/blob/validation/spotbugs-docs/.github/spotbugs/analysis.init.gradle)：不修改原生产构建脚本，编译并导出生产 main 字节码、compileClasspath、模块清单。
- [SARIF 校验与路径规范化](https://github.com/openlibing-test/junit5/blob/validation/spotbugs-docs/.github/spotbugs/verify-sarif.py)：上传前解析唯一源码路径，上传后逐条比对实际源码片段。
- 工作流目前保留在验证分支，push 路径过滤仅覆盖工作流和验证脚本；报告更新不会重新触发扫描。workflow_dispatch 保留，但在工作流进入默认分支前，应使用分支 push 触发。
- 插件公开后，移除私有仓 checkout 和 Secret 可用性检查，将本地 action 引用改为 `uses: openlibing-test/upload-sarif-action@0fd322c74908e464f6df593b0a914f66fc287482`（或经团队确认的公开发布版本）；保留 `id-token: write`、源码路径规范化、上传后校验和 artifact 归档。
- 验证期间没有修改上传插件仓、组织 Secret、组织策略或 junit5 默认分支。
