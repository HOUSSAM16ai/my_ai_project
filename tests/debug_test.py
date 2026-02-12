import sys


def test_env():
    print(f"Python executable: {sys.executable}")
    print(f"Sys path: {sys.path}")
    try:
        import httpx

        print(f"httpx version: {httpx.__version__}")
        print(f"httpx file: {httpx.__file__}")
    except ImportError as e:
        print(f"ImportError: {e}")
        assert False, "httpx not found"
