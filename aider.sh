#!/bin/bash
GEMINI_API_KEY=AIzaSyCReRXyX1b8WOzP-q5KRjatGU6FErO94So \
uv tool run aider  --lint-cmd 'python: just ruff' \
  --architect \
    --model openrouter/deepseek/deepseek-r1-0528 \
  --watch-files --notifications \
  --read CONVENTIONS.md \
  --read DEVELOPERS.md \
  --read STRUCTURE.md \
  --test-cmd 'just test-py'
