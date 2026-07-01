# World Models Batch B Analysis (#6-#10) — Reference

## Papers Analyzed

| # | Paper | Sub-direction | Code Repo | Key Insight |
|---|-------|---------------|-----------|-------------|
| 6 | MuZero (Schrittwieser 2020) | 规划+学习 | google-deepmind/mctx (partial) | Learned latent dynamics + MCTS, no env rules needed |
| 7 | IRIS (Micheli 2023) | Transformer世界模型 | eloalonso/iris ✅ | VQ-VAE tokenizer + GPT-style world model |
| 8 | Genie (Bruce 2024) | 生成式环境 | ❌ Closed (DeepMind) | Unsupervised action discovery from video |
| 9 | UniSim (Yang 2024) | 生成式环境 | ❌ Closed (Google DM) | Video diffusion as world simulator |
| 10 | GAIA-1 (Hu 2023) | 领域专用(驾驶) | ❌ Closed (Wayve) | ViT-VQGAN + 6.5B GPT for driving |

## Architecture Comparison

| Component | MuZero | IRIS | Genie | UniSim | GAIA-1 |
|-----------|--------|------|-------|--------|--------|
| **Encoder** | ResNet→128×8×8 | VQ-VAE (8×8 tokens, 512 codebook) | Causal VQ-ViT (8×8 tokens, 4096 codebook) | Video diffusion (3D U-Net) | ViT-VQGAN (16×16 tokens, 8192 codebook) |
| **Dynamics** | ResNet conv in latent space | GPT autoregressive on tokens | MaskGIT non-autoregressive | Conditional diffusion | GPT autoregressive (6.5B params) |
| **Action** | Discrete MCTS actions | Discrete action token | Learned latent action (8 classes) | Multi-modal (text/robot/human) | 6-DOF driving controls |
| **Planning** | MCTS (50-800 sims) | Actor-Critic in imagination | No explicit planning | No explicit planning | Autoregressive sampling |
| **Resolution** | 96×96→84×84 grayscale | 64×64 RGB | 256×256 RGB | 256×256 RGB | 512×256 RGB |

## Key Code-Level Details (IRIS)

From `code/07_IRIS/src/models/`:

### Tokenizer (VQ-VAE)
- Encoder: ResNet with 4 downsampling stages, GroupNorm, Swish activation
- Codebook: 512 entries, 64-dim embeddings
- Quantization: nearest-neighbor lookup, straight-through gradient
- Loss: commitment_loss (β=1.0) + L1 reconstruction + LPIPS perceptual
- Output: 8×8 = 64 discrete tokens per frame

### World Model (Transformer)
- GPT-style causal transformer
- Block tokenization: K observation tokens + 1 action token per timestep
- Heads: observation prediction (cross-entropy), reward prediction (3-class), end prediction (2-class)
- KV-caching for efficient autoregressive inference
- Context: 20 blocks (~200 tokens)

### Actor-Critic
- Same architecture as Dreamer: MLP actor (tanh_normal) + MLP critic
- Trained on imagined trajectories from the transformer world model

## Closed-Source Paper Analysis Strategy

For papers without code repos (#8 Genie, #9 UniSim, #10 GAIA-1):
- Rely on paper's architecture diagrams and method descriptions
- Compare to similar open-source papers (e.g., IRIS for transformer-based, DreamerV3 for RL-based)
- Note specific claims that cannot be verified without code
- Focus on high-level design patterns rather than implementation details

## Sub-direction Clusters Identified

1. **Dreamer系列** (#1-#5): RSSM-based, latent imagination, actor-critic
2. **规划+学习** (#6 MuZero): MCTS + learned dynamics
3. **Transformer世界模型** (#7 IRIS, #13 TransDreamer): Replace RSSM with Transformer
4. **生成式环境** (#8 Genie, #9 UniSim): Video generation as world model
5. **领域专用** (#10 GAIA-1): Driving-specific world model
6. **Diffusion世界模型** (#16 DIAMOND): Diffusion as dynamics model
7. **游戏生成** (#17 GameGen-X): Game-specific generation

## Remaining Papers for Batch C (#11-#15)

| # | Paper | Status |
|---|-------|--------|
| 11 | TDMPC (Hansen 2022) | Pending |
| 12 | TDMPC2 (Hansen 2024) | Pending |
| 13 | TransDreamer (Chen 2022) | Pending |
| 14 | DayDreamer (Wu 2022) | Pending |
| 15 | SimPLe (Kaiser 2020) | Pending |

## Remaining Papers for Batch D (#16-#20)

| # | Paper | Status |
|---|-------|--------|
| 16 | DIAMOND (Alonso 2024) | Pending |
| 17 | GameGen-X (Che 2024) | Pending |
| 18 | PhysDreamer (Zhang 2024) | Pending |
| 19 | WALT (Gupta 2024) | Pending |
| 20 | DiT (Peebles 2023) | Pending |
