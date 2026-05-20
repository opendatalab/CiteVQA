# CiteVQA：面向可信文档智能的证据归因评测基准

<p align="center">
  <a href="https://arxiv.org/pdf/2605.12882"><img src="https://img.shields.io/badge/arXiv-2605.12882-b31b1b?style=flat-square&logo=arxiv" alt="arXiv" /></a>
  <a href="https://huggingface.co/datasets/opendatalab/CiteVQA"><img src="https://img.shields.io/badge/%F0%9F%A4%97_%E6%95%B0%E6%8D%AE%E9%9B%86-HuggingFace-yellow?style=flat-square" alt="Hugging Face dataset" /></a>
  <a href="https://www.modelscope.cn/datasets/OpenDataLab/CiteVQA"><img src="https://img.shields.io/badge/ModelScope_%E6%95%B0%E6%8D%AE%E9%9B%86-purple?logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjIzIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KCiA8Zz4KICA8dGl0bGU+TGF5ZXIgMTwvdGl0bGU+CiAgPHBhdGggaWQ9InN2Z18xNCIgZmlsbD0iIzYyNGFmZiIgZD0ibTAsODkuODRsMjUuNjUsMGwwLDI1LjY0OTk5bC0yNS42NSwwbDAsLTI1LjY0OTk5eiIvPgogIDxwYXRoIGlkPSJzdmdfMTUiIGZpbGw9IiM2MjRhZmYiIGQ9Im05OS4xNCwxMTUuNDlsMjUuNjUsMGwwLDI1LjY1bC0yNS42NSwwbDAsLTI1LjY1eiIvPgogIDxwYXRoIGlkPSJzdmdfMTYiIGZpbGw9IiM2MjRhZmYiIGQ9Im0xNzYuMDksMTQxLjE0bC0yNS42NDk5OSwwbDAsMjIuMTlsNDcuODQsMGwwLC00Ny44NGwtMjIuMTksMGwwLDI1LjY1eiIvPgogIDxwYXRoIGlkPSJzdmdfMTciIGZpbGw9IiMzNmNmZDEiIGQ9Im0xMjQuNzksODkuODRsMjUuNjUsMGwwLDI1LjY0OTk5bC0yNS42NSwwbDAsLTI1LjY0OTk5eiIvPgogIDxwYXRoIGlkPSJzdmdfMTgiIGZpbGw9IiMzNmNmZDEiIGQ9Im0wLDY0LjE5bDI1LjY1LDBsMCwyNS42NWwtMjUuNjUsMGwwLC0yNS42NXoiLz4KICA8cGF0aCBpZD0ic3ZnXzE5IiBmaWxsPSIjNjI0YWZmIiBkPSJtMTk4LjI4LDg5Ljg0bDI1LjY0OTk5LDBsMCwyNS42NDk5OWwtMjUuNjQ5OTksMGwwLC0yNS42NDk5OXoiLz4KICA8cGF0aCBpZD0ic3ZnXzIwIiBmaWxsPSIjMzZjZmQxIiBkPSJtMTk4LjI4LDY0LjE5bDI1LjY0OTk5LDBsMCwyNS42NWwtMjUuNjQ5OTksMGwwLC0yNS42NXoiLz4KICA8cGF0aCBpZD0ic3ZnXzIxIiBmaWxsPSIjNjI0YWZmIiBkPSJtMTUwLjQ0LDQybDAsMjIuMTlsMjUuNjQ5OTksMGwwLDI1LjY1bDIyLjE5LDBsMCwtNDcuODRsLTQ3Ljg0LDB6Ii8+CiAgPHBhdGggaWQ9InN2Z18yMiIgZmlsbD0iIzM2Y2ZkMSIgZD0ibTczLjQ5LDg5Ljg0bDI1LjY1LDBsMCwyNS42NDk5OWwtMjUuNjUsMGwwLC0yNS42NDk5OXoiLz4KICA8cGF0aCBpZD0ic3ZnXzIzIiBmaWxsPSIjNjI0YWZmIiBkPSJtNDcuODQsNjQuMTlsMjUuNjUsMGwwLC0yMi4xOWwtNDcuODQsMGwwLDQ3Ljg0bDIyLjE5LDBsMCwtMjUuNjV6Ii8+CiAgPHBhdGggaWQ9InN2Z18yNCIgZmlsbD0iIzYyNGFmZiIgZD0ibTQ3Ljg0LDExNS40OWwtMjIuMTksMGwwLDQ3Ljg0bDQ3Ljg0LDBsMCwtMjIuMTlsLTI1LjY1LDBsMCwtMjUuNjV6Ii8+CiA8L2c+Cjwvc3ZnPg==&labelColor=white&style=flat-square" alt="ModelScope dataset" /></a>
  <a href="./LICENSE.txt"><img src="https://img.shields.io/badge/License-MIT-green?style=flat-square" alt="License MIT" /></a>
