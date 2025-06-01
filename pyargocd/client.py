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
        host: str | None = None,
        namespace: str = "argocd",
        context: str | None = None,
        verify_ssl: bool = False,
    ) -> None:
        """Initialise the client.

        Parameters
        ----------
        host:
            ArgoCD server host. If not provided, the client will attempt to
            use the `argocd-server` service in the provided ``namespace``.
        namespace:
            Namespace where ArgoCD is deployed.
        context:
            Optional Kubernetes context to use when loading configuration.
        verify_ssl:
            Whether to verify HTTPS certificates when talking to ArgoCD.
        """
        kubernetes.config.load_kube_config(context=context)
        self._core = k8s_client.CoreV1Api()
        self.namespace = namespace

        if host is None:
            host = f"https://argocd-server.{namespace}.svc"
        self.base_url = host.rstrip("/")

        self.session = requests.Session()
        self.session.verify = verify_ssl
        if not verify_ssl:
            warnings.filterwarnings("ignore", message="Unverified HTTPS request")

        self._authenticate()

    # ------------------------------------------------------------------
    # Authentication helpers
    def _authenticate(self) -> None:
        password = self._get_admin_password()
        response = self.session.post(
            f"{self.base_url}/api/v1/session",
            json={"username": "admin", "password": password},
            timeout=10,
        )
        response.raise_for_status()
        token = response.json()["token"]
        self.session.headers.update({"Authorization": f"Bearer {token}"})

    def _get_admin_password(self) -> str:
        secret_name = "argocd-initial-admin-secret"
        secret = self._core.read_namespaced_secret(secret_name, self.namespace)
        password_b64 = secret.data["password"]
        return base64.b64decode(password_b64).decode()

    # ------------------------------------------------------------------
    # Public API methods
    def list_apps(self) -> List[Dict[str, Any]]:
        r = self.session.get(f"{self.base_url}/api/v1/applications")
        r.raise_for_status()
        return r.json().get("items", [])

    def list_envs(self) -> List[Dict[str, Any]]:
        r = self.session.get(f"{self.base_url}/api/v1/clusters")
        r.raise_for_status()
        return r.json().get("items", [])

    def list_projects(self) -> List[Dict[str, Any]]:
        r = self.session.get(f"{self.base_url}/api/v1/projects")
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
