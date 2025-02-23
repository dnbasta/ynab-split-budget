import requests

YNAB_BASE_URL = 'https://api.ynab.com/v1/'

class Session(requests.Session):
    def __init__(self, token: str):
        super().__init__()
        self.request_count = 0
        self.headers.update({'Authorization': f'Bearer {token}'})

    def request(self, *args, **kwargs):
        self.request_count += 1
        return super().request(*args, **kwargs)