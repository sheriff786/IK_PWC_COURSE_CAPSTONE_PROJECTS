"""
ContractIQ — production entry point.

Serves the FastAPI API and the Gradio UI from ONE process on ONE port:

    /          -> redirects to /ui
    /ui        -> Gradio workspace (same app_service facade as the API)
    /docs      -> Swagger UI for the API
    /health    -> health check
    /api/...   -> the 18 API endpoints

Why one process: the app keeps state in a local Chroma client, a cached
knowledge graph, and JSON files. A second process (or --workers > 1) would get
its own copy of each, so they can drift apart. Always run with --workers 1.

Place this file in the PROJECT ROOT (next to src/), then run from there:

    uvicorn serve:app --host 0.0.0.0 --port 8000 --workers 1
"""

import gradio as gr
from fastapi.responses import RedirectResponse

from src.contractiq.api import app
from src.contractiq.ui import _CSS, _HEAD, build_app


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse("/ui")


# Gradio 6 takes theme/css/head at launch time; when mounting into FastAPI they
# go to mount_gradio_app instead. The docs list css and head for sure; if your
# installed Gradio rejects theme=, remove it here and check the look locally.
theme = gr.themes.Soft(primary_hue="teal", secondary_hue="teal", neutral_hue="slate")

app = gr.mount_gradio_app(
    app,
    build_app(),
    path="/ui",
    theme=theme,
    css=_CSS,
    head=_HEAD,
)
