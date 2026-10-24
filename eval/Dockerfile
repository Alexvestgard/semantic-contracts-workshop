FROM python:3.12-slim-bookworm@sha256:6a0e06f5ba0b373d051aabd3fffb9b873f27f9a2a3a14bcbe37dee6f0e3bbc70 AS base
WORKDIR /app
COPY eval/requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

FROM base AS runner
COPY sql_eval/__init__.py sql_eval/common.py sql_eval/database.py sql_eval/prompts.py sql_eval/agent.py sql_eval/run.py /app/sql_eval/
COPY scripts/model_client.py /app/scripts/model_client.py
COPY models/gemma.lock.json /app/models/gemma.lock.json
COPY eval/questions.json eval/question-set.json eval/pilots.json /app/eval/
COPY eval/prompts /app/eval/prompts
USER 1000:1000
ENTRYPOINT ["python", "-m", "sql_eval.run"]

FROM base AS scorer
COPY sql_eval/__init__.py sql_eval/common.py sql_eval/database.py sql_eval/score.py /app/sql_eval/
COPY eval/questions.json eval/question-set.json /app/eval/
COPY eval/gold /app/eval/gold
USER 1000:1000
ENTRYPOINT ["python", "-m", "sql_eval.score"]
