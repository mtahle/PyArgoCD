# PyArgoCD

PyArgoCD is a minimal Python wrapper around the ArgoCD API. It authenticates using your Kubernetes configuration so no `argocd` CLI is required. The client exchanges the bearer token from your current context for an ArgoCD session token and falls back to the initial admin password if that fails. Provide the server URL and namespace and the client can list, refresh and sync your applications.

```python
from pyargocd.client import ArgoCDClient

client = ArgoCDClient(host="https://argocd.example.com", namespace="argocd")
print(client.list_apps())
```
