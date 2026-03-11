"""
PMax Audit Automation Tool
===========================
Business Problem:
    Performance Max campaigns are complex and time-consuming to audit
    manually. Analysts waste hours identifying the same recurring issues
    across dozens of accounts.

Approach:
    Reads campaign data from a CSV, runs automated audit logic to flag
    issues across 6 key dimensions, scores each campaign, and outputs
    a prioritised recommendations report. This is a simplified public
    version of the automation built at Google gTech Ads.

Requirements:
    pip install pandas numpy matplotlib seaborn openpyxl

Usage:
    python pmax_audit.py
    (Uses mock data by default — replace with your own CSV)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import warnings
warnings.filterwarnings('ignore')

sns.set_theme(style="whitegrid")
plt.rcParams.update({'figure.dpi': 130})
OUTPUT = "outputs"
os.makedirs(OUTPUT, exist_ok=True)


# ── Generate Mock Campaign Data ──────────────────────────────────────────────
def generate_mock_data(n=30):
    """
    Generates realistic mock PMax campaign data.
    Replace this with pd.read_csv('your_data.csv') for real data.
    """
    np.random.seed(42)
    categories = ["Electronics", "Apparel", "Home & Garden", "Beauty",
                  "Sports", "Toys", "Automotive", "Food & Grocery"]
    ad_strength_options = ["Excellent", "Good", "Fair", "Poor"]
    url_expansion = ["Enabled", "Disabled"]

    data = {
        "campaign_name": [f"PMax_{categories[i % len(categories)]}_{i+1}" for i in range(n)],
        "category": [categories[i % len(categories)] for i in range(n)],
        "daily_budget": np.random.choice([100, 200, 500, 1000, 2000], n),
        "spend": np.random.uniform(20, 2100, n).round(2),
        "impressions": np.random.randint(500, 50000, n),
        "clicks": np.random.randint(10, 2000, n),
        "conversions": np.random.uniform(0.5, 150, n).round(1),
        "conversion_value": np.random.uniform(100, 50000, n).round(2),
        "target_roas": np.random.choice([200, 300, 400, 500, 600, 800], n),
        "actual_roas": np.random.uniform(80, 900, n).round(1),
        "ad_strength": np.random.choice(ad_strength_options, n,
                                         p=[0.15, 0.30, 0.35, 0.20]),
        "url_expansion": np.random.choice(url_expansion, n, p=[0.45, 0.55]),
        "asset_groups": np.random.randint(1, 8, n),
        "headlines_count": np.random.randint(1, 15, n),
        "descriptions_count": np.random.randint(1, 5, n),
        "images_count": np.random.randint(0, 20, n),
        "videos_count": np.random.randint(0, 3, n),
        "audience_signals": np.random.choice([True, False], n, p=[0.6, 0.4]),
    }

    df = pd.DataFrame(data)
    df["budget_utilization"] = (df["spend"] / df["daily_budget"] * 100).round(1)
    df["ctr"] = (df["clicks"] / df["impressions"] * 100).round(2)
    df["cvr"] = (df["conversions"] / df["clicks"] * 100).round(2)
    df["cpa"] = (df["spend"] / df["conversions"].replace(0, np.nan)).round(2)
    return df


# ── Audit Logic ──────────────────────────────────────────────────────────────
def run_audit(df):
    """
    Flags issues across 6 audit dimensions.
    Each flag adds to a priority score — higher score = needs attention first.
    """
    issues = pd.DataFrame(index=df.index)
    scores = pd.Series(0, index=df.index)

    # 1. Ad Strength
    issues["ad_strength_issue"] = df["ad_strength"].isin(["Fair", "Poor"])
    issues["ad_strength_detail"] = df["ad_strength"].apply(
        lambda x: f"Ad Strength is '{x}' — add more headlines, descriptions, and images" 
        if x in ["Fair", "Poor"] else "")
    scores += issues["ad_strength_issue"].astype(int) * 3

    # 2. Budget Utilization
    issues["budget_issue"] = df["budget_utilization"] < 70
    issues["budget_detail"] = df.apply(
        lambda r: f"Budget utilization only {r['budget_utilization']:.0f}% — consider lowering tROAS target" 
        if r["budget_utilization"] < 70 else "", axis=1)
    scores += issues["budget_issue"].astype(int) * 2

    # 3. URL Expansion
    issues["url_expansion_issue"] = df["url_expansion"] == "Disabled"
    issues["url_expansion_detail"] = df["url_expansion"].apply(
        lambda x: "Final URL Expansion is disabled — enabling could increase reach by ~9%" 
        if x == "Disabled" else "")
    scores += issues["url_expansion_issue"].astype(int) * 2

    # 4. ROAS vs Target
    issues["roas_issue"] = df["actual_roas"] < (df["target_roas"] * 0.8)
    issues["roas_detail"] = df.apply(
        lambda r: f"Actual ROAS {r['actual_roas']:.0f}% vs target {r['target_roas']}% — underperforming by {r['target_roas'] - r['actual_roas']:.0f}pts" 
        if r["actual_roas"] < r["target_roas"] * 0.8 else "", axis=1)
    scores += issues["roas_issue"].astype(int) * 3

    # 5. Audience Signals
    issues["audience_issue"] = ~df["audience_signals"]
    issues["audience_detail"] = df["audience_signals"].apply(
        lambda x: "No audience signals applied — add customer lists or custom intent audiences" 
        if not x else "")
    scores += issues["audience_issue"].astype(int) * 2

    # 6. Asset Completeness
    issues["asset_issue"] = (df["headlines_count"] < 8) | (df["images_count"] < 5)
    issues["asset_detail"] = df.apply(
        lambda r: f"Incomplete assets: {r['headlines_count']} headlines, {r['images_count']} images — aim for 8+ headlines, 5+ images" 
        if (r["headlines_count"] < 8 or r["images_count"] < 5) else "", axis=1)
    scores += issues["asset_issue"].astype(int) * 2

    df["priority_score"] = scores
    df["issue_count"] = issues[[c for c in issues.columns if c.endswith("_issue")]].sum(axis=1)

    # Build recommendations
    recs = []
    for _, row in df.iterrows():
        campaign_recs = []
        for dim in ["ad_strength", "budget", "url_expansion", "roas", "audience", "asset"]:
            detail = issues.loc[row.name, f"{dim}_detail"]
            if detail:
                campaign_recs.append(detail)
        recs.append(" | ".join(campaign_recs) if campaign_recs else "No issues found ✓")

    df["recommendations"] = recs
    return df.sort_values("priority_score", ascending=False)


# ── Chart 1: Issue Heatmap ──────────────────────────────────────────────────
def chart_issue_heatmap(df):
    # Recalculate flags directly from raw columns — fully self-contained
    audit_flags = pd.DataFrame(index=df["campaign_name"])
    audit_flags["Ad Strength"]       = df["ad_strength"].isin(["Fair", "Poor"]).values.astype(int)
    audit_flags["Budget Util"]       = (df["budget_utilization"] < 70).values.astype(int)
    audit_flags["URL Expansion"]     = (df["url_expansion"] == "Disabled").values.astype(int)
    audit_flags["ROAS vs Target"]    = (df["actual_roas"] < df["target_roas"] * 0.8).values.astype(int)
    audit_flags["Audience Signals"]  = (~df["audience_signals"]).values.astype(int)
    audit_flags["Asset Completeness"]= ((df["headlines_count"] < 8) | (df["images_count"] < 5)).values.astype(int)

    # Sort by total issues descending, take top 20
    audit_flags["_total"] = audit_flags.sum(axis=1)
    audit_flags = audit_flags.sort_values("_total", ascending=False).drop(columns="_total")
    top20 = audit_flags.head(20)

    # Build annotation array: blank for 0, warning symbol for 1
    annot = top20.copy().astype(object)
    annot[top20 == 0] = ""
    annot[top20 == 1] = "✗"

    fig, ax = plt.subplots(figsize=(12, 10))
    sns.heatmap(
        top20,
        cmap=["#e8f4e8", "#d62728"],
        linewidths=0.5,
        linecolor="white",
        cbar=False,
        ax=ax,
        vmin=0, vmax=1,
        annot=annot.values,
        fmt="",
        annot_kws={"size": 13}
    )
    ax.set_title("PMax Audit — Issue Flags (Top 20 Campaigns by Priority)",
                 fontsize=13, fontweight="bold", pad=15)
    ax.set_xlabel("Audit Dimension", fontsize=11)
    ax.set_ylabel("Campaign", fontsize=11)
    ax.tick_params(axis="y", labelsize=8)
    ax.tick_params(axis="x", labelsize=10)
    plt.tight_layout()
    plt.savefig(f"{OUTPUT}/01_audit_heatmap.png")
    plt.close()
    print("  ✓ Audit heatmap")


# ── Chart 2: Priority Score Distribution ──────────────────────────────────
def chart_priority_scores(df):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # Score distribution
    df["priority_score"].value_counts().sort_index().plot(
        kind='bar', ax=ax1, color='steelblue', alpha=0.8)
    ax1.set_title('Priority Score Distribution', fontsize=12, fontweight='bold')
    ax1.set_xlabel('Priority Score (higher = more issues)')
    ax1.set_ylabel('Number of Campaigns')

    # Issue count by category
    cat_issues = df.groupby("category")["issue_count"].mean().sort_values(ascending=False)
    cat_issues.plot(kind='barh', ax=ax2,
                    color=sns.color_palette("Reds_d", len(cat_issues))[::-1])
    ax2.set_title('Avg Issues per Campaign by Category', fontsize=12, fontweight='bold')
    ax2.set_xlabel('Average Issue Count')

    plt.tight_layout()
    plt.savefig(f"{OUTPUT}/02_priority_scores.png")
    plt.close()
    print("  ✓ Priority scores")


# ── Chart 3: ROAS Analysis ─────────────────────────────────────────────────
def chart_roas_analysis(df):
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = ['#d62728' if actual < target * 0.8 else '#2ca02c'
              for actual, target in zip(df["actual_roas"], df["target_roas"])]
    ax.scatter(df["target_roas"], df["actual_roas"],
               c=colors, alpha=0.7, s=80)
    lims = [min(df["target_roas"].min(), df["actual_roas"].min()) * 0.9,
            max(df["target_roas"].max(), df["actual_roas"].max()) * 1.1]
    ax.plot(lims, lims, 'k--', alpha=0.4, lw=1, label='Target = Actual')
    ax.fill_between(lims, [l * 0.8 for l in lims], lims,
                    alpha=0.05, color='red', label='<80% of target')
    ax.set_xlabel('Target ROAS (%)')
    ax.set_ylabel('Actual ROAS (%)')
    ax.set_title('Actual vs Target ROAS by Campaign\n(Red = underperforming by >20%)',
                 fontsize=12, fontweight='bold')
    ax.legend()
    plt.tight_layout()
    plt.savefig(f"{OUTPUT}/03_roas_analysis.png")
    plt.close()
    print("  ✓ ROAS analysis")


# ── Export Report ────────────────────────────────────────────────────────────
def export_report(df):
    """Exports prioritised recommendations to Excel."""
    report_cols = ["campaign_name", "category", "priority_score", "issue_count",
                   "ad_strength", "budget_utilization", "url_expansion",
                   "actual_roas", "target_roas", "recommendations"]
    report = df[report_cols].copy()
    report.columns = ["Campaign", "Category", "Priority Score", "Issues Found",
                       "Ad Strength", "Budget Util %", "URL Expansion",
                       "Actual ROAS", "Target ROAS", "Recommendations"]

    path = f"{OUTPUT}/pmax_audit_report.xlsx"
    report.to_excel(path, index=False)
    print(f"  ✓ Excel report exported → {path}")


# ── Print Summary ────────────────────────────────────────────────────────────
def print_summary(df):
    total = len(df)
    critical = (df["priority_score"] >= 5).sum()
    needs_attention = (df["priority_score"].between(3, 4)).sum()
    healthy = (df["priority_score"] < 3).sum()

    issue_rates = {
        "Poor/Fair Ad Strength": (df["ad_strength"].isin(["Fair", "Poor"])).mean() * 100,
        "Low Budget Utilization": (df["budget_utilization"] < 70).mean() * 100,
        "URL Expansion Disabled": (df["url_expansion"] == "Disabled").mean() * 100,
        "ROAS Underperforming": (df["actual_roas"] < df["target_roas"] * 0.8).mean() * 100,
        "No Audience Signals": (~df["audience_signals"]).mean() * 100,
    }

    print("\n" + "="*55)
    print("  AUDIT SUMMARY")
    print("="*55)
    print(f"  Campaigns Audited:    {total}")
    print(f"  Critical (5+ issues): {critical} ({critical/total*100:.0f}%)")
    print(f"  Needs Attention:      {needs_attention} ({needs_attention/total*100:.0f}%)")
    print(f"  Healthy:              {healthy} ({healthy/total*100:.0f}%)")
    print("\n  ISSUE RATES:")
    for issue, rate in sorted(issue_rates.items(), key=lambda x: -x[1]):
        bar = "█" * int(rate / 5)
        print(f"  {issue:<30} {rate:>5.1f}%  {bar}")
    print("\n  TOP PRIORITY CAMPAIGNS:")
    for _, row in df.head(5).iterrows():
        print(f"  [{row['priority_score']} pts] {row['campaign_name']}")
    print("="*55 + "\n")


# ── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n🚀 PMax Audit Automation Tool\n")
    print("Generating mock campaign data (replace with your own CSV)...")
    df_raw = generate_mock_data(n=30)
    print(f"  {len(df_raw)} campaigns loaded\n")

    print("Running audit logic...")
    df_audited = run_audit(df_raw)

    print("Generating charts...")
    chart_issue_heatmap(df_audited)
    chart_priority_scores(df_audited)
    chart_roas_analysis(df_audited)
    export_report(df_audited)
    print_summary(df_audited)
    print(f"✅ All outputs saved to /{OUTPUT}/\n")
