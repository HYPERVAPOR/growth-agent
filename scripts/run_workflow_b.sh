#!/bin/bash
cd /home/openclaw/.openclaw/workspace/growth-agent
/home/openclaw/.local/bin/uv run -q python -m growth_agent.main run workflow-b
