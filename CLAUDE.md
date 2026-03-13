# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FortiGate MCP Function — a Python Knative Function designed to run on Kubernetes clusters with Knative installed. Built using the Knative `func` CLI tooling (spec version 0.36.0).

## Commands

```bash
# Run locally (outside container)
func run --builder=host

# Deploy to cluster
func deploy --registry ghcr.io/<user>

# Run tests
pytest tests/

# Run a single test
pytest tests/test_func.py::test_function_handle
```

## Architecture

This is a Knative Function using the ASGI interface pattern:

- `function/func.py` — Main function implementation. The `new()` factory function returns a `Function` instance. The `Function` class implements `handle(scope, receive, send)` as an ASGI-style async handler, plus lifecycle hooks (`start`, `stop`, `alive`, `ready`).
- `function/__init__.py` — Re-exports `new` from `func.py`.
- `func.yaml` — Knative function metadata (runtime, name, spec version).
- `pyproject.toml` — Python project config. Uses hatchling build system. Requires Python >=3.9. Key deps: `httpx`, `pytest`, `pytest-asyncio`.

## Testing

Tests use `pytest-asyncio` in **strict** mode (`asyncio_mode = "strict"`). Test functions must be decorated with `@pytest.mark.asyncio`. The ASGI `send` callable is mocked directly in tests.
