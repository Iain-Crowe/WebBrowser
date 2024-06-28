DEBUG = True

class URL:
    def __init__(self, url: str):
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