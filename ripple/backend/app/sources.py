"""Where source snapshots come from. Code is only ever *read*, never executed."""
from __future__ import annotations

import io
import time
import zipfile
from typing import Protocol

import httpx
import jwt

from .config import settings
from .engine.gitutil import file_authors, files_at_ref
from .models import Repository

MAX_ZIP_BYTES = 100 * 1024 * 1024
MAX_UNCOMPRESSED = 300 * 1024 * 1024
MAX_FILES = 30_000
MAX_FILE_BYTES = 1_000_000


class SourceProvider(Protocol):
    def snapshot(self, repo: Repository, ref: str) -> dict[str, str]: ...


class LocalGitProvider:
    """Self-hosted / development: reads a local git repository."""
    def snapshot(self, repo: Repository, ref: str) -> dict[str, str]:
        return files_at_ref(repo.local_path, ref)

    def authors(self, repo: Repository, ref: str, paths: list[str]):
        return file_authors(repo.local_path, ref, paths)


class GitHubProvider:
    """Uses a GitHub App installation token (read-only 'contents' permission) to download a zipball."""

    def _app_jwt(self) -> str:
        now = int(time.time())
        return jwt.encode({"iat": now - 60, "exp": now + 540, "iss": settings.github_app_id},
                          settings.github_app_private_key.replace("\\n", "\n"), algorithm="RS256")

    def _installation_token(self, installation_id: str) -> str:
        r = httpx.post(f"https://api.github.com/app/installations/{installation_id}/access_tokens",
                       headers={"Authorization": f"Bearer {self._app_jwt()}", "Accept": "application/vnd.github+json"},
                       timeout=20)
        r.raise_for_status()
        return r.json()["token"]   # short-lived (1h); never persisted

    def comment(self, repo: Repository, pr_number: int, body: str) -> None:
        token = self._installation_token(repo.installation_id)
        r = httpx.post(f"https://api.github.com/repos/{repo.full_name}/issues/{pr_number}/comments",
                       headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
                       json={"body": body[:60000]}, timeout=20)
        r.raise_for_status()

    def list_repositories(self, installation_id: str) -> list[dict]:
        token = self._installation_token(installation_id)
        r = httpx.get("https://api.github.com/installation/repositories?per_page=100",
                      headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}, timeout=20)
        r.raise_for_status()
        return [{"id": str(x["id"]), "name": x["name"], "full_name": x["full_name"], "private": x["private"]}
                for x in r.json().get("repositories", [])]

    def snapshot(self, repo: Repository, ref: str) -> dict[str, str]:
        token = self._installation_token(repo.installation_id)
        with httpx.stream("GET", f"https://api.github.com/repos/{repo.full_name}/zipball/{ref}",
                          headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
                          follow_redirects=True, timeout=120) as r:
            r.raise_for_status()
            buf = io.BytesIO()
            for chunk in r.iter_bytes():
                buf.write(chunk)
                if buf.tell() > MAX_ZIP_BYTES:
                    raise ValueError("repository archive exceeds size limit")
        return _read_zip(buf)


def _read_zip(buf: io.BytesIO) -> dict[str, str]:
    files: dict[str, str] = {}
    with zipfile.ZipFile(buf) as z:
        infos = [i for i in z.infolist() if not i.is_dir()]
        if len(infos) > MAX_FILES or sum(i.file_size for i in infos) > MAX_UNCOMPRESSED:
            raise ValueError("repository exceeds analysis limits")   # zip-bomb protection
        for i in infos:
            path = i.filename.split("/", 1)[-1]
            if ".." in path.split("/"):
                continue
            if path.endswith(".py") and i.file_size <= MAX_FILE_BYTES:
                files[path] = z.read(i).decode("utf-8", "replace")
            else:
                files[path] = f"crc:{i.CRC}"
    return files


def get_provider(repo: Repository) -> SourceProvider:
    if repo.local_path:
        if not settings.allow_local_repos:
            raise PermissionError("Local repositories are disabled on this deployment")
        return LocalGitProvider()
    if repo.full_name and repo.installation_id:
        return GitHubProvider()
    raise ValueError("Repository has no source configured")
