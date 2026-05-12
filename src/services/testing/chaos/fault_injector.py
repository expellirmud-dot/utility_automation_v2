import httpx
from unittest.mock import patch, MagicMock
import asyncio
import time

class FaultInjector:
    def __init__(self):
        self.patches = []
        self.original_post = httpx.Client.post
        self.original_async_post = httpx.AsyncClient.post
        self.original_get = httpx.Client.get
        self.original_async_get = httpx.AsyncClient.get

    def inject_timeout(self, target_url_part: str):
        """Simulate a timeout when calling a specific service URL."""
        
        def mock_post(client_self, url, *args, **kwargs):
            if target_url_part in str(url):
                raise httpx.TimeoutException("Injected Timeout")
            return self.original_post(client_self, url, *args, **kwargs)

        async def mock_async_post(client_self, url, *args, **kwargs):
            if target_url_part in str(url):
                await asyncio.sleep(0.1)
                raise httpx.TimeoutException("Injected Async Timeout")
            return await self.original_async_post(client_self, url, *args, **kwargs)

        self._apply_patch('httpx.Client.post', mock_post)
        self._apply_patch('httpx.AsyncClient.post', mock_async_post)

    def inject_500_error(self, target_url_part: str):
        """Simulate a 500 Internal Server Error."""
        
        def mock_post(client_self, url, *args, **kwargs):
            if target_url_part in str(url):
                resp = MagicMock()
                resp.status_code = 500
                resp.raise_for_status.side_effect = httpx.HTTPStatusError(
                    "Injected 500 Error", request=MagicMock(), response=resp
                )
                return resp
            return self.original_post(client_self, url, *args, **kwargs)

        async def mock_async_post(client_self, url, *args, **kwargs):
            if target_url_part in str(url):
                resp = MagicMock()
                resp.status_code = 500
                resp.raise_for_status.side_effect = httpx.HTTPStatusError(
                    "Injected Async 500 Error", request=MagicMock(), response=resp
                )
                return resp
            return await self.original_async_post(client_self, url, *args, **kwargs)

        self._apply_patch('httpx.Client.post', mock_post)
        self._apply_patch('httpx.AsyncClient.post', mock_async_post)

    def inject_latency(self, delay_seconds: float, target_url_part: str = ""):
        """Inject artificial network delay."""
        
        def mock_post(client_self, url, *args, **kwargs):
            if target_url_part in str(url):
                time.sleep(delay_seconds)
            return self.original_post(client_self, url, *args, **kwargs)

        async def mock_async_post(client_self, url, *args, **kwargs):
            if target_url_part in str(url):
                await asyncio.sleep(delay_seconds)
            return await self.original_async_post(client_self, url, *args, **kwargs)

        self._apply_patch('httpx.Client.post', mock_post)
        self._apply_patch('httpx.AsyncClient.post', mock_async_post)

    def _apply_patch(self, target, new_func):
        p = patch(target, new=new_func)
        p.start()
        self.patches.append(p)

    def cleanup(self):
        for p in self.patches:
            p.stop()
        self.patches = []
