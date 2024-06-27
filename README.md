
# Simple Browser

This project is a simple browser implemented in Python using the `tkinter` library for the GUI and raw socket connections for HTTP communication. It supports basic browsing functionalities, including handling HTTP/HTTPS requests, displaying content, scrolling, and resizing. The browser also has a cache system and can handle `gzip` compression.

**Note: This is a work in progress.**

## Features

- **Basic HTTP/HTTPS Support**: Handles GET requests for `http` and `https` URLs.
- **File Support**: Can load local files using the `file` scheme.
- **Data URLs**: Supports `data` scheme URLs.
- **View Source**: Allows viewing the raw HTML source with the `view-source` scheme.
- **Scrolling**: Supports scrolling using the arrow keys and mouse wheel.
- **Resizing**: The browser window is resizable, and the layout adjusts accordingly.
- **Scrollbar**: Displays a scrollbar that reflects the visible portion of the document.
- **Error Handling**: Malformed URLs are handled gracefully by displaying a blank page.

## Requirements

- Python 3.x
- `tkinter` library (usually included with Python)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/simple-browser.git
   cd simple-browser
   ```

2. Run the browser:
   ```bash
   python browser.py <url>
   ```

## Usage

### Running the Browser

To start the browser, run the `browser.py` script with a URL as an argument:

```bash
python browser.py http://example.org/
```

### Supported Schemes

- **HTTP/HTTPS**: `http://example.com`, `https://example.com`
- **File**: `file:///path/to/local/file`
- **Data**: `data:text/html,Hello world!`
- **View Source**: `view-source:http://example.com`
- **About Blank**: `about:blank`

### Scrolling

- **Down Arrow**: Scroll down
- **Up Arrow**: Scroll up
- **Mouse Wheel**: Scroll up/down

### Resizing

- The browser window can be resized, and the content layout will adjust accordingly.

### Error Handling

- If a malformed URL is entered, the browser will display a blank page (`about:blank`).

## Code Overview

### `browser.py`

This is the main script that initializes the browser, handles user input, and renders the content.

### `URL` Class

Handles parsing and validation of URLs.

### `Cache` Class

Implements a simple cache to store and retrieve HTTP responses.

### `HTTPClient` Class

Manages HTTP connections, handles redirects, and supports gzip compression.

### `Browser` Class

Handles rendering the content, scrolling, resizing, and drawing the scrollbar.

### Helper Functions

- `lex(body)`: Strips HTML tags from the body.
- `layout(text)`: Converts text into a list of displayable items with coordinates.

## Contributing

Contributions are welcome! Please fork the repository and submit pull requests for any improvements or bug fixes.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
