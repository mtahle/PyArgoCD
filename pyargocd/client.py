"""Client for interacting with ArgoCD using Kubernetes authentication."""
from __future__ import annotations

import base64
import warnings
from typing import Any, Dict, List

import kubernetes
from kubernetes import client as k8s_client
import requests


class ArgoCDClient:
    """Simple wrapper around the ArgoCD REST API."""

    def __init__(
        self,
        host: str,
        namespace: str,
        *,
        username: str | None = None,
        password: str | None = None,
        context: str | None = None,
        verify_ssl: bool = True,
    ) -> None:
        """Initialise the client.

        Parameters
        ----------
        host:
            Fully qualified URL of the ArgoCD server.
        namespace:
            Namespace where ArgoCD is deployed.
        username:
            Optional username for login. If omitted the client will try the
            initial admin secret and finally fall back to the current
            Kubernetes credentials.
        password:
            Password for ``username`` if provided.
        context:
            Optional Kubernetes context to use when loading configuration.
        verify_ssl:
            Whether to verify HTTPS certificates when talking to ArgoCD.
        """
        kubernetes.config.load_kube_config(context=context)
        self._core = k8s_client.CoreV1Api()
        self.namespace = namespace
        self.username = username
        self.password = password

        self.base_url = host.rstrip("/")

        self.session = requests.Session()
        self.session.verify = verify_ssl
        if not verify_ssl:
            warnings.filterwarnings("ignore", message="Unverified HTTPS request")

        self._authenticate()

    # ------------------------------------------------------------------
    # Authentication helpers
    def _authenticate(self) -> None:
        if self.username and self.password:
            token = self._login(self.username, self.password)
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            return

        token = self._get_kube_token()
        if token:
            try:
                token = self._login_with_token(token)
                self.session.headers.update({"Authorization": f"Bearer {token}"})
                return
            except requests.exceptions.RequestException:
                pass

        try:
            password = self._get_admin_password()
            token = self._login("admin", password)
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            return
        except (kubernetes.client.exceptions.ApiException, requests.exceptions.RequestException):
            raise RuntimeError("Failed to authenticate to ArgoCD")

    def _login(self, username: str, password: str) -> str:
        response = self.session.post(
            f"{self.base_url}/api/v1/session",
            json={"username": username, "password": password},
            timeout=10,
        )
        response.raise_for_status()
        return response.json()["token"]

    def _login_with_token(self, kube_token: str) -> str:
        response = self.session.post(
            f"{self.base_url}/api/v1/session",
            json={"token": kube_token},
            timeout=10,
        )
        response.raise_for_status()
        return response.json()["token"]

    def _get_admin_password(self) -> str:
        secret_name = "argocd-initial-admin-secret"
        secret = self._core.read_namespaced_secret(secret_name, self.namespace)
        password_b64 = secret.data["password"]
        return base64.b64decode(password_b64).decode()

    def _get_kube_token(self) -> str | None:
        cfg = k8s_client.ApiClient().configuration
        token = cfg.api_key.get("authorization") if cfg.api_key else None
        if not token:
            return None
        if token.startswith("Bearer "):
            return token.split(" ", 1)[1]
        return token

    # ------------------------------------------------------------------
    # Public API methods
    def list_apps(self) -> List[Dict[str, Any]]:
        r = self.session.get(f"{self.base_url}/api/v1/applications", timeout=10)
        r.raise_for_status()
        return r.json().get("items", [])

    def list_envs(self) -> List[Dict[str, Any]]:
        r = self.session.get(f"{self.base_url}/api/v1/clusters", timeout=10)
        r.raise_for_status()
        return r.json().get("items", [])

    def list_projects(self) -> List[Dict[str, Any]]:
        r = self.session.get(f"{self.base_url}/api/v1/projects", timeout=10)
        r.raise_for_status()
        return r.json().get("items", [])

    def refresh_app(self, app_name: str) -> None:
        r = self.session.post(
            f"{self.base_url}/api/v1/applications/{app_name}/refresh",
            json={},
        )
        r.raise_for_status()

    def sync_app(self, app_name: str) -> None:
        r = self.session.post(
            f"{self.base_url}/api/v1/applications/{app_name}/sync",
            json={},
        )
        r.raise_for_status()
