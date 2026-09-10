"""
In-memory streaming reader for single or split (.tar.aa, .tar.ab, ...) archives over HTTP.
"""
import io
import time
import urllib.request
import logging
from typing import List, Optional, Callable, Any

from config import USER_AGENT

logger = logging.getLogger(__name__)


class ConcatStreamReader(io.RawIOBase):
    """
    A readable stream that concatenates multiple HTTP URL streams into a single
    continuous stream in-memory.
    """

    def __init__(
        self,
        urls: List[str],
        user_agent: str = USER_AGENT,
        max_retries: int = 5,
        retry_delay: float = 2.0,
        progress_callback: Optional[Callable[[int], None]] = None,
    ):
        super().__init__()
        self.urls = list(urls)
        self.user_agent = user_agent
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.progress_callback = progress_callback

        self.current_idx = 0
        self.current_response: Optional[Any] = None
        self.current_offset = 0
        self.total_bytes_read = 0
        self._closed = False

        self._open_next_stream()

    def readable(self) -> bool:
        return True

    def seekable(self) -> bool:
        return False

    def writable(self) -> bool:
        return False

    def _open_next_stream(self, offset: int = 0) -> bool:
        """Open the next URL stream or reopen current with Range header if retrying."""
        if self.current_response is not None:
            try:
                self.current_response.close()
            except Exception:
                pass
            self.current_response = None

        if self.current_idx >= len(self.urls):
            return False

        url = self.urls[self.current_idx]
        headers = {"User-Agent": self.user_agent}
        if offset > 0:
            headers["Range"] = f"bytes={offset}-"

        for attempt in range(1, self.max_retries + 1):
            try:
                req = urllib.request.Request(url, headers=headers)
                self.current_response = urllib.request.urlopen(req, timeout=30)
                self.current_offset = offset
                return True
            except Exception as e:
                logger.warning(
                    f"HTTP stream error (url {self.current_idx + 1}/{len(self.urls)}, attempt {attempt}/{self.max_retries}): {e}"
                )
                if attempt == self.max_retries:
                    raise IOError(f"Failed to connect to {url} after {self.max_retries} attempts: {e}") from e
                time.sleep(self.retry_delay * attempt)
        return False

    def readinto(self, b) -> int:
        """Read bytes into buffer b."""
        if self._closed:
            raise ValueError("I/O operation on closed stream")

        if self.current_response is None and self.current_idx >= len(self.urls):
            return 0  # EOF

        bytes_to_read = len(b)
        total_read = 0
        mv = memoryview(b)

        while total_read < bytes_to_read:
            if self.current_response is None:
                if not self._open_next_stream():
                    break  # All URLs finished

            try:
                # Read chunk from current response
                chunk = self.current_response.read(bytes_to_read - total_read)
                if not chunk:
                    # Current file part finished, advance to next
                    self.current_idx += 1
                    self.current_offset = 0
                    self._open_next_stream()
                    continue

                chunk_len = len(chunk)
                mv[total_read : total_read + chunk_len] = chunk
                total_read += chunk_len
                self.current_offset += chunk_len
                self.total_bytes_read += chunk_len

                if self.progress_callback:
                    self.progress_callback(chunk_len)

            except Exception as e:
                logger.warning(f"Error reading stream chunk at offset {self.current_offset}: {e}. Retrying with Range...")
                # Reopen same URL at current offset
                self._open_next_stream(offset=self.current_offset)

        return total_read

    def read(self, size: int = -1) -> bytes:
        if size is None or size < 0:
            # Read all remaining bytes
            chunks = []
            while True:
                buf = bytearray(65536)
                n = self.readinto(buf)
                if n == 0:
                    break
                chunks.append(bytes(buf[:n]))
            return b"".join(chunks)

        buf = bytearray(size)
        n = self.readinto(buf)
        return bytes(buf[:n])

    def close(self):
        if not self._closed:
            self._closed = True
            if self.current_response is not None:
                try:
                    self.current_response.close()
                except Exception:
                    pass
                self.current_response = None
            super().close()
