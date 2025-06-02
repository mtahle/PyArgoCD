# PyArgoCD

PyArgoCD provides a thin wrapper around the ArgoCD REST API while
leveraging the Kubernetes configuration on your machine for authentication.
It performs a similar login flow to `argocd login --core` but is done
entirely in Python without requiring the `argocd` CLI to be installed.

## Features

* Authenticate to ArgoCD using the current Kubernetes context
* List applications, clusters and projects
* Refresh and synchronise applications

## Usage

```python
from pyargocd.client import ArgoCDClient

client = ArgoCDClient()
print(client.list_apps())
```

The client expects access to the Kubernetes cluster running ArgoCD. By
default it assumes the `argocd-server` service is available in the
`argocd` namespace. You can override these values when creating the
client.

## Contributing

We welcome contributions through GitHub pull requests. To get started:

1. Fork the repository and create a branch for your change.
2. Install the development requirements with `pip install -e .[dev]`.
3. Run the tests via `PYTHONPATH=. pytest -q`.
4. Open a pull request for review.

Package releases are automated. When a maintainer pushes a tag like
`v1.2.3`, the workflow in `.github/workflows/publish.yml` builds and
publishes the package to PyPI using the `PYPI_API_TOKEN` secret.


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