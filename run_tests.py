import subprocess
import sys


def main() -> int:
    return subprocess.call([sys.executable, "-m", "pytest", "tests", "-q"])


if __name__ == "__main__":
    raise SystemExit(main())
