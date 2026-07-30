FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY documents/ ./documents/
COPY eval/ ./eval/

ENV PYTHONPATH=/app/src

# Extract the sample doc. Pass your key at run time:
#   docker build -t trade-doc-extractor .
#   docker run --rm -e ANTHROPIC_API_KEY=sk-ant-... trade-doc-extractor
ENTRYPOINT ["python", "-m", "cli"]
CMD ["documents/trade_confirmation_001.pdf"]
