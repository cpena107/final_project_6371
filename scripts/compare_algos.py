import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import ttest_ind

MILESTONES = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0]

BASELINE_LABEL  = "CPFA"
ALGORITHM_LABEL = "PPSA"

PALETTE = {
    BASELINE_LABEL:  '#4C72B0',
    ALGORITHM_LABEL: '#C0392B',
}


def sig_label(p: float) -> str:
    """Significance star notation."""
    if p < 0.001:
        return '***'
    elif p < 0.01:
        return '**'
    elif p < 0.05:
        return '*'
    return '-'


def draw_bracket(ax, x1, x2, y_top, label, color='black', lw=0.9, fontsize=9):
    """Draw a bracket between x1 and x2 at y_top with a significance label."""
    y_range = ax.get_ylim()[1] - ax.get_ylim()[0]
    tick_h = y_range * 0.012
    ax.plot([x1, x1, x2, x2],
            [y_top, y_top + tick_h, y_top + tick_h, y_top],
            lw=lw, c=color, clip_on=False)
    ax.text((x1 + x2) / 2, y_top + tick_h * 1.15, label,
            ha='center', va='bottom', color=color, fontsize=fontsize,
            clip_on=False)


def _dist_short(distribution: str) -> str:
    """Return the short folder name for a distribution string."""
    return distribution.replace('_distribution', '')


def _results_path(distribution: str, algo_label: str) -> str:
    """Return absolute path to the results file for a given distribution and algo."""
    short = _dist_short(distribution)
    base_dir = os.path.join(os.path.dirname(__file__), "..", "results", short)
    return os.path.join(base_dir, algo_label, f"{short}_results")


def _load_group(distribution: str, algo_label: str) -> pd.DataFrame:
    """Load a single group's results file."""
    path = _results_path(distribution, algo_label)
    df = pd.read_csv(path)
    df['Experiment Type'] = algo_label
    return df


def load_all_data(distribution: str,
                  baseline: str = "CPFA",
                  algorithm: str = "PPSA") -> pd.DataFrame:
    """Load results for both groups and return a combined DataFrame filtered to 10% milestones."""
    frames = []
    for label in [baseline, algorithm]:
        df = _load_group(distribution, label)
        df = df[df['milestone_percent'].round(1).isin([float(m) for m in range(10, 101, 10)])].copy()
        df['milestone_percent'] = df['milestone_percent'].round(0).astype(int)
        frames.append(df[['milestone_percent', 'cumulative_time', 'Experiment Type']])
    return pd.concat(frames, ignore_index=True)


def load_highest_milestone_data(distribution: str,
                                baseline: str = "CPFA",
                                algorithm: str = "PPSA") -> pd.DataFrame:
    """For each seed, find the highest milestone_percent reached and return a combined DataFrame."""
    frames = []
    for label in [baseline, algorithm]:
        df = _load_group(distribution, label)
        highest = (
            df.groupby('random_seed')['milestone_percent']
            .max()
            .reset_index()
            .rename(columns={'milestone_percent': 'highest_milestone'})
        )
        highest['Experiment Type'] = label
        frames.append(highest)
    return pd.concat(frames, ignore_index=True)


def plot_highest_milestone(distribution: str,
                           distribution_label: str,
                           baseline: str = "CPFA",
                           algorithm: str = "PPSA") -> None:
    """Box-plot comparing the highest milestone percent reached per seed for each algorithm."""
    data = load_highest_milestone_data(distribution, baseline, algorithm)

    sns.set_theme(style='whitegrid')
    sns.set_context('paper', font_scale=2.2)
    plt.rcParams.update({
        'font.size': 16,
        'axes.titlesize': 24,
        'axes.labelsize': 18,
        'xtick.labelsize': 16,
        'ytick.labelsize': 16,
        'legend.fontsize': 16,
    })

    hue_order = [baseline, algorithm]
    fig, ax = plt.subplots(figsize=(7, 7))

    sns.boxplot(
        data=data,
        x='Experiment Type',
        y='highest_milestone',
        order=hue_order,
        palette=[PALETTE.get(baseline, '#4C72B0'), PALETTE.get(algorithm, '#C0392B')],
        width=0.45,
        fliersize=4,
        linewidth=1.1,
        showfliers=True,
        ax=ax,
    )

    # significance bracket between the two boxes
    b_vals = data[data['Experiment Type'] == baseline]['highest_milestone'].values
    a_vals = data[data['Experiment Type'] == algorithm]['highest_milestone'].values
    _, p = ttest_ind(b_vals, a_vals, equal_var=False)
    y_top = data['highest_milestone'].max()
    ax.set_ylim(top=y_top * 1.2)
    draw_bracket(ax, 0, 1, y_top * 1.08, sig_label(p), fontsize=11)

    ax.set_ylabel('Highest Milestone Reached (%)', fontsize=18)
    ax.set_xlabel('Algorithm', fontsize=18)
    ax.set_title(f'Highest Milestone — {distribution_label}', fontsize=20)

    plt.tight_layout()
    out_dir = "results"
    out_prefix = os.path.join(out_dir, f"highest_milestone_{distribution}")
    fig.savefig(f"{out_prefix}.png", dpi=300, bbox_inches='tight')
    fig.savefig(f"{out_prefix}.pdf", bbox_inches='tight')
    fig.savefig(f"{out_prefix}.svg", bbox_inches='tight')
    plt.close(fig)
    print(f"Saved {out_prefix}.{{png,pdf,svg}}")


