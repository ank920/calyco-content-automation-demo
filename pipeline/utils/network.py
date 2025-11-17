# pipeline/utils/network.py
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=2, max=20),
       retry=retry_if_exception_type(requests.exceptions.RequestException))
def safe_get(url, session=None, timeout=20, **kwargs):
    s = session or requests
    resp = s.get(url, timeout=timeout, **kwargs)
    resp.raise_for_status()
    return resp
