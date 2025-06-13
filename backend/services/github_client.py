import os
import base64
import requests
from typing import List, Dict, Any, Optional
from utils.logger import logger


class GitHubClient:
    """Simple GitHub REST API client."""

    def __init__(self, token: Optional[str] = None) -> None:
        self.token = token or os.getenv("GITHUB_TOKEN")
        if not self.token:
            raise RuntimeError("GITHUB_TOKEN environment variable not set")
        self.base_url = "https://api.github.com"
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github+json",
            }
        )

    def _request(self, method: str, url: str, **kwargs) -> Any:
        full_url = f"{self.base_url}{url}"
        resp = self.session.request(method, full_url, **kwargs)
        if resp.status_code >= 400:
            logger.error(f"GitHub API error {resp.status_code}: {resp.text}")
            resp.raise_for_status()
        return resp.json()

    def list_repos(self) -> List[Dict[str, Any]]:
        """List repositories accessible by the token."""
        return self._request("GET", "/user/repos")

    def get_tree(self, owner: str, repo: str, ref: str = "HEAD") -> Dict[str, Any]:
        """Fetch repository tree for given ref."""
        return self._request(
            "GET", f"/repos/{owner}/{repo}/git/trees/{ref}", params={"recursive": "1"}
        )

    def get_file_content(self, owner: str, repo: str, path: str, ref: str = "main") -> str:
        """Get file content as text."""
        data = self._request(
            "GET", f"/repos/{owner}/{repo}/contents/{path}", params={"ref": ref}
        )
        if data.get("encoding") == "base64":
            return base64.b64decode(data["content"]).decode()
        return data.get("content", "")

    def commit_file(
        self,
        owner: str,
        repo: str,
        path: str,
        content: str,
        message: str,
        branch: str = "main",
    ) -> Any:
        """Create or update a file in the repository."""
        b64 = base64.b64encode(content.encode()).decode()
        sha = None
        try:
            meta = self._request(
                "GET", f"/repos/{owner}/{repo}/contents/{path}", params={"ref": branch}
            )
            sha = meta.get("sha")
        except requests.HTTPError as e:
            if e.response.status_code != 404:
                raise
        payload = {"message": message, "content": b64, "branch": branch}
        if sha:
            payload["sha"] = sha
        return self._request(
            "PUT", f"/repos/{owner}/{repo}/contents/{path}", json=payload
        )
