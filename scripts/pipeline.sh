#!/bin/zsh
# Atalho: repassa para o pipeline em Python
cd "$(dirname "$0")/.." && python3 pipeline.py "$@"
