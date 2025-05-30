# PyArgoCD

PyArgoCD is a minimal Python wrapper around the ArgoCD API. It authenticates using your Kubernetes configuration so no `argocd` CLI is required. Provide the server URL and namespace and the client can list, refresh and sync your applications.

```python
from pyargocd.client import ArgoCDClient

client = ArgoCDClient(host="https://argocd.example.com", namespace="argocd")
print(client.list_apps())
```
