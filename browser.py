from typing import List, Tuple

import tkinter

from http_client import HTTPClient
from url import URL

DEBUG = True

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

    def scrollup(self, e: tkinter.Event = None) -> None:
        self.scroll = max(0, self.scroll - SCROLL_STEP)
        self.draw()

    def scrolldown(self, e: tkinter.Event = None) -> None:
        max_scroll = max(0, self.content_height - HEIGHT)
        self.scroll = min(max_scroll, self.scroll + SCROLL_STEP)
        self.draw()
    
    def mouse_scroll(self, e: tkinter.Event) -> None:
        if e.num == 4 or e.delta > 0:
            self.scrollup()
        elif e.num == 5 or e.delta < 0:
            self.scrolldown()
        self.draw()

    def resize(self, e: tkinter.Event) -> None:
        global WIDTH, HEIGHT
        WIDTH, HEIGHT = e.width, e.height
        self.display_list = layout(lex(self.body))
        self.draw()

    def draw_scrollbar(self) -> None:
        if self.content_height <= HEIGHT:
            return
        scrollbar_height = HEIGHT * HEIGHT / self.content_height
        scrollbar_pos = self.scroll * HEIGHT / self.content_height
        self.canvas.create_rectangle(
            WIDTH - 10, scrollbar_pos,
            WIDTH , scrollbar_pos + scrollbar_height,
            fill="blue"
        )

    def draw(self) -> None:
        self.canvas.delete("all")
        for x, y, c in self.display_list:
            if y > self.scroll + HEIGHT: continue
            if y + VSTEP < self.scroll: continue
            self.canvas.create_text(x, y - self.scroll, text=c)
        self.draw_scrollbar()

    def load(self, client: HTTPClient, url: URL) -> None:
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
    
def layout(text) -> List[Tuple[int, int, str]]:
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