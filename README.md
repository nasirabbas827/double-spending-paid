# Double Spending Paid

double-spending-paid is a local blockchain simulation for exploring double-spending scenarios.

![Flask](https://img.shields.io/badge/Flask-2563EB?style=flat-square)

## Overview

The Flask implementation is organized around the entry points and modules below.

## Implemented workflows

The source defines these handlers:

- **Index** — `index`
- **Blockchain** — `blockchain`
- **Transactions** — `transactions`
- **Create Transaction** — `create_transaction`
- **Mine Block** — `mine_block`
- **Attack** — `attack`
- **Analytics** — `analytics`
- **Serve Plots** — `serve_plots`
- **Download Csv** — `download_csv`

## Getting started

### 1. Get the project

```bash
git clone https://github.com/nasirabbas827/double-spending-paid.git
cd double-spending-paid
```

### 2. Prepare Python

Create an isolated environment:

```bash
python -m venv .venv
```

Activate it with `.venv\Scripts\activate` on Windows Command Prompt, or `source .venv/bin/activate` on macOS/Linux.

No requirements file is included. The inspected Python imports indicate these dependencies as a starting point:

```bash
python -m pip install Flask pandas matplotlib simpy
```

Dependency versions are not pinned in this repository.

### 3. Configure and run

Run from the repository root so relative file paths resolve correctly:

```bash
python app.py
```

Open http://127.0.0.1:5000/, or use the address printed by the application.

## Repository guide

| Path | Purpose |
| --- | --- |
| [`app.py`](app.py) | Application entry point |
| [`static`](static) | Static application assets |
| [`templates`](templates) | HTML page templates |

## Development notes

These setup instructions are based on the repository source. The application has not been executed as part of this documentation update; verify dependencies and configuration in your local environment.
