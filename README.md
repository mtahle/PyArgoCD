# PyArgoCD

PyArgoCD is a minimal Python wrapper around the ArgoCD API. It authenticates using your Kubernetes configuration so no `argocd` CLI is required. The client exchanges the bearer token from your current context for an ArgoCD session token and falls back to the initial admin password if that fails. Provide the server URL and namespace and the client can list, refresh and sync your applications.

```python
from pyargocd.client import ArgoCDClient

client = ArgoCDClient(host="https://argocd.example.com", namespace="argocd")
print(client.list_apps())
```

SSL certificates are verified by default. If you are using a self-signed
certificate, pass `verify_ssl=False` when creating the client:

```python
client = ArgoCDClient(
    host="https://argocd.example.com",
    namespace="argocd",
    verify_ssl=False,
)
```

## Installation

Install the package along with the development dependencies defined in
`pyproject.toml`:

```bash
pip install -e .[dev]
```

## Running tests

After installing the development dependencies, run the test suite with:

```bash
PYTHONPATH=. pytest -q
```