def plot_highest_milestone_combined(
        distributions: list[tuple[str, str]],
        baseline: str = "CPFA",
        algorithm: str = "PPSA",
) -> None:
    """Box-plot comparing highest milestone reached across all distributions in one figure.

    Parameters
    ----------
    distributions:
        List of ``(distribution_key, display_label)`` tuples, e.g.
        ``[("cluster_distribution", "Cluster"), ...]``.
    baseline / algorithm:
        Algorithm labels used to load data and style the boxes.
    """
    frames = []
    for dist_key, dist_label in distributions:
        data = load_highest_milestone_data(dist_key, baseline, algorithm)
        data['Distribution'] = dist_label
        frames.append(data)
    combined = pd.concat(frames, ignore_index=True)

    sns.set_theme(style='whitegrid')
    sns.set_context('paper', font_scale=2.2)
    plt.rcParams.update({
        'font.size': 16,
        'axes.titlesize': 24,
        'axes.labelsize': 18,
        'xtick.labelsize': 16,
        'ytick.labelsize': 16,
        'legend.fontsize': 16,
    })

    dist_labels = [d[1] for d in distributions]
    hue_order = [baseline, algorithm]
    palette = [PALETTE.get(baseline, '#4C72B0'), PALETTE.get(algorithm, '#C0392B')]

    fig, ax = plt.subplots(figsize=(10, 7))

    sns.boxplot(
        data=combined,
        x='Distribution',
        y='highest_milestone',
        hue='Experiment Type',
        order=dist_labels,
        hue_order=hue_order,
        palette=palette,
        width=0.45,
        fliersize=4,
        linewidth=1.1,
        dodge=True,
        showfliers=True,
        ax=ax,
    )

    # significance brackets for each distribution
    box_width = 0.45 / 2
    offsets = np.array([-box_width / 2, box_width / 2])
    y_max_global = combined['highest_milestone'].max()
    ax.set_ylim(top=y_max_global * 1.25)

    for tick_idx, (dist_key, dist_label) in enumerate(distributions):
        sub = combined[combined['Distribution'] == dist_label]
        b_vals = sub[sub['Experiment Type'] == baseline]['highest_milestone'].values
        a_vals = sub[sub['Experiment Type'] == algorithm]['highest_milestone'].values
        if len(b_vals) == 0 or len(a_vals) == 0:
            continue
        _, p = ttest_ind(b_vals, a_vals, equal_var=False)
        y_top = sub['highest_milestone'].max()
        gap = (ax.get_ylim()[1] - ax.get_ylim()[0]) * 0.06
        draw_bracket(
            ax,
            tick_idx + offsets[0],
            tick_idx + offsets[1],
            y_top + gap,
            sig_label(p),
            fontsize=10,
        )

    ax.set_ylabel('Highest Milestone Reached (%)', fontsize=18)
    ax.set_xlabel('Distribution', fontsize=18)
    ax.set_title('Highest Milestone Reached by Distribution', fontsize=20)
    ax.legend(title='', loc='upper left', borderaxespad=0.5)

    plt.tight_layout()
    out_dir = "results"
    out_prefix = os.path.join(out_dir, "highest_milestone_combined")
    fig.savefig(f"{out_prefix}.png", dpi=300, bbox_inches='tight')
    fig.savefig(f"{out_prefix}.pdf", bbox_inches='tight')
    fig.savefig(f"{out_prefix}.svg", bbox_inches='tight')
    plt.close(fig)
    print(f"Saved {out_prefix}.{{png,pdf,svg}}")