</p>

<div align="center">
  <a href="https://huggingface.co/papers/2605.12882">
    <img src="img/huggingface_paper_gold_day.svg"/>
  </a>
</div>

<p align="center">
  📖 <a href="./README.md"><b>English</b></a> &nbsp;|&nbsp; <a href="./README_zh.md"><b>简体中文</b></a>
</p>

<p align="center">
  <b>如果你喜欢我们的项目，欢迎在 GitHub 上给我们一个 star ⭐，以便及时获取最新更新。</b>
</p>

---
## 🔎 概览

**CiteVQA** 是一个面向**忠实证据归因**的文档视觉问答基准。不同于传统只评估最终答案是否正确的 DocVQA 数据集，CiteVQA 要求模型在回答问题时，必须给出与源文档**元素级**对齐的支持证据。这个基准用于评估系统是否不仅能答对问题，还能在长篇、真实世界 PDF 中引用正确的支撑区域。

该数据集包含来自 **711** 份 PDF 的 **1,897** 个问题，覆盖 **7** 个大领域和 **30** 个子领域，文档平均长度为 **40.6** 页。数据同时包含**英文**和**中文**文档，并支持**单文档**与**多文档**两种设置。

评测覆盖以下三种数据设置：

- **Single-Doc**：单文档问答。
- **Multi (1-Gold)**：多文档问答，且恰好只有一个 gold document。
- **Multi (N-Gold)**：多文档问答，且存在多个 gold document。

<p align="center">
  <img src="./img/citevqa_example.png" width="92%" alt="CiteVQA overview">
</p>
<p align="center">
  <em>
    CiteVQA 概览。左侧表示 SAA 的判定逻辑：预测只有在答案正确，且引用证据与标准证据在语义上相关、在空间上充分对齐时，才被记为正确。右上展示数据集统计，说明 CiteVQA 更强调长篇、真实场景 PDF。右下展示模型表现，表明现有 MLLM 在答案正确率与证据归因正确率之间仍存在显著差距。
  </em>
</p>

## ✨ 亮点

- **答案与证据联合评测**：CiteVQA 同时评估答案是否正确，以及引用是否忠实。
- **元素级证据标注**：真值证据以结构化元素形式提供，包含 bounding box、页码和文档编号。
- **长文档场景**：文档均为多页 PDF，具有真实世界长度和版式复杂度。
- **跨领域与双语**：基准覆盖 **7** 个领域、**30** 个子领域，以及 `en`、`zh` 两种语言。
- **多文档推理**：除单文档问答外，数据集还包含需要跨文档聚合证据的问题。
- **三种评测设置**：基准同时覆盖 `Single-Doc`、`Multi (1-Gold)` 和 `Multi (N-Gold)` 三类场景。

## ⚙️ 环境配置

安装依赖：

```bash
pip install -r requirements.txt
```

如需更稳定地渲染中文 PDF，可额外配置 CJK 字体：

<details>
<summary>展开查看中文 PDF 字体配置</summary>

```bash
apt install fonts-noto-cjk poppler-data

cat > /etc/fonts/conf.d/99-pdf-cjk.conf << 'EOF'
<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "fonts.dtd">
<fontconfig>
  <alias><family>STSong-Light</family><prefer><family>Noto Serif CJK SC</family></prefer></alias>
  <alias><family>STSong</family><prefer><family>Noto Serif CJK SC</family></prefer></alias>
  <alias><family>SimSun</family><prefer><family>Noto Serif CJK SC</family></prefer></alias>
  <alias><family>FangSong</family><prefer><family>Noto Serif CJK SC</family></prefer></alias>
  <alias><family>KaiTi</family><prefer><family>Noto Serif CJK SC</family></prefer></alias>
  <alias><family>SimHei</family><prefer><family>Noto Sans CJK SC</family></prefer></alias>
  <alias><family>Microsoft YaHei</family><prefer><family>Noto Sans CJK SC</family></prefer></alias>
</fontconfig>
EOF

fc-cache -f
```

</details>

## 📦 数据

可在仓库根目录执行以下命令，从 Hugging Face 获取 benchmark 数据到 `data/`，再下载源 PDF：

```bash
pip install -U "huggingface_hub[cli]"
hf download opendatalab/CiteVQA --repo-type dataset --local-dir .
python data/download/download_pdfs.py --workers 16 --out data/pdf --csv data/download/pdf_source.csv
```

也可在仓库根目录执行以下命令，从 ModelScope 获取 benchmark 数据到 `data/`，再下载源 PDF：

```bash
pip install -U modelscope
modelscope download --dataset OpenDataLab/CiteVQA --local_dir .
python data/download/download_pdfs.py --workers 16 --out data/pdf --csv data/download/pdf_source.csv
```

