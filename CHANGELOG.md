# Changelog

All notable changes to this project. Format: [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added
- Repo skeleton: settings module (`src/settings.py`), `.env.example`, folder structure.
- Free-tier provider setup on Google AI Studio: `gemma-4-31b-it` for generation, `gemini-3.5-flash-lite` as judge (fallback `gemini-3.1-flash-lite`), local open-source embeddings. Azure OpenAI kept as a config option.
- Data selection: `data/drug_list.csv` (28 drugs, 13 classes, max 10 single-ingredient labels each) and the exploration script `notebooks/00_explore_openfda.py` with its output `data/exploration/label_counts.csv`.
