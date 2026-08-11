"""`pytest`(모듈 형태가 아닌 직접 실행)에서도 `app` 패키지를 임포트할 수 있게 한다."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
