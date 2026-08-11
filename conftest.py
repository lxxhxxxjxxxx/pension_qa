"""pytest 부트스트랩 — 저장소 루트를 import 경로에 올린다.

`python -m pytest`는 cwd를 자동으로 넣지만, 맨 `pytest`는 넣지 않아
`from app import ...`가 수집 단계에서 깨진다. 두 형태 모두 동작하게 맞춘다.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