def plot_distribution(distribution: str,
                      distribution_label: str,
                      baseline: str = "CPFA",
                      algorithm: str = "PPSA") -> None:
    """Create a box-plot with significance brackets for a single distribution."""
    data = load_all_data(distribution, baseline, algorithm)

    sns.set_theme(style='whitegrid')
    sns.set_context('paper', font_scale=2.2)
    plt.rcParams.update({
        'font.size': 16,
        'axes.titlesize': 24,
        'axes.labelsize': 18,
        'xtick.labelsize': 16,
        'ytick.labelsize': 16,
        'legend.fontsize': 16,
    })

    fig, ax = plt.subplots(figsize=(14, 7))

    hue_order = [baseline, algorithm]
    sns.boxplot(
        data=data,
        x='milestone_percent',
        y='cumulative_time',
        hue='Experiment Type',
        palette=PALETTE,
        hue_order=hue_order,
        width=0.45,
        fliersize=3,
        linewidth=1.1,
        dodge=True,
        showfliers=True,
        ax=ax,
    )

    ax.set_ylabel('Time (seconds)', fontsize=18)
    ax.set_xlabel('Percent of Resources Collected', fontsize=18)

    for artist in ax.artists:
        artist.set_edgecolor('black')
        artist.set_linewidth(0.8)

    # ---- significance brackets ----
    milestones = sorted(data['milestone_percent'].unique())
    box_width = 0.45 / 3          # matches width/n_groups
    offsets = np.array([-box_width, 0.0, box_width])

    y_max_global = data['cumulative_time'].max()
    ax.set_ylim(top=y_max_global * 1.28)

    for tick_idx, ms in enumerate(milestones):
        sub = data[data['milestone_percent'] == ms]
        cpfa_vals  = sub[sub['Experiment Type'] == baseline]['cumulative_time'].values
        ppsa_vals  = sub[sub['Experiment Type'] == algorithm]['cumulative_time'].values

        _, p_cpfa  = ttest_ind(cpfa_vals,  ppsa_vals, equal_var=False)

        y_base = sub['cumulative_time'].max()
        gap    = (ax.get_ylim()[1] - ax.get_ylim()[0]) * 0.055

        x_cpfa  = tick_idx + offsets[0]
        x_ppsa  = tick_idx + offsets[1]

        # Lower bracket: ppsa vs ppsa
        draw_bracket(ax, x_cpfa, x_ppsa, y_base + gap * 0.6,
                     sig_label(p_cpfa), fontsize=8)

    # ---- two-legend layout ----
    ax.legend(loc='upper left', borderaxespad=0.5, title='')

    plt.tight_layout()

    out_dir = "results"
    out_prefix = os.path.join(out_dir, f"ttest_boxplot_milestones_{distribution}")
    fig.savefig(f"{out_prefix}.png", dpi=300, bbox_inches='tight')
    fig.savefig(f"{out_prefix}.pdf", bbox_inches='tight')
    fig.savefig(f"{out_prefix}.svg", bbox_inches='tight')
    plt.close(fig)
    print(f"Saved {out_prefix}.{{png,pdf,svg}}")


def load_milestone_times(group: str, milestone: float, distribution: str, fill_value: float = 720.0) -> pd.Series:
    """Return cumulative_time at a given milestone percent for each seed in a group.
    Seeds that never reached the milestone are filled with fill_value."""
    df = _load_group(distribution, group)
    all_seeds = df['random_seed'].unique()
    at_milestone = (
        df[df["milestone_percent"].round(1) == milestone]
        .set_index('random_seed')['cumulative_time']
    )
    filled = at_milestone.reindex(all_seeds, fill_value=fill_value)
    return filled.reset_index(drop=True)

