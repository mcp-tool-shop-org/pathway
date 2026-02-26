<p align="center">
  <a href="README.ja.md">日本語</a> | <a href="README.zh.md">中文</a> | <a href="README.es.md">Español</a> | <a href="README.fr.md">Français</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.it.md">Italiano</a> | <a href="README.pt-BR.md">Português (BR)</a>
</p>

<p align="center">
  
            <img src="https://raw.githubusercontent.com/mcp-tool-shop-org/brand/main/logos/pathway/readme.png"
           alt="Pathway logo" width="400">
</p>

<p align="center">
    <em>Append-only journey engine where undo never erases learning.</em>
</p>

<p align="center">
    <a href="https://github.com/mcp-tool-shop-org/pathway/actions/workflows/ci.yml">
        <img src="https://github.com/mcp-tool-shop-org/pathway/actions/workflows/ci.yml/badge.svg" alt="CI">
    </a>
    <a href="https://pypi.org/project/mcpt-pathway/">
        <img src="https://img.shields.io/pypi/v/mcpt-pathway" alt="PyPI version">
    </a>
    <a href="https://opensource.org/licenses/MIT">
        <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT">
    </a>
    <a href="https://mcp-tool-shop-org.github.io/pathway/">
        <img src="https://img.shields.io/badge/Landing_Page-live-blue" alt="Landing Page">
    </a>
</p>

Pathway Core 是一种只追加数据的学习引擎，它保证学习成果不会因为撤销操作而消失。

撤销操作是导航。学习成果会持续存在。

## 设计理念

传统的撤销操作会重写历史。Pathway 不会。

当你在 Pathway 中回溯时，会创建一个新的事件，指向之前的状态，原始路径仍然保留。当你在一个失败的路径上学到知识时，这些知识会持续存在。你的错误会帮助你学习，它们不会消失。

这使得 Pathway 对发生了什么情况保持完全的透明。

## 特性

- **只追加数据的事件日志**: 事件永远不会被编辑或删除。
- **撤销 = 指针移动**: 回溯会创建一个新的事件，并移动指针。
- **学习成果持续存在**: 知识会在回溯和分支中持续存在。
- **分支是首等公民**: 类似于 Git 的隐式分叉，在回溯后开始新的工作。

## 快速开始

```bash
# Install
pip install -e ".[dev]"

# Initialize database
python -m pathway.cli init

# Import sample session
python -m pathway.cli import sample_session.jsonl

# View derived state
python -m pathway.cli state sess_001

# Start API server
python -m pathway.cli serve
```

## API 接口

- `POST /events` - 追加一个事件
- `GET /session/{id}/state` - 获取派生状态 (JourneyView, LearnedView, ArtifactView)
- `GET /session/{id}/events` - 获取原始事件
- `GET /sessions` - 列出所有会话
- `GET /event/{id}` - 获取单个事件

## 事件类型

涵盖完整学习生命周期的 14 种事件类型：

| Type | 目的 |
| ------ | --------- |
| IntentCreated | 用户的目标和上下文 |
| TrailVersionCreated | 学习路径/地图 |
| WaypointEntered | 在路径中导航 |
| ChoiceMade | 用户做出分支选择 |
| StepCompleted | 用户完成一个步骤 |
| Blocked | 用户遇到障碍 |
| Backtracked | 用户回退 (撤销) |
| Replanned | 路径被修改 |
| Merged | 分支合并 |
| ArtifactCreated | 生成输出 |
| ArtifactSuperseded | 旧输出被替换 |
| PreferenceLearned | 用户喜欢的学习方式 |
| ConceptLearned | 用户理解的内容 |
| ConstraintLearned | 用户的环境信息 |

## 派生视图

系统从事件中计算出三个视图：

1. **JourneyView**: 当前位置、分支、已访问的步骤。
2. **LearnedView**: 偏好、概念、约束以及置信度分数。
3. **ArtifactView**: 所有输出以及版本跟踪信息。

## 安全性

- **API 密钥**: 设置 `PATHWAY_API_KEY` 环境变量以保护写入接口。
- **有效载荷限制**: 默认 1MB (可通过 `PATHWAY_MAX_PAYLOAD_SIZE` 进行配置)。
- **会话 ID 验证**: 允许使用字母数字、下划线和连字符，最大长度 128 个字符。

## 测试

```bash
pytest  # 73 tests covering invariants, API, reducers, store
```

## 架构

```
pathway/
├── models/         # Pydantic models for events and views
├── store/          # SQLite event store + JSONL import/export
├── reducers/       # Compute derived views from events
├── api/            # FastAPI endpoints
└── cli.py          # Command-line tools
```
