class HTTPError(Exception):
    pass

class Session:
    def __init__(self):
        self.headers = {}
        self.verify = True

    def get(self, *args, **kwargs):
        raise NotImplementedError

    def post(self, *args, **kwargs):
        raise NotImplementedError
