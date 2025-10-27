# UMC Project Analyzer (Local Agentic Stack)

Цель: локальный AI-анализатор криптопроектов (Coherence Score / Stimulation Index) на 24GB GPU. Архитектура использует LLM-агентов, RAG и рубрики оценивания.

## Архитектура агентов
- DataIngestionAgent: собирает тексты событий (анонсы, твиты, посты, релизы), метаданные (GitHub, TVL, ончейн), нормализует.
- ClaimExtractionAgent (LLM): извлекает атомарные «claims» из текстов проекта.
- EvidenceRetrievalAgent (RAG): находит подтверждения/опровержения (репозитории, релизы, ончейн‑метрики, новости) через эмбеддинги в Qdrant.
- VerificationAgent (LLM): для каждого claim вычисляет степень подтверждения (entail / neutral / contradict + score 0–1) на основе извлечённых источников.
- ScoringAgent (LLM+правила): агрегирует компоненты в Coherence Score (CS) и Stimulation Index (SI) по рубрике.
- CriticAgent (LLM): второй проход — проверка когерентности выводов, флаг неуверенности, запрос доп.данных.
- TemporalMonitorAgent: обновляет оценки по окнам времени (7/14/30 дней), делает «ожидание vs факт».

## Локальные модели
- LLM (инструкция): Qwen2.5‑7B‑Instruct (vLLM, FP16) или Qwen2.5‑14B‑Instruct (GGUF Q4_K_M, llama.cpp/CUDA).
- Embeddings: bge‑m3 (мультиязычные) или e5‑multilingual‑small.
- Vector DB: Qdrant (локально) или PGVector.

## Метрики
- Coherence Score (0–100): согласованность заявлений с фактами, стабильность разработки, безопасность, соответствие трендам.
- Stimulation Index (0–100): охваты/вовлечённость, рыночная реакция, новизна нарратива, скорость медиа‑диффузии.

## Быстрый старт
1) Установить зависимости и модели (см. команды ниже).
2) Заполнить `agents/config.yaml` (пути моделей, Qdrant).
3) Запустить скелет пайплайна:
   ```bash
   cd active-agent/agents
   source .venv/bin/activate
   python orchestrator.py --project "Uniswap" --sources ./demo_samples
   ```

## План развития
- Подключить реальные источники (GitHub/X/Telegram/DefiLlama/ончейн).
- Обучить ранжирующую модель для весов CS/SI на исторических лейблах.
- Веб/API публикация и автоматический дайджест.
