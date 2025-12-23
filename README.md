---
title: Ukrainian LLM Leaderboard
emoji: 👁
colorFrom: red
colorTo: indigo
sdk: gradio
sdk_version: 6.2.0
app_file: leaderboard.py
pinned: false
license: mit
short_description: Measuring LLM capabilities to process Ukrainian texts
---

## About
        
This leaderboard displays performance metrics for language models on Ukrainian language benchmarks. 
The data comes from evaluation results stored in `eval-results/<model_name>/results*.json`.

### Important Notes

- **FLORES benchmarks**: Only English↔Ukrainian (en-uk, uk-en) translation pairs are displayed
- **MMLU**: Only the aggregate score is shown (no subcategories)

### How to Use

- **Main Leaderboard**: View performance on core benchmarks
- **Detailed Benchmarks**: Explore performance on specific benchmark categories
- **Model Comparison**: Compare multiple models with radar charts
- **Visualizations**: Generate bar charts for specific metrics

Sort tables by any metric and adjust display options using the controls.