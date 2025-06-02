class CoreV1Api:
    def read_namespaced_secret(self, name, namespace):
        pass

class ApiClient:
    def __init__(self):
        self.configuration = type('Config', (), {'api_key': {}})()
