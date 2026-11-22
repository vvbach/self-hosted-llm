# Self-Hosted LLM Error Classifier

A self-hosted service for classifying software error logs using a local large language model. The application exposes a REST API that accepts an error message and returns its category, severity, a short explanation, and a suggested action.

## Features

- Local inference with **Qwen2.5-Coder-3B-Instruct (GGUF Q4_K_M)** and **llama.cpp**
- REST API implemented with **FastAPI**
- Structured JSON output validated with **Pydantic**
- Eight error categories and four severity levels
- Health/readiness checks and Prometheus metrics
- Docker Compose deployment and automated unit tests

## Architecture

```text
Client
  |
  | POST /api/v1/classify
  v
FastAPI (:8000)
  |  Input validation, concurrency control, output validation
  v
llama.cpp (:8080, internal)
  |
  v
Qwen2.5-Coder-3B-Instruct (local GGUF model)
```

## Project structure

```text
self-hosted-llm/
├── app/
│   ├── classifier.py
│   ├── config.py
│   ├── main.py
│   ├── schema.py
│   └── system_prompt.txt
├── test/
│   ├── test_api.py
│   └── test_classifier.py
├── docker-compose.yaml
├── Dockerfile
├── requirements.txt
├── .env.example
├── results.csv
├── summary.json
└── README.md
```

The GGUF model is not included in the repository archive.

## Requirements

- Docker Engine and Docker Compose v2
- Sufficient memory for the quantized 3B model
- The `qwen2.5-coder-3b-q4_k_m.gguf` model file

## Run the service

1. Place the GGUF model at `models/qwen2.5-coder-3b-q4_k_m.gguf`.
2. From the project directory, run:

```bash
docker compose up -d --build
```

3. Verify the service:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/ready
```

The API is available on port **8000**. Interactive documentation is at `http://localhost:8000/docs`.

## API

### `POST /api/v1/classify`

Request:

```json
{
  "error": "ModuleNotFoundError: No module named 'pandas'"
}
```

Example response (illustrative):

```json
{
  "category": "dependency_error",
  "severity": "medium",
  "summary": "The required pandas module is not available.",
  "suggested_action": "Install pandas in the active Python environment."
}
```

Supported categories: `runtime_error`, `syntax_error`, `type_error`, `dependency_error`, `configuration_error`, `network_error`, `resource_error`, `unknown`.

Supported severity levels: `low`, `medium`, `high`, `critical`.

Additional endpoints:

| Endpoint | Description |
|---|---|
| `GET /health` | API health check |
| `GET /ready` | Model readiness check |
| `GET /metrics` | Prometheus metrics |
| `GET /docs` | Interactive API documentation |

## Configuration

The `api` service is configured in `docker-compose.yaml`:

| Variable | Default in Compose | Description |
|---|---|---|
| `LLM_URL` | `http://llm:8080/v1/chat/completions` | Local model endpoint |
| `LLM_TIMEOUT` | `120` | Request timeout in seconds |
| `MAX_CONCURRENT` | `1` | Maximum concurrent inference requests |
| `MODEL_NAME` | `local` | Model identifier |
| `MAX_TOKENS` | `384` | Maximum generated tokens |

The llama.cpp service uses a 2048-token context, four CPU threads, no GPU offloading, and one parallel slot. These parameters can be changed in `docker-compose.yaml`.

The classification instructions are stored in `app/system_prompt.txt`. After changing this file, rebuild the API container:

```bash
docker compose up -d --build api
```

## Tests

Install dependencies and run unit tests:

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s test -v
```

## Benchmark Results

The system was evaluated using a synthetic dataset of 1,000 error logs across 8 error categories, with 125 samples per category.

Both models were tested using the same dataset and completed all API requests successfully.

| Metric | Qwen2.5-Coder-1.5B | Qwen2.5-Coder-3B |
|---|---:|---:|
| Accuracy | 72.2% | **83.4%** |
| Correct predictions | 722 / 1000 | **834 / 1000** |
| Average latency | **5.81 s** | 14.16 s |
| P95 latency | **7.68 s** | 17.60 s |
| Request success rate | 100% | 100% |

The 3B model achieved an **11.2 percentage-point improvement in classification accuracy** compared to the 1.5B model, at the cost of increased inference latency.

These results demonstrate the trade-off between classification accuracy and inference speed. The benchmark uses synthetic data, so further evaluation on real-world error logs is recommended.
