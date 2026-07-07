---
name: Bug 上报
about: 插件行为异常、路由错误、脚本报错等缺陷
title: "[Bug] "
labels: bug, needs-review
---

## 现象
<!-- 看到了什么不对？最好附上会话截图或关键输出 -->


## 复现步骤
<!-- 你对 agent 说了什么 / 执行了什么命令 -->
1.
2.
3.

## 期望行为
<!-- 应该路由到哪个后端 / 应该产生什么结果？ -->


## 实际行为
<!-- 实际路由/输出/报错是什么？粘贴报错原文 -->


## 涉及模块
- [ ] office-router（意图分类/路由/编排）
- [ ] local-email / `skills/local-email/scripts/mail.py`（Apple Mail）
- [ ] 飞书后端（lark-cli / lark-* skill）
- [ ] 插件安装 / 更新 / marketplace
- [ ] 文档（README / SKILL.md）

## 环境
- macOS 版本：
- Claude Code 版本（`claude --version`）：
- 插件版本（`/plugin` 里查看，或 plugin.json version）：
- lark-cli 版本（如涉及飞书）：
- 宿主 Agent（Claude Code / 其他）：

## 影响范围
- [ ] 偶发，可绕过
- [ ] 稳定复现，功能不可用
- [ ] 产生了错误的对外动作（误发邮件/IM、误删邮件等）
