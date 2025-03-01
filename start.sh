#!/bin/bash
uvicorn src.web_interface:app --host 0.0.0.0 --port $PORT
