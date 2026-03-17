# Test Reporting API

A FastAPI application for ingesting, storing, and visualizing test automation results. It stores test data in MongoDB and provides a dashboard for analytics, trends, and export.

## Features

- **Bulk document ingestion** – POST test results with automatic run ID assignment
- **Dashboard** – Overview, run reports, trends, slowest tests, recent failures, module health
- **Export** – CSV and Excel export for runs and filtered test results
- **Pagination** – All list views support 10 records per page

## Requirements

- Python 3.8+
- MongoDB

## Installation

```bash
cd reporting
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the project root:

```env
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=report
MONGO_COLLECTION_NAME=clicker_result
```

## Running

```bash
uvicorn main:app --reload
```

Open [http://localhost:8000](http://localhost:8000) or [http://localhost:8000/dashboard](http://localhost:8000/dashboard) for the dashboard.

## API Endpoints

### Document ingestion

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/documents/bulk` | Bulk insert test results (JSON array) |

### Reports

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/reports/summary` | Overall summary stats |
| GET | `/api/reports/modules` | Pass/fail by module |
| GET | `/api/reports/runs` | List runs (paginated) |
| GET | `/api/reports/runs/{run_id}/report` | Full run report |
| GET | `/api/reports/tests` | List tests with filters (paginated) |
| GET | `/api/reports/trend` | Pass/fail trend by date |
| GET | `/api/reports/slowest-tests` | Slowest tests (paginated) |
| GET | `/api/reports/recent-failures` | Recent failures (paginated) |
| GET | `/api/reports/most-failing-tests` | Most failing tests (paginated) |
| GET | `/api/reports/module-health` | Pass rate % per module |
| GET | `/api/reports/run-duration-trend` | Duration trend by date |
| GET | `/api/reports/filter-options` | Distinct run IDs and modules |
| POST | `/api/reports/test-run-history` | Run history for given tests |

### Export

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/reports/export/run/{run_id}?format=csv\|xlsx` | Export run report |
| GET | `/api/reports/export/tests?format=csv\|xlsx` | Export tests (supports filters) |

## Project Structure

```
reporting/
├── main.py              # FastAPI app entry point
├── requirements.txt
├── .env                 # MongoDB config (create from .env.example)
├── core/                # Config and database
│   ├── config.py        # MongoSettings from env
│   └── database.py      # MongoConnection
├── services/            # Business logic
│   ├── document.py      # DocumentService (bulk insert)
│   └── report.py        # ReportService (aggregations)
├── routes/              # HTTP handlers
│   ├── document.py      # DocumentRoutes
│   └── report.py        # ReportRoutes
├── export/              # CSV/Excel export
│   └── report_exporter.py
└── static/dashboard/    # Single-page dashboard
    └── index.html
```

## Document Schema

Each test result document should include:

- `test_name` – Test case name
- `module` – Module or suite name
- `status` – `passed` or `failed`
- `duration` – Duration in seconds
- `start_time` – Start timestamp
- `end_time` – End timestamp (optional)
- `error_message` – Error details for failures (optional)

The API assigns `run_id` (e.g. `run_1`, `run_2`) and `run_by_who` to each document on bulk insert.
