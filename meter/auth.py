# meter/auth.py
#
# Authenticates with the BTU meter API and manages the access token lifecycle.
#
# Endpoint: POST {API_BASE_URL}/oauth/token
# Params:   client_id, client_secret (query string)
# Response: { "code": 0, "access_token": "...", "expires_in": 7200 }

# Note: these imports assume the project is executed from the repository root.
import time
from typing import Optional

import requests

from constants import (
    API_BASE_URL,
    API_CLIENT_ID,
    API_CLIENT_SECRET,
    API_TIMEOUT,
    API_USER_AGENT,
    TOKEN_REFRESH_BUFFER,
)


class AuthenticationError(Exception):
    """Raised when the BTU meter API rejects authentication or returns no token."""
    pass


# Module-level token cache.
_token: Optional[str] = None
_token_expiry: float = 0.0


def get_access_token() -> str:
    """
    Return a valid access token, refreshing from the API when needed.

    Caches the token in module-level state. Refreshes when fewer than
    TOKEN_REFRESH_BUFFER seconds remain before expiry.

    Returns:
        str: A valid access token.

    Raises:
        AuthenticationError: If the API request fails or returns an error.
    """
    global _token, _token_expiry

    now = time.time()
    if _token and now < _token_expiry - TOKEN_REFRESH_BUFFER:
        return _token

    url = (
        f"{API_BASE_URL}/oauth/token"
        f"?client_id={API_CLIENT_ID}"
        f"&client_secret={API_CLIENT_SECRET}"
    )
    headers = {
        "content-Type": "application/json",
        "charset": "UTF-8",
        "client_id": API_CLIENT_ID,
        "User-Agent": API_USER_AGENT,
    }

    try:
        response = requests.post(url, headers=headers, timeout=API_TIMEOUT)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        raise AuthenticationError(f"Token request failed: {exc}") from exc

    if data.get("code") != 0:
        raise AuthenticationError(
            f"API rejected authentication. Response: {data}"
        )

    token = data.get("access_token")
    if not token:
        raise AuthenticationError(
            "API returned code 0 but did not include an access_token."
        )

    expires_in = int(data.get("expires_in", 7200))
    _token = token
    _token_expiry = now + expires_in
    return _token


if __name__ == "__main__":
    import sys
    sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.dirname(__file__)))

    url = (
        f"{API_BASE_URL}/oauth/token"
        f"?client_id={API_CLIENT_ID}"
        f"&client_secret={API_CLIENT_SECRET}"
    )
    headers = {
        "content-Type": "application/json",
        "charset": "UTF-8",
        "client_id": API_CLIENT_ID,
        "User-Agent": API_USER_AGENT,
    }

    print("=" * 60)
    print("PAIR METER API — AUTH DIAGNOSTIC")
    print("=" * 60)
    print(f"\nURL:\n  {url}\n")
    print("Headers sent:")
    for k, v in headers.items():
        print(f"  {k}: {v}")
    print()

    try:
        response = requests.post(url, headers=headers, timeout=API_TIMEOUT)
        print(f"HTTP Status : {response.status_code} {response.reason}")
        print(f"\nRaw response (first 500 chars):\n{response.text[:500]}")
    except requests.exceptions.ConnectionError as exc:
        print(f"CONNECTION ERROR: {exc}")
    except requests.exceptions.Timeout:
        print(f"TIMEOUT: No response within {API_TIMEOUT}s")
    except requests.RequestException as exc:
        print(f"REQUEST ERROR: {exc}")

    print("\n" + "=" * 60)
