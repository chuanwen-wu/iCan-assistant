# 开发协作流程

本仓库是 `ican-assistant` Claude Code 插件（同时自带 marketplace）。需求、Bug 和版本迭代都在
GitHub 上管理。

## 提需求 / 报 Bug

- 用 Issue 模板（[功能需求](ISSUE_TEMPLATE/feature_request.md) / [Bug 上报](ISSUE_TEMPLATE/bug_report.md)），不接受空白 Issue。
- 打好标签：`feature` / `bug` + 优先级 `P0` / `P1` / `P2` + 模块 `area:router` / `area:mail` / `area:lark`。
- 版本规划用 **Milestone**（如 `v0.2.0`）：把纳入该版本的 Issue 挂到对应 milestone。

## 开发流程

1. 从 Issue 出发建分支：`feat/<issue号>-简述` 或 `fix/<issue号>-简述`。
2. 开发并按 CLAUDE.md 要求本地测试（本地路径市场安装/更新，模拟用户使用）。
3. 提 PR，模板里 `closes #<issue号>` 关联 Issue，勾完测试与检查项。
4. CI 通过（manifest 校验、脚本语法、SKILL/command frontmatter、lark MCP 防回归）后合并到 `main`。

## 版本发布

版本号在 `.claude-plugin/plugin.json` 的 `version`（semver）。

1. 该 milestone 的 Issue 全部关闭后，提一个 bump 版本号的 PR（或直接提交）。
2. 打 tag 并推送：`git tag v<版本号> && git push origin v<版本号>`。
3. `release.yml` 会校验 tag 与 `plugin.json` 版本一致，然后自动创建 GitHub Release（自动生成 changelog）。
4. 用户侧执行 `/plugin update` 即可拉到新版本。

## 红线（同 CLAUDE.md）

- 不引入 lark MCP（`mcp__lark__*` / `.mcp.json` / `lark-mcp.sh`）。
- 邮件只走 Apple Mail，飞书邮箱（`lark-cli mail`）保持停用。
- 对外动作（发邮件/IM、建日程、删改数据）必须保留用户确认门槛。
