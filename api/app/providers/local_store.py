"""Local filesystem implementation of FileStore."""

from pathlib import Path

from app.providers.base import FileStore


class LocalFileStore(FileStore):
    """FileStore implementation that persists files to a local directory."""

    def __init__(self, base_path: str = "./data/files", base_url: str = "/files"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.base_url = base_url.rstrip("/")

    def put(self, path: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        target = self.base_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "wb") as f:
            f.write(data)
        return path

    def get(self, path: str) -> bytes:
        target = self.base_path / path
        if not target.exists():
            raise FileNotFoundError(f"File not found: {path}")
        with open(target, "rb") as f:
            return f.read()

    def url(self, path: str) -> str:
        clean_path = path.lstrip("/")
        return f"{self.base_url}/{clean_path}"
