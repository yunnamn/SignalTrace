# SignalTrace: Multilingual Financial Risk Intelligence Platform

**SignalTrace** is a multilingual AI-assisted platform for detecting, monitoring, and investigating potentially suspicious financial content across online platforms.

It combines natural language processing, speech transcription, visual analysis, automated monitoring, and cross-account signal extraction to identify content associated with financial-risk categories such as online gambling, pyramid schemes, guaranteed-income scams, referral schemes, and investment fraud.

## Overview

Online financial scams increasingly appear across videos, social media posts, messaging platforms, and multilingual communities. SignalTrace explores how AI-assisted moderation can help analysts identify suspicious patterns across this content while keeping moderation decisions transparent and configurable.

The system supports content in:

- English
- Russian
- Kazakh

SignalTrace is currently a **working prototype and experimental risk-intelligence system**, not a production fraud-detection service.

## Core Features

### Multimodal Content Analysis

SignalTrace can process several forms of content:

- text
- public URLs
- audio
- video
- images

Audio content can be transcribed before classification, while visual content can be analyzed alongside textual signals.

### Financial Risk Classification

The current detection pipeline evaluates content across five categories:

- **Online Casino / Gambling**
- **Pyramid Schemes**
- **Guaranteed-Income Scams**
- **Referral Schemes**
- **Investment Scams**

Classification signals are combined with configurable moderation policies to produce an overall risk assessment.

### Moderation Decisions

Results are presented as:

- **ALLOW**
- **FLAG**
- **BLOCK**

Each result includes category-level scores and explanatory information to make moderation decisions easier to inspect.

### Moderation Profiles

SignalTrace includes three configurable moderation profiles:

- **Strict** — higher sensitivity
- **Standard** — balanced moderation
- **Soft** — more permissive thresholds

Thresholds can be adjusted through the interface.

The same content can be evaluated under different moderation profiles.

### Automatic Monitoring

SignalTrace includes an automated monitoring system for supported online sources.

Current monitoring integrations focus on:

- YouTube
- Telegram
- VK

Users can configure monitored sources through the Watchlist interface.

### Duplicate Detection

Content is assigned a canonical source identifier, such as:

```text
youtube:VIDEO_ID
```

Automatic monitoring uses both the source identifier and moderation profile to prevent unnecessary duplicate processing while still allowing the same content to be evaluated under different policies.

### Cross-Account Signal Analysis

SignalTrace extracts identifiers that may connect accounts or pieces of content, including:

- URLs
- usernames
- promotional codes
- cryptocurrency wallets
- phone numbers

Shared identifiers can be visualized as a relationship graph to assist investigation of potentially connected accounts.

### Moderation History

Previous analyses are stored and can be reviewed through the dashboard, including:

- platform
- content source
- category scores
- risk score
- moderation decision
- explanation
- transcription when available

### Multilingual Interface

The application interface supports:

- English
- Russian
- Kazakh

## Technology Stack

### Frontend

- React
- Vite
- Recharts
- Nginx

### Backend

- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- Alembic

### Machine Learning

- Hugging Face Transformers
- multilingual zero-shot text classification
- CLIP-based visual analysis
- Whisper speech transcription
- yt-dlp for supported media extraction

### Infrastructure

- Docker
- Docker Compose

## Architecture

```text
User / Monitoring Source
          │
          ▼
 Content Collection
          │
          ├── Text
          ├── Audio
          ├── Image
          └── Video
          │
          ▼
 Content Extraction
          │
          ├── Speech Transcription
          ├── Text Processing
          └── Visual Analysis
          │
          ▼
 ML Classification
          │
          ▼
 Category Risk Scores
          │
          ▼
 Moderation Profile
          │
          ▼
 ALLOW / FLAG / BLOCK
          │
          ├── Moderation History
          ├── Identifier Extraction
          └── Relationship Graph
```

## Project Structure

```text
SignalTrace/
├── backend/
│   ├── app/
│   │   ├── connectors/
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── scoring.py
│   │   ├── auto_crawler.py
│   │   ├── url_queue.py
│   │   └── ...
│   └── alembic/
│
├── frontend/
│   ├── src/
│   ├── Dockerfile
│   └── nginx.conf
│
├── ml_pipeline/
│   ├── classifier.py
│   └── evaluation/
│
├── tests/
├── docker-compose.yml
└── README.md
```

## Running SignalTrace

### Docker

Docker Desktop and Docker Compose are recommended.

From the project root:

```bash
docker compose up --build
```

The Docker configuration starts:

- PostgreSQL
- FastAPI backend
- SignalTrace frontend

## Local Backend Development

Install Python dependencies:

```bash
pip install -r backend/requirements.txt
```

Apply database migrations:

```bash
alembic -c backend/alembic.ini upgrade head
```

Start the API:

```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

FastAPI documentation is then available at:

```text
http://localhost:8000/docs
```

## Local Frontend Development

```bash
cd frontend
npm install
npm run dev
```

The backend URL can be configured using:

```text
VITE_API_URL
```

## Configuration

Important configuration options include:

```text
DATABASE_URL
CORS_ORIGINS
MAX_AUDIO_BYTES
MAX_IMAGE_BYTES
MAX_VIDEO_BYTES
MAX_VIDEO_DURATION_SECONDS
```

Secrets and credentials should be provided through environment variables and should not be committed to the repository.

## Testing

The repository contains automated tests covering core application behavior including:

- moderation scoring
- URL canonicalization
- YouTube source identifiers
- moderation threshold validation
- invalid profile handling
- API behavior
- queue processing
- crawler duplicate prevention
- profile-aware deduplication
- identifier extraction

Tests can be run with:

```bash
pytest tests -v
```

Frontend production builds can be checked with:

```bash
cd frontend
npm run build
```

A multilingual evaluation dataset is also included for further evaluation of the ML pipeline.

## Security Measures

The prototype includes several defensive controls:

- URL scheme validation
- blocking of localhost/private-network destinations
- configurable CORS
- media upload size limits
- video size limits
- video duration limits

Additional authentication, infrastructure hardening, monitoring, and scaling would be required before public production deployment.

## Current Status

**Working prototype / portfolio implementation**

The core application architecture, user interface, API, database migrations, moderation profiles, monitoring queue, watchlist, URL canonicalization, duplicate handling, multilingual interface, and automated tests are implemented.

The machine-learning layer remains experimental. Its predictions are probabilistic and require broader evaluation on a larger labeled real-world dataset before use in high-stakes or production moderation.

SignalTrace is intended to assist investigation and content moderation, not to establish that a person, account, or piece of content is definitively fraudulent.

## Future Development

Potential future work includes:

- larger multilingual evaluation datasets
- improved model calibration
- additional platform integrations
- persistent distributed task processing
- user authentication and role management
- expanded investigation tooling
- production observability and monitoring
- further reduction of false positives on legitimate financial content
