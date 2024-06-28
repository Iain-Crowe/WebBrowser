import time

from url import URL

DEBUG = True

class Cache:
    """
        Class used for caching `http` and `https` content
    """
    def __init__(self):
        self.cache = {}

    def get(self, url: URL) -> None:
        """
            Check cache for content with `url` and return if not expired
        """
        if url in self.cache:
            cache_entry = self.cache[url]
            if cache_entry["expiry"] > time.time():
                if DEBUG:
                    print(f"Cache hit for {url.scheme}://{url.host}:{url.port}{url.path}")

                return cache_entry["content"]
            else: 
                if DEBUG:
                    print(f"Cache expired for {url.scheme}://{url.host}:{url.port}{url.path}")
                
                del self.cache[url]
    
    def set(self, url: URL, content: str, max_age: str) -> None:
        """
            Adding a `url` to the cache and save its `content` and `max_age`
        """
        expiry = time.time() + max_age
        self.cache[url] = {"content": content, "expiry": expiry}
        if DEBUG:
            print(f"Cached {url.scheme}://{url.host}:{url.port}{url.path} for {max_age} seconds")