PDF 下载脚本会读取 `data/download/pdf_source.csv`，并将所有文件保存到 `data/pdf/`。

如果你在数据集或下载过程中遇到问题，可直接跳转到后面的 [联系](#contact) 部分。

<details>
<summary>下载参数</summary>

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `--csv` | `pdf_source.csv` | 包含 PDF URL 的 CSV 文件 |
| `--out` | `pdf` | 输出目录 |
| `--workers` | `16` | 并发下载线程数 |
| `--timeout` | `120` | 单文件超时时间（秒） |
| `--retries` | `3` | 重试次数 |
| `--no-skip` | - | 对已存在文件重新下载 |

</details>

## 🚀 推理与评测

`bash run.sh` 提供了一个评测 `GPT-5.4` 的 demo。先在 `run.sh` 中编辑 API 配置，然后执行：

```bash
bash run.sh
```

参考流程如下：

```bash
# API config
API_TYPE=openai
API_KEY=YOUR_API_KEY
BASE_URL=YOUR_BASE_URL

# Inference
python infer/run.py \
  --api ${API_TYPE} \
  --model MODEL_NAME \
  --base_url ${BASE_URL} \
  --api_key ${API_KEY} \
  --workers 4 \
  --out outputs/infer/MODEL_NAME.json

# Evaluation
python eval/run.py \
  --judge_api ${API_TYPE} \
  --judge_model JUDGE_MODEL_NAME \
  --judge_api_key ${API_KEY} \
  --base_url ${BASE_URL} \
  --input outputs/infer/MODEL_NAME.json \
  --out outputs/eval/MODEL_NAME.json \
  --workers 24

# Summary
python eval/summarize.py \
  --input outputs/eval/MODEL_NAME.json \
  --out_dir outputs/eval/MODEL_NAME
```

### 🧭 推理参数

<details>
<summary>推理参数</summary>

| 参数 | 必需 | 说明 |
| --- | --- | --- |
| `--api` | 是 | `openai`、`genai` 或 `anthropic` |
| `--model` | 是 | 模型名称 |
| `--api_key` | 是 | API 密钥 |
| `--base_url` | 否 | API Base URL |
| `--workers` | 否 | 并发数，默认 `4` |
| `--out` | 否 | 输出 JSON 路径 |
| `--benchmark` | 否 | Benchmark 路径，默认 `data/data_items.json` |
| `--limit` | 否 | 样本数限制，`0` 表示全部 |
| `--max_pdf_mb` | 否 | 超过该大小时先压缩 PDF，单位 MB |

</details>

### 📏 评测参数

<details>
<summary>评测参数</summary>

| 参数 | 必需 | 说明 |
| --- | --- | --- |
| `--input` | 是 | 推理输出 JSON |
| `--judge_api` | 否 | 评测 API 类型，默认 `openai` |
| `--judge_model` | 否 | 评测模型名称，默认 `gpt-4o` |
| `--judge_api_key` | 是 | 评测 API 密钥 |
| `--base_url` | 否 | API Base URL |
| `--metrics` | 否 | 指标列表，默认 `recall,rel` |
| `--workers` | 否 | 并发数 |
| `--out` | 否 | 输出 JSON 路径 |
| `--limit` | 否 | 样本数限制 |

</details>

## 🗂️ 仓库结构

```text
CiteVQA/
├── data/
│   ├── validation/
│   │   └── CiteVQA.json         # 基准问答对
│   ├── pdf/                     # 下载后的 PDF
│   └── download/
│       ├── pdf_source.csv       # PDF 元数据与链接
│       └── download_pdfs.py     # PDF 下载脚本
├── infer/
│   └── run.py                   # 推理脚本
├── eval/
│   ├── run.py                   # 评测脚本
│   └── summarize.py             # 汇总表生成脚本
├── prompts/                     # 系统与用户提示词
├── outputs/                     # 推理与评测输出
├── requirements.txt
└── run.sh                       # 演示脚本
```

## 📊 评测指标

| 指标 | 含义 |
| --- | --- |
| `Recall` | 预测证据是否与关键真值证据发生重叠 |
| `Relevance (Rel.)` | 引用证据在语义上是否支持答案 |
| `Answer Correctness (Ans.)` | 答案是否正确 |
| `SAA` | Strict Attributed Accuracy，要求答案和证据都正确 |
| `Page Recall` | 是否定位到了正确页面 |
| `Precision / F1` | 预测证据的精度与重叠质量 |

`SAA` 是 CiteVQA 的核心指标。

## 🏆 评测结果

我们使用统一提示模板，在 CiteVQA 上评测了 20 个主流 MLLM。结果表明，相比单纯答对问题，忠实的证据归因仍然显著更难。

- **综合最佳 SAA**：`Gemini-3.1-Pro-Preview` 的 SAA 达到 **76.0**，答案分数为 **86.1**。
- **最佳答案准确率**：`GPT-5.4` 的答案分数达到 **87.1**，但其 SAA 降至 **59.0**。
- **最佳开源模型**：`Qwen3-VL-235B-A22B` 的 SAA 达到 **22.5**，答案分数为 **72.3**。
- **关键发现**：多数模型都存在明显的 `Ans.` 与 `SAA` 差距，反映出基准中的 `Attribution Hallucination` 挑战。

完整总体结果如下：

| 模型 | 类别 | Rec. | Rel. | Ans. | SAA |
| --- | --- | ---: | ---: | ---: | ---: |
| Gemini-3.1-Pro-Preview | 闭源 MLLM | 66.0 | 83.6 | 86.1 | 76.0 |
| Gemini-3-Flash-Preview | 闭源 MLLM | 45.4 | 75.7 | 84.5 | 65.4 |
| GPT-5.4 | 闭源 MLLM | 31.0 | 67.5 | 87.1 | 59.0 |
| Gemini-2.5-Pro | 闭源 MLLM | 27.4 | 59.8 | 82.2 | 47.0 |
| Seed2.0-Pro | 闭源 MLLM | 28.5 | 54.9 | 81.3 | 44.1 |
| GPT-5.2 | 闭源 MLLM | 18.2 | 56.6 | 71.5 | 33.7 |
| Qwen3.6-Plus | 闭源 MLLM | 7.7 | 25.0 | 85.9 | 17.5 |
| GLM-5V-Turbo | 闭源 MLLM | 14.9 | 29.2 | 49.6 | 12.8 |
| Qwen3-VL-235B-A22B | 开源大模型 | 11.3 | 35.3 | 72.3 | 22.5 |
| Gemma-4-31B | 开源大模型 | 11.6 | 35.0 | 69.8 | 20.2 |
| Kimi-K2.5 | 开源大模型 | 6.2 | 26.8 | 74.3 | 19.1 |
| Qwen3.5-397B-A17B | 开源大模型 | 5.4 | 24.6 | 76.5 | 18.3 |
| Qwen3.5-27B | 开源大模型 | 5.3 | 25.3 | 75.6 | 17.3 |
| Qwen3-VL-32B | 开源大模型 | 6.6 | 30.5 | 72.3 | 17.3 |
| Qwen3.5-122B-A10B | 开源大模型 | 3.9 | 19.0 | 73.6 | 14.8 |
| Qwen3.5-9B | 开源小模型 | 1.6 | 14.7 | 65.0 | 11.1 |
| Qwen3.5-35B-A3B | 开源小模型 | 1.7 | 13.7 | 76.4 | 10.7 |
| Qwen3-VL-30B-A3B | 开源小模型 | 3.5 | 14.6 | 62.2 | 8.2 |
| Qwen3-VL-8B | 开源小模型 | 1.0 | 14.7 | 61.2 | 7.5 |
| Gemma-4-26B-A4B | 开源小模型 | 3.0 | 17.9 | 48.4 | 6.2 |

<a id="contact"></a>
## 📬 联系

由于 PDF sources 通过链接下载，在下载过程中可能会遇到数据可访问性或链接失效等问题。如有任何下载相关问题，请发送邮件至 [wzr@stu.pku.edu.cn](mailto:wzr@stu.pku.edu.cn)。

## 📚 引用

```bibtex
@article{ma2026citevqa,
  title={CiteVQA: Benchmarking Evidence Attribution for Trustworthy Document Intelligence},
  author={Ma, Dongsheng and Li, Jiayu and Wang, Zhengren and Wang, Yijie and Kong, Jiahao and Zeng, Weijun and Xiao, Jutao and Yang, Jie and Zhang, Wentao and Wang, Bin and He, Conghui},
  journal={arXiv preprint arXiv:2605.12882},
  year={2026}
}
```

## 🙏 致谢

- 感谢 [MinerU](https://github.com/opendatalab/MinerU) 提供的文档解析能力。
- 感谢 [ViDoRe V3](https://huggingface.co/datasets/vidore/vidore-benchmark-v3) 等开源数据集（SPIQA、MedQA、PubMedQA、MaintNorm、PolicyBench）为本基准的构建提供了启发。

## 📄 License

本项目采用 MIT License。详情请参见 [LICENSE](./LICENSE) 文件。

## ©️ 版权声明

本数据集仅用于学术研究和非商业用途。我们充分尊重原始版权持有者的合法权益。若相关权利人认为本基准中任何内容的收录、索引或使用存在不妥之处，请联系 `OpenDataLab@pjlab.org.cn`。我们将在核实后及时配合删除或更新相关内容。
