"""`pytest`를 맨몸으로 실행해도 `app` 패키지를 찾도록 저장소 루트를 sys.path에 넣는다.

`python -m pytest`는 cwd가 자동으로 들어가지만 `pytest`만 실행하면 들어가지 않는다.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
