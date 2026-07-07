<!-- BEGIN ican-assistant (managed by scripts/install-codex.sh — do not edit inside this block) -->
## iCan 办公副手（ican-assistant）

- **邮件只走 Apple Mail**：所有邮件意图（包括「飞书邮箱 / Feishu Mail」，以及多步工作流里的
  发邮件步骤）一律使用 `local-email` skill 的引擎 `scripts/mail.py`（位于该 skill 目录内，
  用 `python3` 运行）。`lark-mail` / `lark-cli mail` 已停用，禁止把任何邮件请求路由过去。
- **办公请求走 office-router**：邮件 / 飞书文档 / 日历 / 任务 / IM / 多维表格 / 电子表格 /
  妙记 / 审批 / OKR 等请求，以及多步办公工作流（gather → process → act），用 `office-router`
  skill 分诊与编排，由它委托给对应的 `lark-*` skill 或 `local-email`。
- **飞书以本人身份运行**：`lark-cli` 需一次性 `lark-cli auth login` +
  `lark-cli config default-as user`。调用报身份/授权错误时先 `lark-cli whoami`，提示用户重新
  登录；不要静默回退到 bot 身份。
- **对外动作先确认**：发送/回复邮件、发 IM 消息、创建或修改日历日程与任务、删除/移动邮件、
  共享文档等对外或破坏性操作，执行前必须向用户确认；邮件发送意图不明时先 `--draft` 存草稿。
  遵守 `lark-cli` 的风险分级，绝不自动确认 `high-risk-write`。
<!-- END ican-assistant -->
