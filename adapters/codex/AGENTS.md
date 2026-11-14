<!-- BEGIN ican-assistant (managed by scripts/install-codex.sh — do not edit inside this block) -->
## iCan 办公副手（ican-assistant）

- **邮件默认走 iCan 网页**：使用 `ican-web` skill，在已登录的浏览器中打开
  `https://icanplatform.feishu.cn/mail` 读取/搜索、草拟、发送/回复/转发邮件及操作邮箱。
  回复/转发使用网页中的原邮件或会话，不切换到 Apple Mail 匹配原信。
- **聊天读取走 iCan 网页**：使用 `ican-web` 打开
  `https://icanplatform.feishu.cn/next/messenger/` 查看个人/群会话列表及聊天消息。
- **不静默切换后端**：普通邮件不使用 Apple Mail、`lark-mail` / `lark-cli mail`；聊天读取不以
  `lark-im` API 结果代替。遇到登录页或浏览器工具不可用时明确告知用户。`local-email` 及
  `scripts/mail.py` 只用于用户明确要求的本地 Apple Mail 操作。发送 IM 及群管理使用 `lark-im`。
  网页会话/邮件行标识不可直接当作旧脚本或 API 的消息 ID。
- **办公请求走 office-router**：邮件 / 飞书文档 / 日历 / 任务 / IM / 多维表格 / 电子表格 /
  妙记 / 审批 / OKR 等请求，以及多步办公工作流（gather → process → act），用 `office-router`
  skill 分诊与编排，由它委托给 `ican-web`、对应的 `lark-*` skill 或 `local-email`。
- **飞书以本人身份运行**：`lark-cli` 需一次性 `lark-cli auth login` +
  `lark-cli config default-as user`。调用报身份/授权错误时先 `lark-cli whoami`，提示用户重新
  登录；不要静默回退到 bot 身份。
- **对外动作先确认**：发送/回复邮件、发 IM 消息、创建或修改日历日程与任务、删除/移动邮件、
  共享文档等对外或破坏性操作，执行前必须向用户确认；邮件发送意图不明时在网页准备草稿并核查
  保存状态。发送结果不确定时先核查网页结果，不重复点击发送或切换后端重发。
  遵守 `lark-cli` 的风险分级，绝不自动确认 `high-risk-write`。
<!-- END ican-assistant -->
