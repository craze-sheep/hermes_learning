# Dreamer系列5篇论文精读分析 — 知识库

> 完成时间：2026-05-31
> 分析方法：论文公开信息 + 代码仓库（01_WorldModels, 03_Dreamer, 04_DreamerV2, 05_DreamerV3）
> 完整分析文件：`/home/lzy/project/方向研究/analysis/01-WorldModels.md` 至 `05-DreamerV3.md`

---

## 技术演进脉络

```
World Models (2018)          PlaNet (2019)           Dreamer (2020)
  VAE + MDN-RNN               RSSM + CEM              RSSM + Actor-Critic
  32-dim latent               离散分布(32x32)          连续高斯
  CMA-ES控制器                在线规划                 想象中学习
  Car Racing only             DMC 6任务               DMC + Atari
       |                         |                        |
       +-------------------------+------------------------+
                                 |
                    DreamerV2 (2021)         DreamerV3 (2023)
                      离散RSSM                 Symlog + Free Bits
                      KL平衡                   Categorical Value
                      跨域通用(DMC+Atari)      150+任务通用
                      Atari超越人类            Nature发表
```

## 关键架构组件对比

| 组件 | World Models | PlaNet | Dreamer | DreamerV2 | DreamerV3 |
|------|-------------|--------|---------|-----------|-----------|
| 视觉编码 | VAE (CNN) | CNN | CNN | CNN(96ch) | CNN(32-256ch)+LN |
| 时序模型 | MDN-RNN(LSTM) | GRU+离散 | GRU+连续高斯 | GRU+离散categorical | GRU+离散categorical |
| 状态维度 | 32(z)+256(h) | 200(h)+32x32(z) | 200(h)+30(z) | 200(h)+32x32(z) | 200(h)+32x32(z) |
| 决策方式 | CMA-ES | CEM规划 | Actor-Critic | Actor-Critic | Actor-Critic |
| 想象horizon | N/A(整个梦境) | 12步 | 15步 | 15步 | 15步 |
| 动作分布 | 连续 | 连续 | tanh_normal | trunc_normal/onehot | tanh_normal |
| Value预测 | N/A | N/A | 回归 | 回归+slow target | symlog-categorical |
| KL处理 | N/A | free bits=1.0 | free nats=3.0 | KL平衡(0.8/1.0) | 自适应free bits |
| 框架 | PyTorch | TF | TF | TF | JAX |

## 核心技术创新时间线

1. **2018 World Models**: 提出"在梦境中学习"范式，VAE+MDN-RNN+CMA-ES三模块架构
2. **2019 PlaNet**: 引入RSSM（确定性+随机性融合），用CEM在线规划替代进化策略
3. **2020 Dreamer**: 用Actor-Critic在想象轨迹中训练，替代CEM规划，效率提升1000倍
4. **2021 DreamerV2**: 离散categorical分布替代连续高斯，KL平衡训练技巧，Atari超越人类
5. **2023 DreamerV3**: Symlog预测、自适应free bits、categorical value，150+任务通用，Nature发表

## 各论文关键数值

| 论文 | 核心指标 | 数值 | 基线对比 |
|------|---------|------|---------|
| World Models | Car Racing回报 | 906+/-21 | 随机-35 |
| PlaNet | DMC样本效率 | 比D4PG提升50倍 | D4PG |
| Dreamer | 决策速度 | 比PlaNet CEM快1000倍 | PlaNet |
| DreamerV2 | Atari 100K人类归一化 | 1.02(超越人类) | DrQ 0.36 |
| DreamerV3 | Minecraft钻石 | 首次持续获得 | 此前无法 |

## 风险与局限（贯穿系列）

1. **模型误差累积**: 所有版本都面临，horizon=15是经验最优折中
2. **离散vs连续选择**: V2/V3用离散解决了多模态问题，但引入量化误差
3. **计算资源**: V3的Minecraft任务需约500 GPU小时
4. **长程规划不足**: 固定15步horizon对超长程任务（数百步）仍有局限

## 代码仓库位置

- `code/01_WorldModels/` — PyTorch复刻，含VAE/MDN-RNN/Controller
- `code/03_Dreamer/` — TensorFlow，含RSSM/ActorCritic/Dreamer主循环
- `code/04_DreamerV2/` — TensorFlow，含EnsembleRSSM/exploration
- `code/05_DreamerV3/` — JAX，含embodied框架/分布式训练
