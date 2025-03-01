#!/bin/bash
playwright install --with-deps
uvicorn src.web_interface:app --host 0.0.0.0 --port $PORT
