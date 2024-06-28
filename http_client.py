import base64
import gzip
import socket
import ssl
import urllib.parse

from io import BufferedReader

from cache import Cache
from url import URL

DEBUG = True
MAX_REDIRECTS = 5

class HTTPClient:
    """
        Class for handling various requests, contains a `cache` for 
        eligiable URLs.
    """
    def __init__(self):
        self.sockets = {}
        self.redirect_count = 0
        self.cache = Cache()

    def request(self, url: URL) -> str:
        """
            Wrapper method to handle various requests at `url`

            Will call on other request methods depending on the `url.scheme`
        """
        # Check cache
        cached_content = self.cache.get(url)
        if cached_content:
            return cached_content

        # Handle request in case of cache miss
        if url.scheme == "file":
            return self.__request_file(url)
        elif url.scheme in ["http", "https"]:
            return self.__request_http(url)
        elif url.scheme == "data":
            return self.__request_data(url)
        elif url.scheme == "view-source":
            return self.__request_view_source(url)

    def __request_http(self, url: URL) -> str:
        """
            Private method to handle `http` and `https` requests

            Accepts a `URL` object and returns the content of the page as a string.
        """
        # Open socket or use exisitng socket if one is already open for a given `URL`
        if (url.host, url.port) in self.sockets:
            s = self.sockets[(url.host, url.port)]    
        else:
            s = socket.socket(
                family=socket.AF_INET,
                type=socket.SOCK_STREAM,
                proto=socket.IPPROTO_TCP
            )

            s.connect((url.host, url.port))

            if url.scheme == "https":
                ctx = ssl.create_default_context()
                s = ctx.wrap_socket(s, server_hostname=url.host)
            
        # Request headers
        headers = {
            "Host": url.host,
            "User-Agent": "MyBrowser/1.0",
            "Accept-Encoding": "gzip"
        }

        # Format GET request and send
        request = "GET {} HTTP/1.1\r\n".format(url.path)
        for header, value in headers.items():
            request += "{}: {}\r\n".format(header, value)
        request += "\r\n"
        s.send(request.encode("utf8"))

        # Recieve response and parse it
        response = s.makefile("rb", encoding="utf8", newline="\r\n")

        statusline = response.readline().decode("utf8")
        version, status, explanation = statusline.split(" ", 2)
        status = int(status)

        if DEBUG:
            print(f"Response -\n Version: {version}\n Status: {status}\n Explanation: {explanation}")

        response_headers = {}
        content_length = None
        location = None
        cache_control = None
        content_encoding = None
        transfer_encoding = None
        while True:
            line = response.readline().decode("utf8")
            if line == "\r\n": break
            header, value = line.split(":", 1)
            response_headers[header.casefold()] = value.strip()
            if header.casefold() == "content-length":
                content_length = int(value.strip())
            elif header.casefold() == "location":
                location = value.strip()
            elif header.casefold() == "cache-control":
                cache_control = value.strip()
            elif header.casefold() == "content-encoding":
                content_encoding = value.strip()
            elif header.casefold() == "transfer-encoding":
                transfer_encoding = value.strip()

        # Handle redirects if applicable 
        if status in range(300, 400) and location:
            if self.redirect_count >= MAX_REDIRECTS:
                raise Exception("Too many redirects")
            
            self.redirect_count += 1

            if location.startswith("/"):
                location = f"{url.scheme}://{url.host}{location}"
            elif not location.startswith("http"):
                location = f"{url.scheme}://{url.host}/{location}"

            if DEBUG:
                print(f"Redirecting to: {location}")

            return self.request(URL(location))
        
        if transfer_encoding == "chunked":
            content = self.__read_chunked(response)
        elif content_length is not None:
            content = response.read(content_length)
        else:
            content = response.read()

        if content_encoding == "gzip":
            content = gzip.decompress(content)

        self.redirect_count = 0

        # Cache content for this url if applicable
        if status == 200 and cache_control:
            cache_directives = cache_control.split(",")
            cacheable = True
            max_age = None
            for directive in cache_directives:
                directive = directive.strip()
                if directive == "no-store":
                    cacheable = False
                    break
                elif directive.startswith("max-age="):
                    max_age = int(directive.split("=")[1])
            if cacheable and max_age is not None:
                self.cache.set(url, content, max_age)

        return content.decode("utf8")
    
    def __read_chunked(self, response: BufferedReader) -> bytes:
        content = bytearray()
        while True:
            line = response.readline().decode("utf8").strip()
            if not line:
                break
            chunk_size = int(line, 16)
            if chunk_size == 0:
                break
            content.extend(response.read(chunk_size))
            response.readline()
        return bytes(content)

    def __request_file(self, url: URL) -> str:
        """
            Private method for reading file content at `url`
        """
        if DEBUG:
            print(f"Opening local file: {url.path}")
        with open(url.path, "r", encoding="utf8") as file:
            content = file.read()
        return content

    def __request_data(self, url: URL) -> str:
        """
            Private method for parsing `data` scheme
        """
        mime_type, data = url.data_url.split(",", 1)
        if mime_type.endswith(";base64"):
            data = base64.b64decode(data).decode('utf8')
        else:
            data = urllib.parse.unquote(data)
        return data

    def __request_view_source(self, url: URL) -> str:
        """
            Private method to unnest `url` and display the souce
        """
        return self.request(url.nested_url)