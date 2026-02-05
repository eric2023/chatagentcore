# ChatAgentCore 开发规范智能体

> 本规范基于 Anthropic Skills 标准定义，用于规范化 ChatAgentCore 项目的开发流程。

---

## 概述

ChatAgentCore 开发规范智能体（Skill）是一个可复用的开发工作流规范，确保项目开发过程的一致性、可追溯性和质量可控。

## 目标

- 统一开发流程和工作方法
- 建立可复用的最佳实践库
- 实现任务跟踪和回溯能力
- 保证代码质量和项目文档完整性

## 适用场景

当需要进行以下操作时使用此智能体：
- 新功能开发
- 代码重构
- Bug 修复
- 技术选型决策
- 文档编写
- 测试覆盖

---

## 规范内容

### 1. 项目初始化

#### 技术栈选择原则
- 优先考虑团队熟悉度
- 评估生态系统成熟度
- 考虑性能和扩展性需求
- 验证社区支持和文档完整性

#### 目录结构规范
```
chatagentcore/
├── core/              # 核心对话引擎
├── adapters/          # LLM 适配器层
├── memory/            # 上下文和记忆管理
├── tools/             # 工具函数和插件
├── storage/           # 持久化存储
├── api/               # 外部接口
├── examples/          # 使用示例
├── tests/             # 测试套件
├── tasks/             # ⭐ 任务和计划跟踪
├── docs/              # ⭐ 技术文档
├── CLAUDE.md          # AI 上下文索引
└── README.md          # 项目说明
```

### 2. 开发流程

#### 六阶段工作流
1. **研究阶段 (Research)**
   - 收集需求和技术约束
   - 分析现有解决方案
   - 评估技术可行性

2. **构思阶段 (Brainstorm)**
   - 设计解决方案
   - 识别关键组件
   - 规划接口定义

3. **计划阶段 (Plan)**
   - 制定实施步骤
   - 识别依赖关系
   - 估算工作量

4. **执行阶段 (Execute)**
   - 编写代码实现
   - 单元测试覆盖
   - 代码审查

5. **优化阶段 (Optimize)**
   - 性能调优
   - 代码清理
   - 文档完善

6. **评审阶段 (Review)**
   - 功能验证
   - 质量检查
   - 经验总结

### 3. 任务跟踪规范

#### 任务创建
所有确定执行的任务和计划必须在 `tasks/` 文件夹中保存，文件命名格式：
```
tasks/YYYY-MM-DD-{任务摘要}.md
```

#### 任务模板
```markdown
# 任务标题

**创建日期:** YYYY-MM-DD
**状态:** pending/in_progress/completed
**优先级:** high/medium/low
**负责人:** [可选]

## 需求描述
[详细描述任务需求和目标]

## 实施计划
- [ ] 步骤 1
- [ ] 步骤 2
- [ ] 步骤 3

## 相关资源
- 链接 1
- 链接 2

## 参考文档
- [文档 A](../docs/doc-a.md)
```

### 4. 文档编写规范

#### 技术文档归档
所有技术文档应存放在 `docs/` 文件夹中，分类组织：
```
docs/
├── architecture/      # 架构设计
├── api/              # API 文档
├── guides/           # 使用指南
├── sop/              # SOP 流程
└── faq/              # 常见问题
```

#### 文档模板
```markdown
# 文档标题

**创建日期:** YYYY-MM-DD
**最后更新:** YYYY-MM-DD
**作者:** [作者名]

## 概述
[简要说明文档目的和范围]

## 详细内容
[技术细节、代码示例、图表等]

## 参考资料
- [参考链接]
```

### 5. 编码规范

#### 环境配置
- 前置依赖记录在 README.md
- 开发环境配置详细说明
- 调试运行方法清晰标注

#### 代码风格
- 遵循语言社区标准 (PEP 8 / ESLint)
- 类型检查启用 (TypeScript / mypy)
- 所有公共 API 包含文档字符串

#### 提交规范
遵循 Conventional Commits 规范：
```
feat: 新功能
fix: Bug 修复
docs: 文档更新
style: 代码格式（不影响代码运行）
refactor: 重构（既不是新增功能也不是修复bug）
test: 新增测试
chore: 构建过程或辅助工具的变动
```

### 6. 测试策略

- 单元测试：覆盖率目标 80%+
- 集成测试：关键流程验证
- 端到端测试：模拟真实对话场景
- 性能测试：并发和响应时间验证

---

## 使用方式

### 调用方式
```bash
# 在对话中提及使用此开发规范智能体
"使用 ChatAgentCore 开发规范智能体来实现 [功能描述]"
```

### 工作示例
```
用户: "使用 ChatAgentCore 开发规范智能体来实现 LLM 适配器模块"

智能体响应:
1. 进入研究阶段 - 分析 LLM 适配需求
2. 进入构思阶段 - 设计适配器接口
3. 进入计划阶段 - 制定实施步骤
4. 创建任务文件 tasks/2026-02-04-llm-adapter.md
5. 执行开发并在 docs/architecture/ 下创建设计文档
```

---

## 注意事项

- 每个重要里程碑应及时记录为经验
- 复杂问题需创建独立的任务跟踪文档
- 文档更新与代码提交同步
- 保持 tasks/ 和 docs/ 的一致性和可追溯性

---

## 参考资源

- [Anthropic Skills GitHub](https://github.com/anthropics/skills)
- [What are Skills?](https://support.claude.com/en/articles/12512176-what-are-skills)
- [Creating Custom Skills](https://support.claude.com/en/articles/12512198-creating-custom-skills)
- [Conventional Commits](https://www.conventionalcommits.org/)

---

**版本:** 1.0.0
**最后更新:** 2026-02-04
