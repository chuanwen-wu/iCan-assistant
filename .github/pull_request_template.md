## 关联 Issue
closes #

## 变更内容
-

## 测试（对应 CLAUDE.md 测试要求）
- [ ] CI 通过（manifest 校验 / 脚本语法 / frontmatter 检查）
- [ ] 本地市场安装或 `/plugin update` 后重启会话，模拟用户主流程验证
- [ ] 涉及 `scripts/mail.py` 的变更已在真机 Apple Mail 上手动验证
- [ ] 涉及飞书的变更已用本人身份（`lark-cli` user）验证

## 检查项
- [ ] 未引入 lark MCP（`mcp__lark__*` / `.mcp.json` / `lark-mcp.sh`）
- [ ] 未把邮件意图路由回 `lark-cli mail`（飞书邮箱保持停用）
- [ ] 对外动作（发邮件/IM、建日程、删改数据）保留用户确认门槛
- [ ] 如属功能变更，已同步 bump `plugin.json` 的 `version`

## 风险点 / 需要 Reviewer 注意的地方
