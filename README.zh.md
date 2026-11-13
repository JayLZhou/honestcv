<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/banner-dark.svg">
  <img alt="honestcv — 一份招聘方能逐条核验的简历" src="assets/banner-light.svg" width="820">
</picture>

## honestcv：把你已经有的证据亮出来

[![CI](https://github.com/JayLZhou/honestcv/actions/workflows/ci.yml/badge.svg)](https://github.com/JayLZhou/honestcv/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.9+-D6E7FC?style=flat)](https://www.python.org/)
[![Dependencies](https://img.shields.io/badge/Dependencies-none-C5EAB4?style=flat)](pyproject.toml)
[![Model](https://img.shields.io/badge/Model-optional-E9DBFC?style=flat)](#optional-polish)
[![License](https://img.shields.io/badge/License-MIT-EDEDED?style=flat)](LICENSE)
[![English](https://img.shields.io/badge/Docs-English-FCE7D6?style=flat)](README.md)

### ✨ 简历上的每一条都挂着对应的 commit —— 而且有一个验证器证明它没编。 ✨

</div>

<a id="why"></a>

## 🎯 为什么要有 honestcv？

你够格，但你证明不了。

培训班出来的、自学的、没有大厂实习的应届生——困境都很具体：GitHub 上是三个和同班同学一模一样的
练手项目，简历上没有一个招聘方认得出的公司名，而现在对面默认新人的项目是 AI 一键生成的。

这不是文笔问题，是**证据**问题。形容词写得再好也没用。

honestcv 做的是把你已经产出的证据变得可读：

- **你到底做了什么** —— 从 commit 里挖，而不是抄 README 上的宣传稿。
- **凭什么说是你做的** —— 每条 bullet 后面挂着招聘方点得开的链接。
- **你还拿不出什么** —— 明确说成缺口，给一个两周能做完的项目去补，绝不用措辞糊弄过去。

**整个工具只守一条规矩**：**只翻译和排序事实，绝不新增一条。**

### 🔌 你只需要带这些来

| 你有的 | honestcv 拿它做什么 |
| :-- | :-- |
| 任意 **git** 仓库 —— GitHub、GitLab，或者纯本地 | 挖事实；公开托管的还会生成可点击的证据链接 |
| 一份贴进文本文件的 **JD** | 逐条要求的覆盖情况、排序，以及缺口清单 |
| **只有你知道的事**（第一版怎么崩的、是不是一个人做的） | 引导式问答，存下来并永远标记为「自述」 |
| *（可选）* 一个 **Anthropic API key** | 措辞更自然——改写后会被重新验证，跑偏就丢掉 |

就这些。不用注册、不用上传、没有必需依赖，整条链路也不需要模型。

<div align="center">
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/pipeline-dark.svg">
  <img alt="工作流：证据 → 事实库 → 对着 JD 匹配 → 简历·计划·面试题 → 验证" src="assets/pipeline-light.svg" width="100%">
</picture>
</div>

<a id="watch"></a>

## 👀 看它当场拒绝一句假话

<div align="center">
  <img alt="终端录像：honestcv 挖掘仓库、匹配 JD、生成已验证的简历，然后拒绝一句编造的 bullet" src="assets/demo.svg" width="880">
</div>

<div align="center"><sub>真实输出，来自 <code>examples/demo.sh</code>。你自己跑一遍只要二十秒。</sub></div>

最后那个退出码就是这个产品。这个仓库里其余所有东西，都是为了走到那一步。

<a id="features"></a>

## ✨ 核心能力

### 🧾 一个事实库，而不是一个"上传简历"的表单

- 🔍 **挖出来的，不是填出来的** —— 功能、修复、重构、测试、**你自己**加的依赖、**你自己**配的基础设施、你关掉的 issue。
- 🔢 **数出来的，不是估的** —— bullet 里出现的每个数字，背后都有东西真的数过。
- 🔗 **带链接** —— 每条事实挂着对应的 commit，审阅者离原始改动只有一次点击。
- 🏷 **对来源诚实** —— 你亲口说的内容，每一次都标成「自述」。

<table>
  <tr>
    <td width="33.33%" align="center">
      <picture><source media="(prefers-color-scheme: dark)" srcset="assets/card-mine-dark.svg"><img src="assets/card-mine-light.svg" width="100%" alt="commit 变成事实"></picture>
    </td>
    <td width="33.33%" align="center">
      <picture><source media="(prefers-color-scheme: dark)" srcset="assets/card-links-dark.svg"><img src="assets/card-links-light.svg" width="100%" alt="简历上的一行能点开背后的 commit"></picture>
    </td>
    <td width="33.33%" align="center">
      <picture><source media="(prefers-color-scheme: dark)" srcset="assets/card-self-report-dark.svg"><img src="assets/card-self-report-light.svg" width="100%" alt="可核验的证据与自述内容分开"></picture>
    </td>
  </tr>
  <tr>
    <td width="33.33%" valign="top">
      <p align="center"><strong>🔍 你的 commit 变成事实</strong></p>
      <p>按模块和意图分组，保留写得最清楚的那条 commit 原文——不会替你"合理推测"你大概想说什么。</p>
    </td>
    <td width="33.33%" valign="top">
      <p align="center"><strong>🔗 一次点击到原始改动</strong></p>
      <p>每条 bullet 后面挂着对应 commit。怀疑你的人可以直接打开 diff，而不是凭感觉打分。</p>
    </td>
    <td width="33.33%" valign="top">
      <p align="center"><strong>🏷 自述的归自述</strong></p>
      <p>只有你能回答的内容照样会用、会写进去——但放在自己的区块里，永远不会被包装成可核验的。</p>
    </td>
  </tr>
</table>

### 🔒 拿证明说话，不是拿保证说话

- ✅ **每份文档都带一份 trace** —— 每一行出自哪条事实、哪些证据，全部记录在案。
- 🚫 **六道检查** 挡在你和一句撑不住的话之间。
- 🧪 **有退出码** —— `honestcv verify` 会明确失败，所以它在 CI 里和在终端里一样好用。
- 🛠 **缺口给项目，不给 bullet** —— 两周的晚上，一天一天排好，而不是在技能栏多加一行。

<table>
  <tr>
    <td width="33.33%" align="center">
      <picture><source media="(prefers-color-scheme: dark)" srcset="assets/card-verify-dark.svg"><img src="assets/card-verify-light.svg" width="100%" alt="文档、trace、事实库三方对账"></picture>
    </td>
    <td width="33.33%" align="center">
      <picture><source media="(prefers-color-scheme: dark)" srcset="assets/card-plan-dark.svg"><img src="assets/card-plan-light.svg" width="100%" alt="两周的晚上，提交分散在各天"></picture>
    </td>
    <td width="33.33%" align="center">
      <picture><source media="(prefers-color-scheme: dark)" srcset="assets/card-practice-dark.svg"><img src="assets/card-practice-light.svg" width="100%" alt="从你自己的 commit 出的面试题"></picture>
    </td>
  </tr>
  <tr>
    <td width="33.33%" valign="top">
      <p align="center"><strong>✅ 三方对账</strong></p>
      <p>文档 × trace × 事实库。手改过的一行、没有出处的数字、证据撑不起的技能——每一种都会被点名拦下。</p>
    </td>
    <td width="33.33%" valign="top">
      <p align="center"><strong>🛠 缺口变成两周</strong></p>
      <p>它只排计划，拒绝替你写代码。那两周里分散开的 commit 历史，本身就是你真做了的证据。</p>
    </td>
    <td width="33.33%" valign="top">
      <p align="center"><strong>❓ 拿自己的活练</strong></p>
      <p>题目从你的 commit 里出，包括现在每个新人都会被问的那句："我凭什么信这不是生成的？"</p>
    </td>
  </tr>
</table>

<a id="toc"></a>

## 📋 目录

- [🎯 为什么要有 honestcv？](#why)
- [👀 看它当场拒绝一句假话](#watch)
- [✨ 核心能力](#features)
- [🚀 快速上手](#quick-start)
- [🧩 它怎么做到的](#how-it-works)
  - [难题一：审阅者默认你的项目是生成的](#challenge-1)
  - [难题二：简历工具会把不知道的事编出来](#challenge-2)
  - [难题三：缺口没法靠措辞糊弄](#challenge-3)
- [📊 实际跑出来是什么样](#in-action)
- [🧭 命令](#commands)
- [📖 代码结构](#code-structure)
- [⚠️ 它解决不了什么](#limits)
- [🛠 开发](#development)
- [🔗 相关项目](#related)

<a id="quick-start"></a>

## 🚀 快速上手

### ① 安装

```bash
git clone https://github.com/JayLZhou/honestcv && cd honestcv
pip install -e .
```

### ② 把仓库变成事实

```bash
honestcv init --name "你的名字" --email you@example.com
honestcv mine ~/code/your-project
honestcv audit ~/code/your-project     # 这段历史在审阅者眼里有多可读？
```

### ③ 对准一个岗位

```bash
honestcv match  --jd jd.txt            # 逐条要求：已覆盖 / 缺口 / 工具读不懂
honestcv resume --jd jd.txt -o resume.md
honestcv plan   --jd jd.txt -o plan.md # 缺的东西给一个两周项目
```

### ④ 证明它

```bash
honestcv verify resume.md              # 有任何一行没有出处就以非零退出
```

<details>
<summary><b>手头没有自己的仓库？</b></summary>

<br>

```bash
bash examples/demo.sh
```

它会造一个"像是三周晚上做出来的"示例仓库——有功能、有后来才发现并修掉的 bug、有边做边写的测试、
有一次引入依赖——跑完整条链路，最后往生成好的简历里加一句编造的话，让验证器把它抓出来。
不需要联网，不需要 API key。

</details>

<a id="how-it-works"></a>

## 🧩 它怎么做到的

<a id="challenge-1"></a>

### 🧩 难题一：审阅者默认你的项目是生成的

**问题。** 现在初级岗位的作品集是带着怀疑被打开的。审阅者分不出你三周的晚上和一个模型一下午的产物，
于是两个一起打折。你说"这真是我写的"没有用——所有人都这么说。

**✅ 解法：把真实的工作变得可读，并且绝不声称无法核验的东西。**

事实从历史里挖出来，所以一条 bullet 指向的是 commit 而不是形容词。在这之上，`honestcv audit` 衡量
一段历史有多**可读**——时间跨度、有提交的天数、最大 commit 占比、有没有回头改自己写的代码、有没有
修过东西——并且会直接点名审阅者反应最强烈的那种模式：

```console
$ honestcv audit ~/code/dumped-project
**得分**: 6/100 (1 次提交)

## 明显问题
- 第一个 commit 里装着项目的大部分内容。在审阅者眼里，这是代码从别处搬进来的样子。
```

它给出的每条建议都是"让你本来就做过的事留下痕迹"。报告自己会写明：它无法证明代码是谁写的，分数低
也不是指控——因为这是实话，而一个在这里吹牛的工具，不过是同一个问题换了身白大褂。

<a id="challenge-2"></a>

### 🧩 难题二：简历工具会把不知道的事编出来

**问题。** 让模型"润色一下这条 bullet"，你会拿到"优化了数据管道，吞吐提升 40%"。没有人量过 40%。
候选人会在面试现场、当着能决定录不录他的人的面，第一次发现这件事。

**✅ 解法：让"编造"在结构上做不到，然后照样再查一遍。**

事实不是一句话，而是**模板 + 来自证据的 payload**：

```json
{
  "template": "bugfix_work",
  "payload": { "repo": "demo/orders", "area": "src/dispatch", "commits": 2,
               "subject": "dispatch dropped orders when the queue was slow" },
  "skills": ["Python"],
  "evidence": [{ "kind": "commit", "ref": "c9f62bf",
                 "url": "https://github.com/demo/orders/commit/c9f62bf…" }]
}
```

渲染器可以挑事实、排顺序、选语言，但**写不出一句话**——句子存在 `data/templates.json` 里，而它能
填进去的值只有 payload 里的。换语言换的是模板，不是 payload；有一条测试盯着这件事：中英文两份简历
里的数字必须完全一致。

然后每份文档都带一份 trace，`honestcv verify` 拿它们对账：

| 检查 | 不通过会怎样 |
| :-- | :-- |
| 这一行在 trace 里吗 | ✗ `untraced_claim` —— 生成之后被人加过或改过 |
| 它指向的事实还在吗 | ✗ `unknown_fact` |
| 行里每个数字都来自证据吗 | ✗ `unbacked_number` —— "提升 40%" 死在这里 |
| 行里提到的技能，这条事实撑得起吗 | ✗ `unbacked_skill` |
| 有没有可点击的链接 | ! `missing_link` |
| 有没有"精通""expert""行业领先" | ! `unverifiable_language` |

`--strict` 会把警告也算失败。这套检查同样作用在可选的模型输出上：改写跑偏就丢掉，换回朴素的原文。

<a id="challenge-3"></a>

### 🧩 难题三：缺口没法靠措辞糊弄

**问题。** JD 要 Kafka，而你的历史里一点没有。所有简历工具的答案都是在技能栏加上"Kafka"。这能过
关键词筛选，然后死在技术面的第一个问题上。

**✅ 解法：两周的晚上，只排计划，不写代码。**

```markdown
## 两周补齐计划：Kafka

项目：可重放的订单事件管道
为什么这能证明你会：跑通教程谁都会。消费者在批处理中途挂掉、重复投递、offset 重放——
                    能讲清楚这三件事，才是『懂 Kafka』而不是『用过 Kafka』。
不要做的事：        不要做界面，不要加第二个服务。一个 topic、一个消费者组、把一种故障处理透。

| 天     | 做什么                                     | 交付物                                 |
| 4-7    | 改成手动提交 offset，故意中途 kill 掉消费者 | FAILURE_NOTES.md，写清楚哪些消息被重投 |
| 8-10   | 用 processed-ids 表让消费者幂等            | 一个把同一条消息重放两次的测试         |
```

八个手写蓝本（Kafka、Kubernetes、Redis、PostgreSQL、gRPC、React、CI/CD、OpenTelemetry）外加一个
通用模板。每个蓝本最后都列着"做完之后你必须答得上来的问题"——而计划里永远没有代码，因为面试官问的
是你写代码时在想什么，那件事没人能替你经历。

<a id="in-action"></a>

## 📊 实际跑出来是什么样

跑在 [`examples/`](examples/) 里的示例仓库上——20 次提交、跨度 22 天，一个真实副业项目的形状。
下面每个数字都能用 `bash examples/demo.sh` 复现：

| 阶段 | 结果 |
| :-- | :-- |
| `mine` | 从 20 次提交里挖出 **13 条事实**，**9 项技能**有证据支撑 |
| `audit` | 可读性 **94/100**，没有问题标记 |
| `match`（后端 JD） | 硬性要求覆盖 **100%**，一个加分项缺口（Kubernetes） |
| `resume` | **21 条声明**全部可追溯 —— `PASS (0 errors, 0 warnings)` |
| `plan` | 为缺口生成一个 14 天、按天排的项目方案 |
| 手工加一句编造的 bullet | `FAIL … ✗ untraced_claim`，**退出码 1** |

再看一个"一次性倒进来"的仓库：

| 信号 | 观察值 | 评分 |
| :-- | :-- | --: |
| 时间跨度 | 0 天 | 0% |
| 有提交的天数 | 1 天 | 8% |
| 提交数量 | 1 次 | 2% |
| 最大提交占比 | 占全部改动行的 100% | 0% |
| 回头改自己写过的文件 | 0% 的提交 | 0% |
| 修复与重构占比 | 0% 的提交 | 0% |
| **总分** | | **6/100** |

> [!NOTE]
> 这个 6 分不是指控，报告自己也会这么写。它只是一份清单：现在审阅者看不见哪些东西——而每一条都能靠
> 真去做、并且边做边提交来补上。

<a id="commands"></a>

## 🧭 命令

| 命令 | 做什么 |
| :-- | :-- |
| `honestcv init` | 建一个空的事实库 |
| `honestcv mine <repo>` | git 历史 → 事实（重挖同一个仓库会覆盖，不会重复累积） |
| `honestcv audit <repo>` | 证据强度体检，`--json` 供脚本使用 |
| `honestcv questions [--jd]` | 代码回答不了的问题；`--template` 写一份空白答卷 |
| `honestcv interview [--answers f]` | 把回答记成「自述」事实；不加参数就在终端里一问一答 |
| `honestcv facts [--skill X]` | 看看事实库里有什么 |
| `honestcv match --jd jd.txt` | 逐条要求：已覆盖 / 缺口 / 工具读不懂 |
| `honestcv resume --jd jd.txt` | 定制简历 |
| `honestcv letter --jd jd.txt` | 求职信——不知道的地方留 `[TODO]`，不编 |
| `honestcv plan --jd jd.txt` | 缺口 → 两周项目方案 |
| `honestcv practice [--jd]` | 基于自己工作的面试题 |
| `honestcv verify <doc>` | 文档、trace、事实库三方对账；`--strict` 把警告也算失败 |

全局参数：`--lang zh|en`（默认中文）、`-f/--file`（事实库路径，默认 `honestcv.json`）。

<a id="optional-polish"></a>

<details>
<summary><b>可选：让 Claude 润色措辞</b></summary>

<br>

```bash
pip install -e ".[llm]"
export ANTHROPIC_API_KEY=...
honestcv resume --jd jd.txt --polish
```

模型只拿到**一句话，以及这句话被允许使用的数字和技术名**，拿不到证据链接（所以它编不出链接）。
它返回的每一句都会再过一遍和渲染器一样的规则：多出一个数字、少了一个数字、多出一项技能、想自己
写链接——这句就被丢掉、换回原文，并在 stderr 里说明原因。

没装 `anthropic`、没有 API key，或者调用失败，你照样拿到简历，只是措辞朴素一点。
**整个工具不依赖任何模型。**

</details>

<a id="code-structure"></a>

## 📖 代码结构

> **图例**：📥 证据进来 | 🧠 核心模型 | 📤 文档出去 | 🔒 不变量 | 🎨 插图

```text
honestcv/
├── src/honestcv/
│   ├── models.py            🧠 Evidence / Fact / FactBase —— 整个工具的地基
│   ├── taxonomy.py          🧠 路径、依赖名、自由文本 → 规范化技能
│   ├── i18n.py              🧠 分语言的模板；换模板永远碰不到 payload
│   ├── grounding.py         🔒 Trace 与 verify：六道检查，每次渲染后都跑
│   ├── mining/
│   │   ├── git_miner.py     📥 commit → 事实，每个数字都是数出来的
│   │   └── authenticity.py  📥 证据强度体检，以及它拒绝声称的东西
│   ├── jd.py                📥 JD → 要求（硬性 / 加分 / 读不懂）
│   ├── matcher.py           🧠 已覆盖 / 缺口 / 读不懂，三者严格分开
│   ├── interview.py         📥 代码看不出来的事，存成「自述」
│   ├── render/
│   │   ├── resume.py        📤 定制简历及其 trace
│   │   ├── cover_letter.py  📤 求职信，不知道的地方留 [TODO]
│   │   └── project_plan.py  📤 缺口 → 两周项目
│   ├── practice.py          📤 从本人事实出的面试题
│   ├── llm.py               📤 可选润色，重新验证，跑偏就丢
│   ├── cli.py               🧭 命令行
│   └── data/                skills.json · templates.json · gap_projects.json
├── tests/                   92 个测试 —— 不需要网络，不需要 API key
├── examples/                示例仓库生成器、两份 JD、端到端 demo
└── assets/make_assets.py    🎨 生成 README 里的每一张图
```

约 3,100 行 Python，零必需依赖。

<a id="limits"></a>

## ⚠️ 它解决不了什么

> [!WARNING]
> 说实话比好用更重要。

- **它解决不了歧视。** 如果某个群体的问题是雇主根本不给面试，再好的简历也白搭。那种情况下的杠杆点
  是撮合愿意招的雇主，不是措辞。
- **它造不出初级岗位。** 如果岗位本身在减少，简历再好也只是在更小的池子里排名靠前。它帮的是
  "够格但说不清楚"的人，帮不了"岗位不存在"的问题。
- **它无法证明代码是谁写的。** `audit` 衡量的是可读性，不是真实性。分数低不是指控。
- **它不会偷偷替你翻译 commit。** 你的 commit message 是什么语言，简历里引用的就是什么语言，
  除非你开 `--polish`。

<a id="development"></a>

## 🛠 开发

```bash
pip install -e ".[dev]"
pytest -q                      # 92 个测试，不需要网络，不需要 API key
bash examples/demo.sh          # 端到端链路，CI 里也会跑
python3 assets/make_assets.py  # 重新生成上面所有插图
```

CI 在 3.11 / 3.12 / 3.13 上跑测试和 demo，另外在容器里跑 3.9——runner 镜像已经不带 3.9 了，而
"写了没人测的声明"正是这个项目最反对的东西。

最值得扩充的两处：

- **[`src/honestcv/data/skills.json`](src/honestcv/data/skills.json)** —— 技能词表：别名、文件
  后缀、依赖名、路径特征。
- **[`src/honestcv/data/gap_projects.json`](src/honestcv/data/gap_projects.json)** —— 两周项目
  蓝本。只有一条规矩：它必须是一个人用两周晚上能真做完、并且能在面试里讲十分钟的东西。

设计细节见 **[docs/design.md](docs/design.md)**：为什么事实是「模板 + payload」，以及 trace 怎么
在"用户自己动手改简历"之后依然成立。

<a id="related"></a>

## 🔗 相关项目

**简历工具** —— 都很好用，但没有一个去证明内容是真的。

- **[Resume-Matcher](https://github.com/srbhr/Resume-Matcher)** —— 把简历和 JD 做匹配并给改进
  建议。honestcv 往前站了一步：内容从你的 commit 里来；也往后站了一步：内容要能被验证。
- **[Reactive Resume](https://github.com/reactive-resume/reactive-resume)** —— 注重隐私、排版
  漂亮的简历编辑器。内容由你提供；honestcv 关心的是内容从哪来。
- **[RenderCV](https://github.com/rendercv/rendercv)** —— 用 YAML 写简历、排版成 PDF。它和事实库
  是天然的下游：honestcv 决定什么是真的，RenderCV 决定它长什么样。
- **[Awesome-CV](https://github.com/posquit0/Awesome-CV)** —— 很多工程师在用的 LaTeX 模板。

**这个区别为什么重要**：帮人生成 GitHub 历史的工具，是在帮人伪造证据。honestcv 押的是相反的一注——
大多数初级候选人说的是实话，只是证明不了。

<br>

<div align="center">
<sub><b>MIT</b> · 为那些够格、却还说不清楚的人而做。</sub>
</div>
