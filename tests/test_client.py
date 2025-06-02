from unittest import mock
import sys
import types
import pytest
import requests

# ---------------------------------------------------------------------------
# Inject a minimal ``kubernetes`` module so the tests can run without the real
# dependency being installed.  ``ArgoCDClient`` expects ``kubernetes.config``
# and ``kubernetes.client`` to be importable with the following attributes.
config_mod = types.ModuleType("kubernetes.config")
client_mod = types.ModuleType("kubernetes.client")

def load_kube_config(context=None):
    """Dummy ``load_kube_config`` used by the tests."""
    return None

class CoreV1Api:
    def read_namespaced_secret(self, name, namespace):
        pass

class ApiClient:
    def __init__(self):
        self.configuration = type("Config", (), {"api_key": {}})()

config_mod.load_kube_config = load_kube_config
client_mod.CoreV1Api = CoreV1Api
client_mod.ApiClient = ApiClient

kubernetes_mod = types.ModuleType("kubernetes")
kubernetes_mod.config = config_mod
kubernetes_mod.client = client_mod

sys.modules.setdefault("kubernetes", kubernetes_mod)
sys.modules.setdefault("kubernetes.config", config_mod)
sys.modules.setdefault("kubernetes.client", client_mod)

from pyargocd.client import ArgoCDClient

def make_client():
    with mock.patch("kubernetes.config.load_kube_config"), \
            mock.patch("kubernetes.client.ApiClient") as api_client, \
            mock.patch("kubernetes.client.CoreV1Api") as core:
        api_client.return_value.configuration.api_key = {"authorization": "k8sToken"}
        core.return_value.read_namespaced_secret.return_value.data = {
            "password": "cGFzc3dvcmQ="  # base64 for "password"
        }
        with mock.patch("requests.Session.post") as post:
            post.return_value.json.return_value = {"token": "dummy"}
            post.return_value.raise_for_status.return_value = None
            client = ArgoCDClient(host="https://example.com")
    return client


def test_list_apps():
    client = make_client()
    with mock.patch.object(client.session, "get") as get:
        get.return_value.json.return_value = {"items": [1, 2]}
        get.return_value.raise_for_status.return_value = None
        assert client.list_apps() == [1, 2]


def test_refresh_sync():
    client = make_client()
    with mock.patch.object(client.session, "post") as post:
        post.return_value.raise_for_status.return_value = None
        client.refresh_app("myapp")
        client.sync_app("myapp")
        assert post.call_count == 2


def test_login_fallback_to_admin():
    with mock.patch("kubernetes.config.load_kube_config"), \
            mock.patch("kubernetes.client.ApiClient") as api_client, \
            mock.patch("kubernetes.client.CoreV1Api") as core, \
            mock.patch("requests.Session.post") as post:
        api_client.return_value.configuration.api_key = {"authorization": "k8sToken"}
        core.return_value.read_namespaced_secret.return_value.data = {
            "password": "cGFzc3dvcmQ="
        }
        first_resp = mock.Mock()
        first_resp.raise_for_status.side_effect = requests.HTTPError()
        second_resp = mock.Mock()
        second_resp.json.return_value = {"token": "dummy"}
        second_resp.raise_for_status.return_value = None
        post.side_effect = [first_resp, second_resp]
        ArgoCDClient(host="https://example.com")
        assert post.call_args_list[0].kwargs["json"] == {"token": "k8sToken"}
        assert post.call_args_list[1].kwargs["json"] == {"username": "admin", "password": "password"}

