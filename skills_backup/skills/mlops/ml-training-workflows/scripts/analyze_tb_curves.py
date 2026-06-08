"""
Analyze TensorBoard training curves: plot + diagnostics report.

Usage:
    python analyze_tb_curves.py <tb_logdir> [--output-dir .]

Reads all scalar events, generates:
  1. training_curves.png  (3x3 grid, train vs val, smoothed)
  2. Prints diagnostic report to stdout
"""
import argparse, sys, os
import numpy as np

def analyze(tb_logdir, output_dir='.'):
    try:
        from tbparse import SummaryReader
    except ImportError:
        print("Install: pip install tbparse", file=sys.stderr)
        sys.exit(1)

    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        HAS_MPL = True
    except ImportError:
        HAS_MPL = False

    reader = SummaryReader(tb_logdir)
    df = reader.scalars
    tags = sorted(df['tag'].unique())
    train_tags = [t for t in tags if 'train' in t.lower() or '训练' in t]
    val_tags   = [t for t in tags if 'val' in t.lower() or '验证' in t]

    if not train_tags:
        print("No training tags found. Available:", tags)
        return

    # --- PLOT ---
    if HAS_MPL:
        n = len(train_tags)
        cols = min(3, n)
        rows = (n + cols - 1) // cols
        fig, axes = plt.subplots(rows, cols, figsize=(7*cols, 5*rows))
        if n == 1:
            axes = [axes]
        else:
            axes = axes.flatten()

        for idx, ttag in enumerate(train_tags):
            ax = axes[idx]
            tdf = df[df['tag'] == ttag].sort_values('step')
            vals = tdf['value'].values.astype(float)
            steps = tdf['step'].values

            ax.plot(steps, vals, alpha=0.25, color='blue', linewidth=0.5)
            if len(vals) > 20:
                smoothed = np.convolve(vals, np.ones(20)/20, mode='valid')
                ax.plot(steps[19:], smoothed, color='blue', linewidth=2, label='Train')

            # Find matching val tag
            vtag = None
            short = ttag.split('/')[-1] if '/' in ttag else ttag
            for vt in val_tags:
                if short in vt:
                    vtag = vt; break
            if vtag:
                vdf = df[df['tag'] == vtag].sort_values('step')
                if len(vdf) > 0:
                    ax.plot(vdf['step'].values, vdf['value'].values.astype(float),
                            'ro-', markersize=5, linewidth=2, label='Val')

            title = ttag.split('/')[-1] if '/' in ttag else ttag
            ax.set_title(title, fontsize=10)
            ax.legend(fontsize=8)
            ax.grid(True, alpha=0.3)

        for idx in range(n, len(axes)):
            axes[idx].set_visible(False)

        plt.tight_layout()
        out_path = os.path.join(output_dir, 'training_curves.png')
        plt.savefig(out_path, dpi=150, bbox_inches='tight')
        print(f"Plot saved: {out_path}")

    # --- DIAGNOSTICS ---
    print("\n" + "=" * 70)
    print("TRAINING CURVE DIAGNOSTICS")
    print("=" * 70)

    warnings = []
    for ttag in train_tags:
        tdf = df[df['tag'] == ttag].sort_values('step')
        vals = tdf['value'].values.astype(float)
        short = ttag.split('/')[-1] if '/' in ttag else ttag

        print(f"\n--- {short} ---")
        print(f"  Train: start={vals[0]:.6f}, end={vals[-1]:.6f}, min={vals.min():.6f}")

        # Find val
        vtag = None
        for vt in val_tags:
            if short in vt:
                vtag = vt; break

        if vtag:
            vdf = df[df['tag'] == vtag].sort_values('step')
            vvals = vdf['value'].values.astype(float)
            print(f"  Val:   start={vvals[0]:.6f}, end={vvals[-1]:.6f}, min={vvals.min():.6f}")

            if len(vvals) >= 2 and vvals[-1] > vvals[-2]:
                msg = f"  WARNING: Val increasing: {vvals[-2]:.6f} -> {vvals[-1]:.6f}"
                print(msg)
                warnings.append((short, msg))

        # Spike detection
        if len(vals) > 10:
            diffs = np.diff(vals)
            std = np.std(diffs)
            if std > 0:
                max_idx = np.argmax(np.abs(diffs))
                if np.abs(diffs[max_idx]) > 3 * std:
                    step = tdf['step'].values[max_idx]
                    print(f"  ANOMALY: Spike at step ~{step}")

        # NaN/Inf
        if np.any(~np.isfinite(vals)):
            print("  CRITICAL: NaN/Inf detected!")
            warnings.append((short, "NaN/Inf detected"))

    # --- PER-EPOCH OSCILLATION ANALYSIS ---
    print(f"\n{'='*70}")
    print("PER-EPOCH OSCILLATION ANALYSIS (CV = std/mean)")
    print("=" * 70)

    # Try to detect epoch boundaries from val tag steps
    epoch_ends = []
    if val_tags:
        first_val = val_tags[0]
        vdf = df[df['tag'] == first_val].sort_values('step')
        epoch_ends = vdf['step'].tolist()

    for ttag in train_tags:
        tdf = df[df['tag'] == ttag].sort_values('step')
        steps = tdf['step'].values
        vals = tdf['value'].values.astype(float)
        short = ttag.split('/')[-1] if '/' in ttag else ttag

        if len(epoch_ends) < 2:
            continue

        print(f"\n--- {short} ---")
        prev_end = 0
        for i, ep_end in enumerate(epoch_ends):
            mask = (steps > prev_end) & (steps <= ep_end)
            ep_vals = vals[mask]
            if len(ep_vals) < 3:
                prev_end = ep_end
                continue

            mean = np.mean(ep_vals)
            std = np.std(ep_vals)
            median = np.median(ep_vals)
            cv = std / abs(mean) if abs(mean) > 1e-10 else float('inf')
            spike_frac = np.mean(ep_vals > mean + 3 * std) * 100

            print(f"  Epoch {i+1}: mean={mean:.4f}  std={std:.4f}  "
                  f"median={median:.4f}  CV={cv:.2f}  spikes={spike_frac:.1f}%")
            prev_end = ep_end

    # --- CROSS-METRIC INSTABILITY COMPARISON ---
    if epoch_ends:
        print(f"\n{'='*70}")
        print("CROSS-METRIC INSTABILITY (last epoch, CV = std/mean)")
        print("=" * 70)
        last_epoch_start = epoch_ends[-2] if len(epoch_ends) >= 2 else 0
        rows = []
        for ttag in train_tags:
            tdf = df[df['tag'] == ttag].sort_values('step')
            mask = tdf['step'].values > last_epoch_start
            ep_vals = tdf['value'].values.astype(float)[mask]
            if len(ep_vals) < 5:
                continue
            mean = np.mean(ep_vals)
            std = np.std(ep_vals)
            cv = std / abs(mean) if abs(mean) > 1e-10 else float('inf')
            short = ttag.split('/')[-1] if '/' in ttag else ttag
            rows.append((short, mean, std, cv))

        rows.sort(key=lambda x: -x[3])  # sort by CV descending
        for name, mean, std, cv in rows:
            flag = "  <-- UNSTABLE" if cv > 1.0 else ""
            print(f"  {name:30s}  mean={mean:.6f}  std={std:.6f}  CV={cv:.2f}{flag}")

    if warnings:
        print(f"\n{'='*70}")
        print(f"ISSUES FOUND ({len(warnings)}):")
        for name, msg in warnings:
            print(f"  [{name}] {msg.strip()}")
    else:
        print(f"\n{'='*70}")
        print("All metrics look healthy.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('tb_logdir', help='Path to TensorBoard log directory')
    parser.add_argument('--output-dir', default='.')
    args = parser.parse_args()
    analyze(args.tb_logdir, args.output_dir)
