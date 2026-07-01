# World Models — 20 Representative Papers (2018-2024)

Verified on 2026-05-31. All arXiv IDs confirmed.

## Quick Reference Table

| # | Short Name | arXiv ID | Year | Venue | Sub-direction |
|---|-----------|----------|------|-------|---------------|
| 1 | World Models | 1803.10122 | 2018 | NeurIPS Workshop | Foundational |
| 2 | PlaNet | 1811.04551 | 2019 | ICML | Latent Dynamics |
| 3 | Dreamer v1 | 1912.01603 | 2020 | ICLR | Dreamer Series |
| 4 | DreamerV2 | 2010.02193 | 2021 | ICLR | Dreamer Series |
| 5 | DreamerV3 | 2301.04104 | 2023 | JMLR 2024 | Dreamer Series |
| 6 | MuZero | 1911.08265 | 2020 | Nature | Planning + Learning |
| 7 | IRIS | 2209.00588 | 2023 | ICLR | Transformer WM |
| 8 | Genie | 2402.15391 | 2024 | ICML | Generative Env |
| 9 | UniSim | 2310.06114 | 2024 | ICLR | General Simulator |
| 10 | GAIA-1 | 2309.17080 | 2023 | Tech Report | Autonomous Driving |
| 11 | TD-MPC | 2203.04955 | 2022 | ICML | Latent MPC |
| 12 | TD-MPC2 | 2310.16828 | 2024 | ICLR | Latent MPC |
| 13 | TransDreamer | 2202.09481 | 2022 | NeurIPS Workshop | Transformer WM |
| 14 | DayDreamer | 2206.14176 | 2022 | CoRL | Robotics |
| 15 | SimPLe | 1903.00374 | 2020 | ICML | Video Prediction |
| 16 | DIAMOND | 2405.12399 | 2024 | NeurIPS Spotlight | Diffusion WM |
| 17 | GameGen-X | 2411.00769 | 2024 | arXiv | Game Generation |
| 18 | PhysDreamer | 2404.13026 | 2024 | ECCV | Physics WM |
| 19 | W.A.L.T | 2312.06662 | 2024 | CVPR | Video Gen WM |
| 20 | Sora* | N/A | 2024 | OpenAI Blog | Video Gen WM |

## Notes

- Sora is closed-source with no formal paper. Reference: DiT (2212.09748) and W.A.L.T (#19).
- GAIA-1 has no public code (Wayve closed-source).
- Genie and UniSim code repos are community reimplementations, not official.
- DayDreamer appeared twice in original candidate list; W.A.L.T replaced the duplicate.

## Sub-direction Clusters

1. **Dreamer Series** (PlaNet → DreamerV1 → V2 → V3): Core latent imagination line
2. **Transformer World Models** (IRIS, TransDreamer): Replace RNN with Transformer
3. **Generative Environments** (Genie, UniSim, GameGen-X): Learn interactive worlds from video
4. **Diffusion World Models** (DIAMOND): Use diffusion models for environment simulation
5. **Planning + Learning** (MuZero, TD-MPC, TD-MPC2): Tree search / MPC with learned models
6. **Robotics** (DayDreamer): Real-world robot learning with world models
7. **Video Generation as WM** (W.A.L.T, Sora): Video generation models as world simulators
8. **Domain-Specific** (GAIA-1 driving, PhysDreamer physics, SimPLe Atari)
