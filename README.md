# Trade Document Extractor

Structured extraction + RAG pipeline for financial/trade documents.

## Quick Start

```bash
docker-compose build
docker-compose up
```

## Architecture

PDF → Extraction → Validation → Postgres + Retrieval

## Results

| Metric | Baseline | Final |
|--------|----------|-------|
| Accuracy | 71% | 94% |
| Cost/doc | $0.12 | $0.07 |

## Features

- [ ] Document ingestion & PDF parsing
- [ ] LLM-powered structured extraction
- [ ] Validation & repair loop
- [ ] Postgres + pgvector persistence
- [ ] Retrieval with source citations
- [ ] Eval harness with golden-set scoring

## Next Steps

See ROADMAP.md
