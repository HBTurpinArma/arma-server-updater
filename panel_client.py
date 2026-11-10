import requests


class PanelClient:
    def __init__(self, base_url, username, password):
        if not base_url:
            raise ValueError("PANEL_IP must be a panel host or URL")
        if "://" not in base_url:
            base_url = f"http://{base_url}"
        self.base_url = base_url.rstrip("/")
        self.headers = {"X-Requested-With": "XMLHttpRequest"}
        with requests.Session() as session:
            response = session.post(
                f"{self.base_url}/api/session",
                json={"username": username, "password": password},
                headers=self.headers,
                timeout=6,
            )
            response.raise_for_status()
            if not session.cookies:
                raise requests.exceptions.RequestException(
                    "Panel authentication succeeded without a session cookie"
                )
            self.cookies = session.cookies.copy()

    def post_server_action(self, server_id, action):
        return requests.post(
            f"{self.base_url}/api/servers/{server_id}/{action}",
            headers=self.headers,
            cookies=self.cookies,
            timeout=6,
        )
