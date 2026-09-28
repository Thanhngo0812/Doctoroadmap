"""Short-lived Google Cloud credentials for Vertex REST requests."""

from threading import Lock

import google.auth
from google.auth.transport.requests import Request as AuthRequest


class VertexCredentials:
    def __init__(self, project: str, location: str = "global") -> None:
        if not project or not location or "/" in project or "/" in location:
            raise ValueError("Vertex project/location không hợp lệ")
        self.project, self.location = project, location
        self._credentials = None
        self._lock = Lock()

    def headers(self) -> dict[str, str]:
        with self._lock:
            if self._credentials is None:
                self._credentials, _ = google.auth.default(
                    scopes=["https://www.googleapis.com/auth/cloud-platform"]
                )
            if not self._credentials.valid:
                self._credentials.refresh(AuthRequest())
            return {"Authorization": f"Bearer {self._credentials.token}",
                    "x-goog-user-project": self.project}

    def url(self, model: str, operation: str) -> str:
        return (f"https://aiplatform.googleapis.com/v1/projects/{self.project}"
                f"/locations/{self.location}/publishers/google/models/{model}:{operation}")
