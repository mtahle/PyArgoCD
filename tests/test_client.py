from unittest import mock

import pytest
import requests

from pyargocd.client import ArgoCDClient


def make_client():
    with mock.patch("kubernetes.config.load_kube_config"), \
            mock.patch("kubernetes.client.CoreV1Api") as core, \
            mock.patch("kubernetes.client.ApiClient") as api_client:
        core.return_value.read_namespaced_secret.return_value.data = {
            "password": "cGFzc3dvcmQ="  # base64 for "password"
        }
        api_client.return_value.configuration.api_key = {"authorization": "Bearer k8s"}
        with mock.patch("requests.Session.post") as post:
            post.return_value.json.return_value = {"token": "dummy"}
            post.return_value.raise_for_status.return_value = None
            client = ArgoCDClient(host="https://example.com", namespace="argocd")
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


def test_login_with_credentials():
    with mock.patch("kubernetes.config.load_kube_config"), \
            mock.patch("kubernetes.client.CoreV1Api"):
        with mock.patch("requests.Session.post") as post:
            post.return_value.json.return_value = {"token": "dummy"}
            post.return_value.raise_for_status.return_value = None
            client = ArgoCDClient(
                host="https://example.com",
                namespace="argocd",
                username="foo",
                password="bar",
            )
            post.assert_called_with(
                "https://example.com/api/v1/session",
                json={"username": "foo", "password": "bar"},
                timeout=10,
            )


def test_fallback_to_admin_password():
    with mock.patch("kubernetes.config.load_kube_config"), \
            mock.patch("kubernetes.client.CoreV1Api") as core, \
            mock.patch("kubernetes.client.ApiClient") as api_client:
        core.return_value.read_namespaced_secret.return_value.data = {
            "password": "cGFzc3dvcmQ="
        }
        api_client.return_value.configuration.api_key = {"authorization": "Bearer k8s"}

        call_responses = []

        def side_effect(*args, **kwargs):
            if not call_responses:
                call_responses.append('first')
                raise requests.exceptions.RequestException
            mock_resp = mock.Mock()
            mock_resp.json.return_value = {"token": "dummy"}
            mock_resp.raise_for_status.return_value = None
            return mock_resp

        with mock.patch("requests.Session.post", side_effect=side_effect) as post:
            ArgoCDClient(host="https://example.com", namespace="argocd")
            assert post.call_count == 2
            post.assert_called_with(
                "https://example.com/api/v1/session",
                json={"username": "admin", "password": "password"},
                timeout=10,
            )


def test_default_ssl_verification():
    session_mock = mock.MagicMock()
    session_mock.post.return_value.json.return_value = {"token": "dummy"}
    session_mock.post.return_value.raise_for_status.return_value = None
    with mock.patch("requests.Session", return_value=session_mock):
        with mock.patch("kubernetes.config.load_kube_config"), \
                mock.patch("kubernetes.client.CoreV1Api") as core, \
                mock.patch("kubernetes.client.ApiClient") as api_client:
            core.return_value.read_namespaced_secret.return_value.data = {
                "password": "cGFzc3dvcmQ="
            }
            api_client.return_value.configuration.api_key = {
                "authorization": "Bearer k8s"
            }
            ArgoCDClient(host="https://example.com", namespace="argocd")
    assert session_mock.verify is True


def test_disable_ssl_verification():
    session_mock = mock.MagicMock()
    session_mock.post.return_value.json.return_value = {"token": "dummy"}
    session_mock.post.return_value.raise_for_status.return_value = None
    with mock.patch("requests.Session", return_value=session_mock):
        with mock.patch("kubernetes.config.load_kube_config"), \
                mock.patch("kubernetes.client.CoreV1Api") as core, \
                mock.patch("kubernetes.client.ApiClient") as api_client, \
                mock.patch("warnings.filterwarnings") as filterwarn:
            core.return_value.read_namespaced_secret.return_value.data = {
                "password": "cGFzc3dvcmQ="
            }
            api_client.return_value.configuration.api_key = {
                "authorization": "Bearer k8s"
            }
            ArgoCDClient(
                host="https://example.com",
                namespace="argocd",
                verify_ssl=False,
            )
    assert session_mock.verify is False
    filterwarn.assert_called_with("ignore", message="Unverified HTTPS request")