def main(baseline: str = "CPFA", algorithm: str = "PPSA", distribution: str = "cluster_distribution"):
    results_baseline_new = []

    for milestone in MILESTONES:
        try:
            baseline_data = load_milestone_times(baseline, milestone, distribution)
            algorithm_data = load_milestone_times(algorithm, milestone, distribution)
        except FileNotFoundError as e:
            print(f"File not found: {e.filename}")
            continue
            
        if len(baseline_data) == 0 or len(algorithm_data) == 0:
            print(f"Not enough data for milestone {milestone}%")
            continue

        results_baseline_new.append(
            {
                "milestone_percent": f"{int(milestone)}\\%",
                "baseline_mean": round(baseline_data.mean(), 2),
                "algorithm_mean": round(algorithm_data.mean(), 2),
            }
        )
        
    if not results_baseline_new:
        print("No results to display.")
        return

    # Add average highest milestone row
    hm_data = load_highest_milestone_data(distribution, baseline, algorithm)
    b_highest = hm_data[hm_data['Experiment Type'] == baseline]['highest_milestone'].values
    a_highest = hm_data[hm_data['Experiment Type'] == algorithm]['highest_milestone'].values
    results_baseline_new.append({
        "milestone_percent": "Avg. Highest",
        "baseline_mean": round(float(b_highest.mean()), 2),
        "algorithm_mean": round(float(a_highest.mean()), 2),
    })

    df_results_baseline_new = pd.DataFrame(results_baseline_new)
    pd.set_option("display.float_format", "{:.4f}".format)
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 140)
    #print(df_results_baseline_new.to_string(index=False))

    out_path = os.path.join("results", "ttest_milestones_results.csv")
    df_results_baseline_new.to_csv(out_path, index=False)
    #print(f"\nResults saved to {out_path}")


    algorithm_label = "PPSA"
    baseline_label = "CPFA"
    if distribution == "random_distribution":
        distribution_label = "Random"
    elif distribution == "cluster_distribution":
        distribution_label = "Cluster"
    elif distribution == "powerlaw_distribution":
        distribution_label = "Powerlaw"
    else:
        distribution_label = distribution

    # Generate plots first (independent of LaTeX)
    plot_distribution(distribution, distribution_label, baseline, algorithm)
    plot_highest_milestone(distribution, distribution_label, baseline, algorithm)

    # LaTeX output
    try:
        latex_df = df_results_baseline_new.copy()
        latex_df["baseline_mean"] = latex_df["baseline_mean"].apply(lambda x: f"{x:.2f}")
        latex_df["algorithm_mean"] = latex_df["algorithm_mean"].apply(lambda x: f"{x:.2f}")
        latex_df.columns = [
            "Milestone",
            f"\\begin{{tabular}}[c]{{@{{}}c@{{}}}}{baseline_label} \\\\ Means \\end{{tabular}}",
            f"\\begin{{tabular}}[c]{{@{{}}c@{{}}}}{algorithm_label} \\\\ Means \\end{{tabular}}",
        ]
        latex_str = latex_df.to_latex(
            index=False,
            column_format="|l|c|c|",
            escape=False,
            caption=f"Experiment: {baseline_label} and {algorithm_label}  Algorithm by ({distribution_label})",
            label=f"tab:ttest_milestones_results_{baseline}_{algorithm}_{distribution}",
        )
        print(latex_str)
    except Exception as e:
        print(f"LaTeX generation skipped: {e}")


def latex_highest_milestone_combined(
        distributions: list[tuple[str, str]],
        baseline: str = "CPFA",
        algorithm: str = "PPSA",
) -> None:
    """Print a LaTeX table with the average highest milestone for each distribution."""
    rows = []
    for dist_key, dist_label in distributions:
        data = load_highest_milestone_data(dist_key, baseline, algorithm)
        b_vals = data[data['Experiment Type'] == baseline]['highest_milestone'].values
        a_vals = data[data['Experiment Type'] == algorithm]['highest_milestone'].values
        rows.append({
            "Distribution": dist_label,
            f"{baseline} Mean (\\%)": f"{b_vals.mean():.2f}",
            f"{algorithm} Mean (\\%)": f"{a_vals.mean():.2f}",
        })

    df = pd.DataFrame(rows)
    latex_str = df.to_latex(
        index=False,
        column_format="|l|c|c|",
        escape=False,
        caption=(
            f"Average highest milestone reached per distribution "
            f"({baseline} vs {algorithm})"
        ),
        label="tab:highest_milestone_combined",
    )
    print(latex_str)


if __name__ == "__main__":
    main(baseline="CPFA", algorithm="PPSA", distribution="cluster_distribution")
    main(baseline="CPFA", algorithm="PPSA", distribution="powerlaw_distribution")
    main(baseline="CPFA", algorithm="PPSA", distribution="random_distribution")

    plot_highest_milestone_combined(
        distributions=[
            ("cluster_distribution",  "Cluster"),
            ("powerlaw_distribution", "Powerlaw"),
            ("random_distribution",   "Random"),
        ],
        baseline="CPFA",
        algorithm="PPSA",
    )

    latex_highest_milestone_combined(
        distributions=[
            ("cluster_distribution",  "Cluster"),
            ("powerlaw_distribution", "Powerlaw"),
            ("random_distribution",   "Random"),
        ],
        baseline="CPFA",
        algorithm="PPSA",
    )

