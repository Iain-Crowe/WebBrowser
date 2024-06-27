from __future__ import annotations

import socket
import ssl
import base64
import urllib.parse
import time
import gzip
import tkinter

DEBUG = True
MAX_REDIRECTS = 5

WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18
SCROLL_STEP = 100

# TODO:
#   - Add Emoji Support
#   - Alternate text direction (for arabic, hebrew, etc.)
class Browser:
    def __init__(self):
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(
            self.window,
            width=WIDTH,
            height=HEIGHT
        )
        self.canvas.pack(fill=tkinter.BOTH, expand=True)
        self.scroll = 0
        self.window.bind("<Up>", self.scrollup)
        self.window.bind("<Down>", self.scrolldown)
        self.window.bind("<MouseWheel>", self.mouse_scroll)
        self.window.bind("<Button-4>", self.mouse_scroll)
        self.window.bind("<Button-5>", self.mouse_scroll)
        self.window.bind("<Configure>", self.resize)

    def scrollup(self, e = None):
        self.scroll = max(0, self.scroll - SCROLL_STEP)
        self.draw()

    def scrolldown(self, e = None):
        max_scroll = max(0, self.content_height - HEIGHT)
        self.scroll = min(max_scroll, self.scroll + SCROLL_STEP)
        self.draw()
    
    def mouse_scroll(self, e):
        if e.num == 4 or e.delta > 0:
            self.scrollup()
        elif e.num == 5 or e.delta < 0:
            self.scrolldown()
        self.draw()

    def resize(self, e):
        global WIDTH, HEIGHT
        WIDTH, HEIGHT = e.width, e.height
        self.display_list = layout(lex(self.body))
        self.draw()

    def draw_scrollbar(self):
        if self.content_height <= HEIGHT:
            return
        scrollbar_height = HEIGHT * HEIGHT / self.content_height
        scrollbar_pos = self.scroll * HEIGHT / self.content_height
        self.canvas.create_rectangle(
            WIDTH - 10, scrollbar_pos,
            WIDTH , scrollbar_pos + scrollbar_height,
            fill="blue"
        )

    def draw(self):
        self.canvas.delete("all")
        for x, y, c in self.display_list:
            if y > self.scroll + HEIGHT: continue
            if y + VSTEP < self.scroll: continue
            self.canvas.create_text(x, y - self.scroll, text=c)
        self.draw_scrollbar()

    def load(self, client: HTTPClient, url: URL):
        try:
            if url.scheme == "about" and url.path == "blank":
                self.body = ""
            else:    
                self.body = client.request(url)
        except Exception as e:
            if DEBUG:
                print(f"Error loading URL: {e}")
            self.body = ""
        
        text = lex(self.body)
        self.display_list = layout(text)   
        self.content_height = self.display_list[-1][1] + VSTEP if self.display_list else HEIGHT
        self.draw()

class URL:
    def __init__(self, url):
        # Parse url for scheme
        # Can be `about:blank`, `view-source`, `http`, `https`, `file`, or `data`
        if url == "about:blank":
            self.scheme = "about"
            self.path = "blank"
        elif url.startswith("view-source:"):
            self.scheme = "view-source"
            self.view_source_url = url[len("view-source:"):]
        elif "://" in url:
            self.scheme, url = url.split("://", 1)
        elif url.startswith("data"):
            self.scheme, url = url.split(":", 1)

        assert self.scheme in ["about", "http", "https", "file", "data", "view-source"]

        # Initialization for `http` and `https`
        if self.scheme in ["http", "https"]:
            if "/" not in url:
                url = url + "/"

            # Get host and path
            self.host, url = url.split("/", 1)
            self.path = "/" + url

            # Get port
            if self.scheme == "http":
                self.port = 80
            elif self.scheme == "https":
                self.port = 443

            if ":" in self.host:
                self.host, port = self.host.split(":", 1)
                self.port = int(port)

            # Print if `DEBUG` is True
            if DEBUG:
                print(f"URL -\n  Scheme: {self.scheme}\n  Host: {self.host}\n  Path: {self.path}\n  Port: {self.port}")
        # Initialize for `file`
        elif self.scheme == "file":
            self.path = url
            if DEBUG:
                print(f"URL -\n  Scheme: {self.scheme}\n  Path: {self.path}")
        # Initialize for `data`
        elif self.scheme == "data":
            self.data_url = url
            if DEBUG:
                print(f"URL -\n  Scheme: {self.scheme}\n  Data URL: {self.data_url}")
        # Unnest url if `view-source`
        elif self.scheme == "view-source":
            self.nested_url = URL(self.view_source_url)

class Cache:
    """
        Class used for caching `http` and `https` content
    """
    def __init__(self):
        self.cache = {}

    def get(self, url: URL):
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
    
    def set(self, url: URL, content: str, max_age: str):
        """
            Adding a `url` to the cache and save its `content` and `max_age`
        """
        expiry = time.time() + max_age
        self.cache[url] = {"content": content, "expiry": expiry}
        if DEBUG:
            print(f"Cached {url.path} for {max_age} seconds")

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
    
    def __read_chunked(self, response) -> bytes:
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

def lex(body: str) -> str:
    """
        Displays content without html tags
    """
    body = body.replace("&lt;", "<").replace("&gt;", ">")
    in_tag = False

    text = ""
    for c in body:
        if c == "<":
            in_tag = True
        elif c == ">":
            in_tag = False
        elif not in_tag:
            text += c
    
    return text
    
def layout(text):
    """
        Lays `text` out to fit the browser window.
    """
    display_list = []
    cursor_x, cursor_y = HSTEP, VSTEP
    for c in text:
        if c == "\n":
            cursor_y += VSTEP
            cursor_x = HSTEP
        else:
            display_list.append((cursor_x, cursor_y, c))
            cursor_x += HSTEP

        if cursor_x >= WIDTH - HSTEP:
            cursor_y += VSTEP
            cursor_x = HSTEP
    
    return display_list

if __name__ == "__main__":
    import sys

    client = HTTPClient()

    url = URL(sys.argv[1])
    
    Browser().load(client, url)
    tkinter.mainloop()