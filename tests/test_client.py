from unittest import mock
import pytest
from pyargocd.client import ArgoCDClient

def make_client():
    with mock.patch("kubernetes.config.load_kube_config"), \
            mock.patch("kubernetes.client.CoreV1Api") as core:
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

