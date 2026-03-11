# PMax Audit Automation Tool

A Python tool that audits Performance Max campaigns across 6 dimensions, scores each campaign by issue severity, and outputs a prioritised Excel recommendations report. Inspired by automation work built at Google gTech Ads Solutions.

---

## The Business Problem

Performance Max campaigns are complex to audit manually. An analyst reviewing 30 accounts would spend hours checking the same recurring issues — ad strength, budget pacing, URL expansion, ROAS delivery, audience signals, asset completeness — across every campaign. This tool does it in seconds.

---

## How It Works

1. Loads campaign data (mock by default — replace with your own CSV)
2. Runs 6 automated audit checks, each producing a flag and a specific recommendation
3. Scores each campaign by weighted issue severity (higher = needs attention first)
4. Outputs a prioritised Excel report and 3 diagnostic charts

---

## The 6 Audit Dimensions

| Dimension | Flag Condition | Weight |
|---|---|---|
| Ad Strength | Poor or Fair rating | 3 |
| ROAS vs Target | Actual < 80% of target | 3 |
| Budget Utilization | Spending < 70% of daily budget | 2 |
| URL Expansion | Final URL Expansion disabled | 2 |
| Audience Signals | No signals applied | 2 |
| Asset Completeness | < 8 headlines or < 5 images | 2 |

Maximum priority score = 14. Campaigns scoring 8+ need urgent attention across multiple dimensions.

---

## Charts

### 1. Audit Issue Heatmap
Visual grid showing which campaigns have which issues. Red = flagged, green = healthy. Sorted by priority score — worst campaigns at the top.

![Audit heatmap](images/audit_heatmap.png)

---

### 2. Priority Score Distribution & Issues by Category
Left: how many campaigns fall into each severity band. Right: which product categories have the most issues on average.

![Priority scores](images/priority_scores.png)

---

### 3. Actual vs Target ROAS
Scatter plot of every campaign. Points below the diagonal line are underperforming. Red shaded zone = more than 20% below target.

![ROAS analysis](images/roas_analysis.png)

---

## Sample Excel Output

The tool exports `pmax_audit_report.xlsx` with one row per campaign, sorted by priority score:

| Campaign | Priority Score | Issues | Recommendations |
|---|---|---|---|
| PMax_Electronics_1 | 10 | 4 | Ad Strength is 'Poor' — add more headlines \| Budget utilization only 45% ... |
| PMax_Apparel_3 | 8 | 3 | Actual ROAS 180% vs target 400% \| No audience signals applied ... |
| PMax_Beauty_7 | 2 | 1 | Final URL Expansion is disabled ... |

---

## How to Run

```bash
pip install pandas numpy matplotlib seaborn openpyxl
python pmax_audit.py
```

**To use your own data:** replace `generate_mock_data()` in the main block with:
```python
df_raw = pd.read_csv('your_campaign_data.csv')
```

Your CSV needs these columns: `campaign_name`, `daily_budget`, `spend`, `impressions`, `clicks`, `conversions`, `conversion_value`, `target_roas`, `actual_roas`, `ad_strength`, `url_expansion`, `headlines_count`, `images_count`, `audience_signals`

---

## Tools Used
Python · pandas · NumPy · Matplotlib · Seaborn · openpyxl