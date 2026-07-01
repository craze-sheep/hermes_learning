---
name: llm-inference
description: "Run LLM inference: llama.cpp (local GGUF, CPU/edge) or vLLM (production serving, high throughput). Choose the right tool for your use case."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [LLM, Inference, llama.cpp, vLLM, GGUF, Quantization, Serving, Production, Local]
---

# LLM Inference

Two approaches for running LLM inference: **llama.cpp** for local/edge use and **vLLM** for production serving.

## Choosing the Right Tool

| Need | Tool | Why |
|------|------|-----|
| Run on CPU / Apple Silicon | llama.cpp | Optimized for CPU, Metal support |
| Edge deployment / single user | llama.cpp | Lightweight, GGUF quantization |
| Production API (100+ req/sec) | vLLM | PagedAttention, continuous batching |
| OpenAI-compatible endpoint | vLLM | Built-in OpenAI API server |
| Limited VRAM, need large model | Both | llama.cpp: GGUF offload; vLLM: AWQ/GPTQ |
| Multi-user chatbot | vLLM | Concurrent request handling |
| Offline / no internet | llama.cpp | Fully local, no cloud dependency |

---

## 1. llama.cpp — Local GGUF Inference

Run quantized models locally on CPU, Apple Silicon, CUDA, ROCm, or Intel GPUs.

### Install
```bash
brew install llama.cpp                    # macOS/Linux
winget install llama.cpp                  # Windows
# Or build from source:
git clone https://github.com/ggml-org/llama.cpp && cd llama.cpp
cmake -B build && cmake --build build --config Release
```

### Run from Hugging Face Hub
```bash
llama-cli -hf bartowski/Llama-3.2-3B-Instruct-GGUF:Q8_0
llama-server -hf bartowski/Llama-3.2-3B-Instruct-GGUF:Q8_0
```

### Python Bindings
```bash
pip install llama-cpp-python
# CUDA: CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python --force-reinstall --no-cache-dir
```

```python
from llama_cpp import Llama
llm = Llama(model_path="./model-q4_k_m.gguf", n_ctx=4096, n_gpu_layers=35)
out = llm("What is machine learning?", max_tokens=256)
print(out["choices"][0]["text"])
```

### Choosing a Quant
- **Q4_K_M** — general chat (default recommendation)
- **Q5_K_M / Q6_K** — code/technical work (higher quality)
- **Q3_K_M** — tight RAM budgets
- **Q8_0** — near-lossless, larger files
- Prefer the exact quant HF marks as compatible for your hardware

### Model Discovery
```bash
# Search HF Hub for llama.cpp compatible models
# https://huggingface.co/models?apps=llama.cpp&sort=trending

# View available GGUFs for a repo
# https://huggingface.co/api/models/<repo>/tree/main?recursive=true
# Filter for .gguf files
```

### OpenAI-Compatible Server
```bash
llama-server -hf repo:QUANT -c 4096
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Hello!"}]}'
```

**Detailed references:** See `references/llama-cpp-advanced.md`, `references/llama-cpp-server.md`, `references/llama-cpp-quantization.md`, `references/llama-cpp-optimization.md`, `references/llama-cpp-troubleshooting.md`, `references/llama-cpp-hub-discovery.md`.

---

## 2. vLLM — Production LLM Serving

High-throughput serving with PagedAttention (24x throughput vs standard transformers) and continuous batching.

### Install
```bash
pip install vllm
```

### Offline Inference
```python
from vllm import LLM, SamplingParams
llm = LLM(model="meta-llama/Llama-3-8B-Instruct")
sampling = SamplingParams(temperature=0.7, max_tokens=256)
outputs = llm.generate(["Explain quantum computing"], sampling)
print(outputs[0].outputs[0].text)
```

### OpenAI-Compatible Server
```bash
vllm serve meta-llama/Llama-3-8B-Instruct \
  --gpu-memory-utilization 0.9 \
  --enable-prefix-caching \
  --port 8000

# Query with OpenAI SDK
from openai import OpenAI
client = OpenAI(base_url='http://localhost:8000/v1', api_key='EMPTY')
response = client.chat.completions.create(
    model='meta-llama/Llama-3-8B-Instruct',
    messages=[{'role': 'user', 'content': 'Hello!'}]
)
```

### Quantized Serving
```bash
# AWQ (best for 70B models)
vllm serve TheBloke/Llama-2-70B-AWQ --quantization awq --tensor-parallel-size 2

# FP8 (fastest on H100)
vllm serve meta-llama/Llama-3-70B-Instruct --quantization fp8
```

### Production Deployment
```bash
# Docker
docker run --gpus all -p 8000:8000 vllm/vllm-openai:latest \
  --model meta-llama/Llama-3-8B-Instruct \
  --gpu-memory-utilization 0.9 \
  --enable-prefix-caching

# Multi-GPU with tensor parallelism
vllm serve meta-llama/Llama-2-70b-hf \
  --tensor-parallel-size 4 \
  --gpu-memory-utilization 0.9
```

### Key Parameters
| Parameter | Default | Description |
|-----------|---------|-------------|
| `--gpu-memory-utilization` | 0.9 | GPU memory fraction |
| `--max-model-len` | auto | Max sequence length |
| `--tensor-parallel-size` | 1 | Number of GPUs |
| `--enable-prefix-caching` | off | Cache repeated prompt prefixes |
| `--enable-metrics` | off | Prometheus metrics endpoint |
| `--quantization` | none | AWQ, GPTQ, FP8 |

### Monitoring
```bash
curl http://localhost:9090/metrics | grep vllm
# Key metrics: vllm:time_to_first_token_seconds, vllm:num_requests_running, vllm:gpu_cache_usage_perc
```

### Common Issues
- **OOM:** Reduce `--gpu-memory-utilization 0.7` or `--max-model-len 4096`
- **Slow TTFT:** Enable `--enable-prefix-caching`
- **Low throughput:** Increase `--max-num-seqs 512`
- **Model not found:** Add `--trust-remote-code`

**Detailed references:** See `references/vllm-server-deployment.md`, `references/vllm-optimization.md`, `references/vllm-quantization.md`, `references/vllm-troubleshooting.md`.

---

## Hardware Requirements

### llama.cpp
| Model | RAM/VRAM | Quant |
|-------|----------|-------|
| 7B | 4-6 GB | Q4_K_M |
| 13B | 8-10 GB | Q4_K_M |
| 70B | 36-48 GB | Q4_K_M |

### vLLM
| Model | VRAM | Config |
|-------|------|--------|
| 7B-13B | 24 GB (1x A10) | Single GPU |
| 30B-40B | 80 GB (2x A100) | Tensor parallel |
| 70B+ | 160 GB (4x A100) | AWQ/GPTQ quantization |
