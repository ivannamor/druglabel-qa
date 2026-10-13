# Changelog

All notable changes to this project. Format: [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added
- Repo skeleton: settings module (`src/settings.py`), `.env.example`, folder structure.
- Free-tier provider setup on Google AI Studio: `gemma-4-31b-it` for generation, `gemini-3.5-flash-lite` as judge (fallback `gemini-3.1-flash-lite`), local open-source embeddings. Azure OpenAI kept as a config option.
