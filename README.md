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

## Benchmark

Evaluation used a synthetic dataset of **1,000 error logs** (125 per category). All three runs completed **1,000/1,000 requests** successfully.

| Model / prompt | Accuracy | Mean latency | P95 latency |
|---|---:|---:|---:|
| Qwen2.5-Coder-1.5B / v3 | 72.2% | 5.81 s | 7.68 s |
| Qwen2.5-Coder-3B / v3 | **83.7%** | 11.03 s | 12.66 s |
| Qwen2.5-Coder-3B / v4 (included) | 83.4% | 14.16 s | 17.60 s |

Prompt v4 improved `unknown` classification from **24.0% to 58.4%** compared with 3B/v3, but reduced `configuration_error` accuracy from **78.4% to 53.6%**. The archive includes the v4 `results.csv` and `summary.json`.

**Limitation:** The dataset is synthetic and contains variations of repeated scenarios. Prompts were tuned using this dataset, so these figures are development benchmark results rather than an independent estimate of real-world accuracy.
