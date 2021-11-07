from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Optional, Tuple
import builtins
import os
from quo.repr import RichReprResult
import sys
from array import array
from collections import Counter, defaultdict, deque, UserDict, UserList
import dataclasses
from dataclasses import dataclass, fields, is_dataclass, field
from inspect import isclass
from itertools import islice
import re

from .highlighter import ReprHighlighter
from .panel import Panel
from .table import Table
from quo._text import Text

if TYPE_CHECKING:
    from quo.console.console import ConsoleRenderable
# *********************


from typing import (
    DefaultDict,
    Callable,
    Dict,
    Iterable,
    List,
    Set,
    Union
)
from types import MappingProxyType

try:
    import attr as _attr_module
except ImportError:  # pragma: no cover
    _attr_module = None  # type: ignore

from ._loop import loop_last
from ._pick import pick_bool
from .abc import RichRenderable
from .cells import cell_len
from .highlighter import ReprHighlighter
from quo._jupyter import JupyterMixin, JupyterRenderable
from .measure import Measurement
from quo._text import Text

if TYPE_CHECKING:
    from quo.console.console import (
        Console,
        ConsoleOptions,
        HighlighterType,
        JustifyMethod,
        OverflowMethod,
        RenderResult,
    )

# Matches Jupyter's special methods
_re_jupyter_repr = re.compile(f"^_repr_.+_$")


# ***********************
import inspect
import platform
import shutil
import threading
from abc import ABC, abstractmethod
from datetime import datetime
from functools import wraps
from getpass import getpass
from html import escape
from time import monotonic
from types import FrameType, TracebackType, ModuleType
from typing import (
    IO,
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Mapping,
    NamedTuple,
    Optional,
    TextIO,
    Tuple,
    Type,
    Union,
    cast,
)

if sys.version_info >= (3, 8):
    from typing import Literal, Protocol, runtime_checkable
else:
    from typing_extensions import (
        Literal,
        Protocol,
        runtime_checkable,
    )  # pragma: no cover

from quo import themes
from quo.errors import exceptions
from quo._emoji_replace import _emoji_replace
from quo._log_render import FormatTimeCallable, LogRender
from quo.align import Align, AlignMethod
from quo.color.color import ColorSystem
from quo.control import Control
# emoji EmojiVariant
from quo._emoji import EmojiVariant
from quo.highlighter import NullHighlighter, ReprHighlighter
from quo.markup import render as render_markup
from quo.measure import Measurement, measure_renderables
from quo.pager import Pager, SystemPager
# from quo.pretty import Pretty, is_expandable
from quo.region import Region
#from quo.scope import render_scope
from quo.screen import Screen
from quo.segment import Segment
from quo.style import Style
from quo.styled import Styled
from quo.terminal_theme import DEFAULT_TERMINAL_THEME, TerminalTheme
from quo._text import Text
from quo.theme import Theme, ThemeStack

if TYPE_CHECKING:
    from quo._windows import WindowsConsoleFeatures
    from quo.live import Live
    from quo.status import Status

WINDOWS = platform.system() == "Windows"

HighlighterType = Callable[[Union[str, "Text"]], "Text"]
JustifyMethod = Literal["default", "left", "center", "right", "full"]
OverflowMethod = Literal["fold", "crop", "ellipsis", "ignore"]
TextType = Union[str, "Text"]
StyleType = Union[str, "Style"]

class NoChange:
    pass


NO_CHANGE = NoChange()


CONSOLE_HTML_FORMAT = """\
<!DOCTYPE html>
<head>
<meta charset="UTF-8">
<style>
{stylesheet}
body {{
    color: {foreground};
    background-color: {background};
}}
</style>
</head>
<html>
<body>
    <code>
        <pre style="font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace">{code}</pre>
    </code>
</body>
</html>
"""

_TERM_COLORS = {"256color": ColorSystem.EIGHT_BIT, "16color": ColorSystem.STANDARD}


class ConsoleDimensions(NamedTuple):
    """Size of the terminal."""

    width: int
    """The width of the console in 'cells'."""
    height: int
    """The height of the console in lines."""


@dataclass
class ConsoleOptions:
    """Options for __rich_console__ method."""

    size: ConsoleDimensions
    """Size of console."""
    legacy_windows: bool
    """legacy_windows: flag for legacy windows."""
    min_width: int
    """Minimum width of renderable."""
    max_width: int
    """Maximum width of renderable."""
    is_terminal: bool
    """True if the target is a terminal, otherwise False."""
    encoding: str
    """Encoding of terminal."""
    max_height: int
    """Height of container (starts as terminal)"""
    justify: Optional[JustifyMethod] = None
    """Justify value override for renderable."""
    overflow: Optional[OverflowMethod] = None
    """Overflow value override for renderable."""
    no_wrap: Optional[bool] = False
    """Disable wrapping for text."""
    highlight: Optional[bool] = None
    """Highlight override for render_str."""
    markup: Optional[bool] = None
    """Enable markup when rendering strings."""
    height: Optional[int] = None

    @property
    def ascii_only(self) -> bool:
        """Check if renderables should use ascii only."""
        return not self.encoding.startswith("utf")

    def copy(self) -> "ConsoleOptions":
        """Return a copy of the options.

        Returns:
            ConsoleOptions: a copy of self.
        """
        options: ConsoleOptions = ConsoleOptions.__new__(ConsoleOptions)
        options.__dict__ = self.__dict__.copy()
        return options

    def update(
        self,
        *,
        width: Union[int, NoChange] = NO_CHANGE,
        min_width: Union[int, NoChange] = NO_CHANGE,
        max_width: Union[int, NoChange] = NO_CHANGE,
        justify: Union[Optional[JustifyMethod], NoChange] = NO_CHANGE,
        overflow: Union[Optional[OverflowMethod], NoChange] = NO_CHANGE,
        no_wrap: Union[Optional[bool], NoChange] = NO_CHANGE,
        highlight: Union[Optional[bool], NoChange] = NO_CHANGE,
        markup: Union[Optional[bool], NoChange] = NO_CHANGE,
        height: Union[Optional[int], NoChange] = NO_CHANGE,
    ) -> "ConsoleOptions":
        """Update values, return a copy."""
        options = self.copy()
        if not isinstance(width, NoChange):
            options.min_width = options.max_width = max(0, width)
        if not isinstance(min_width, NoChange):
            options.min_width = min_width
        if not isinstance(max_width, NoChange):
            options.max_width = max_width
        if not isinstance(justify, NoChange):
            options.justify = justify
        if not isinstance(overflow, NoChange):
            options.overflow = overflow
        if not isinstance(no_wrap, NoChange):
            options.no_wrap = no_wrap
        if not isinstance(highlight, NoChange):
            options.highlight = highlight
        if not isinstance(markup, NoChange):
            options.markup = markup
        if not isinstance(height, NoChange):
            if height is not None:
                options.max_height = height
            options.height = None if height is None else max(0, height)
        return options

    def update_width(self, width: int) -> "ConsoleOptions":
        """Update just the width, return a copy.

        Args:
            width (int): New width (sets both min_width and max_width)

        Returns:
            ~ConsoleOptions: New console options instance.
        """
        options = self.copy()
        options.min_width = options.max_width = max(0, width)
        return options

    def update_dimensions(self, width: int, height: int) -> "ConsoleOptions":
        """Update the width and height, and return a copy.

        Args:
            width (int): New width (sets both min_width and max_width).
            height (int): New height.

        Returns:
            ~ConsoleOptions: New console options instance.
        """
        options = self.copy()
        options.min_width = options.max_width = max(0, width)
        options.height = height
        options.max_height = height
        return options


@runtime_checkable
class RichCast(Protocol):
    """An object that may be 'cast' to a console renderable."""

    def __rich__(self) -> Union["ConsoleRenderable", str]:  # pragma: no cover
        ...


@runtime_checkable
class ConsoleRenderable(Protocol):
    """An object that supports the console protocol."""

    def __rich_console__(
        self, console: "Console", options: "ConsoleOptions"
    ) -> "RenderResult":  # pragma: no cover
        ...


RenderableType = Union[ConsoleRenderable, RichCast, str]
"""A type that may be rendered by Console."""

RenderResult = Iterable[Union[RenderableType, Segment]]
"""The result of calling a __rich_console__ method."""


_null_highlighter = NullHighlighter()


class CaptureError(Exception):
    """An error in the Capture context manager."""


class NewLine:
    """A renderable to generate new line(s)"""

    def __init__(self, count: int = 1) -> None:
        self.count = count

    def __rich_console__(
        self, console: "Console", options: "ConsoleOptions"
    ) -> Iterable[Segment]:
        yield Segment("\n" * self.count)


class ScreenUpdate:
    """Render a list of lines at a given offset."""

    def __init__(self, lines: List[List[Segment]], x: int, y: int) -> None:
        self._lines = lines
        self.x = x
        self.y = y

    def __rich_console__(
        self, console: "Console", options: ConsoleOptions
    ) -> RenderResult:
        x = self.x
        move_to = Control.move_to
        for offset, line in enumerate(self._lines, self.y):
            yield move_to(x, offset)
            yield from line


class Capture:
    """Context manager to capture the result of printing to the console.
    See :meth:`~rich.console.Console.capture` for how to use.

    Args:
        console (Console): A console instance to capture output.
    """

    def __init__(self, console: "Console") -> None:
        self._console = console
        self._result: Optional[str] = None

    def __enter__(self) -> "Capture":
        self._console.begin_capture()
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        self._result = self._console.end_capture()

    def get(self) -> str:
        """Get the result of the capture."""
        if self._result is None:
            raise CaptureError(
                "Capture result is not available until context manager exits."
            )
        return self._result


class ThemeContext:
    """A context manager to use a temporary theme. See :meth:`~rich.console.Console.use_theme` for usage."""

    def __init__(self, console: "Console", theme: Theme, inherit: bool = True) -> None:
        self.console = console
        self.theme = theme
        self.inherit = inherit

    def __enter__(self) -> "ThemeContext":
        self.console.push_theme(self.theme)
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        self.console.pop_theme()


class PagerContext:
    """A context manager that 'pages' content. See :meth:`~rich.console.Console.pager` for usage."""

    def __init__(
        self,
        console: "Console",
        pager: Optional[Pager] = None,
        styles: bool = False,
        links: bool = False,
    ) -> None:
        self._console = console
        self.pager = SystemPager() if pager is None else pager
        self.styles = styles
        self.links = links

    def __enter__(self) -> "PagerContext":
        self._console._enter_buffer()
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        if exc_type is None:
            with self._console._lock:
                buffer: List[Segment] = self._console._buffer[:]
                del self._console._buffer[:]
                segments: Iterable[Segment] = buffer
                if not self.styles:
                    segments = Segment.strip_styles(segments)
                elif not self.links:
                    segments = Segment.strip_links(segments)
                content = self._console._render_buffer(segments)
            self.pager.show(content)
        self._console._exit_buffer()


class ScreenContext:
    """A context manager that enables an alternative screen. See :meth:`~rich.console.Console.screen` for usage."""

    def __init__(
        self, console: "Console", hide_cursor: bool, style: StyleType = ""
    ) -> None:
        self.console = console
        self.hide_cursor = hide_cursor
        self.screen = Screen(style=style)
        self._changed = False

    def update(
        self, *renderables: RenderableType, style: Optional[StyleType] = None
    ) -> None:
        """Update the screen.

        Args:
            renderable (RenderableType, optional): Optional renderable to replace current renderable,
                or None for no change. Defaults to None.
            style: (Style, optional): Replacement style, or None for no change. Defaults to None.
        """
        if renderables:
            self.screen.renderable = (
                Group(*renderables) if len(renderables) > 1 else renderables[0]
            )
        if style is not None:
            self.screen.style = style
        self.console.echo(self.screen, end="")

    def __enter__(self) -> "ScreenContext":
        self._changed = self.console.set_alt_screen(True)
        if self._changed and self.hide_cursor:
            self.console.show_cursor(False)
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        if self._changed:
            self.console.set_alt_screen(False)
            if self.hide_cursor:
                self.console.show_cursor(True)


class Group:
    """Takes a group of renderables and returns a renderable object that renders the group.

    Args:
        renderables (Iterable[RenderableType]): An iterable of renderable objects.
        fit (bool, optional): Fit dimension of group to contents, or fill available space. Defaults to True.
    """

    def __init__(self, *renderables: "RenderableType", fit: bool = True) -> None:
        self._renderables = renderables
        self.fit = fit
        self._render: Optional[List[RenderableType]] = None

    @property
    def renderables(self) -> List["RenderableType"]:
        if self._render is None:
            self._render = list(self._renderables)
        return self._render

    def __rich_measure__(
        self, console: "Console", options: "ConsoleOptions"
    ) -> "Measurement":
        if self.fit:
            return measure_renderables(console, options, self.renderables)
        else:
            return Measurement(options.max_width, options.max_width)

    def __rich_console__(
        self, console: "Console", options: "ConsoleOptions"
    ) -> RenderResult:
        yield from self.renderables


RenderGroup = Group  # TODO: deprecate at some point


def group(fit: bool = True) -> Callable[..., Callable[..., Group]]:
    """A decorator that turns an iterable of renderables in to a group.

    Args:
        fit (bool, optional): Fit dimension of group to contents, or fill available space. Defaults to True.
    """

    def decorator(
        method: Callable[..., Iterable[RenderableType]]
    ) -> Callable[..., Group]:
        """Convert a method that returns an iterable of renderables in to a RenderGroup."""

        @wraps(method)
        def _replace(*args: Any, **kwargs: Any) -> Group:
            renderables = method(*args, **kwargs)
            return Group(*renderables, fit=fit)

        return _replace

    return decorator


render_group = group


def _is_jupyter() -> bool:  # pragma: no cover
    """Check if we're running in a Jupyter notebook."""
    try:
        get_ipython  # type: ignore
    except NameError:
        return False
    ipython = get_ipython()  # type: ignore
    shell = ipython.__class__.__name__
    if "google.colab" in str(ipython.__class__) or shell == "ZMQInteractiveShell":
        return True  # Jupyter notebook or qtconsole
    elif shell == "TerminalInteractiveShell":
        return False  # Terminal running IPython
    else:
        return False  # Other type (?)


COLOR_SYSTEMS = {
    "standard": ColorSystem.STANDARD,
    "256": ColorSystem.EIGHT_BIT,
    "truecolor": ColorSystem.TRUECOLOR,
    "windows": ColorSystem.WINDOWS,
}


_COLOR_SYSTEMS_NAMES = {system: name for name, system in COLOR_SYSTEMS.items()}


@dataclass
class ConsoleThreadLocals(threading.local):
    """Thread local values for Console context."""

    theme_stack: ThemeStack
    buffer: List[Segment] = field(default_factory=list)
    buffer_index: int = 0


class RenderHook(ABC):
    """Provides hooks in to the render process."""

    @abstractmethod
    def process_renderables(
        self, renderables: List[ConsoleRenderable]
    ) -> List[ConsoleRenderable]:
        """Called with a list of objects to render.

        This method can return a new list of renderables, or modify and return the same list.

        Args:
            renderables (List[ConsoleRenderable]): A number of renderable objects.

        Returns:
            List[ConsoleRenderable]: A replacement list of renderables.
        """


_windows_console_features: Optional["WindowsConsoleFeatures"] = None


def get_windows_console_features() -> "WindowsConsoleFeatures":  # pragma: no cover
    global _windows_console_features
    if _windows_console_features is not None:
        return _windows_console_features
    from ._windows import get_windows_console_features

    _windows_console_features = get_windows_console_features()
    return _windows_console_features


def detect_legacy_windows() -> bool:
    """Detect legacy Windows."""
    return WINDOWS and not get_windows_console_features().vt


if detect_legacy_windows():  # pragma: no cover
    from colorama import init

    init(strip=False)


class Console:
    """A high level console interface.

    Args:
        color_system (str, optional): The color system supported by your terminal,
            either ``"standard"``, ``"256"`` or ``"truecolor"``. Leave as ``"auto"`` to autodetect.
        force_terminal (Optional[bool], optional): Enable/disable terminal control codes, or None to auto-detect terminal. Defaults to None.
        force_jupyter (Optional[bool], optional): Enable/disable Jupyter rendering, or None to auto-detect Jupyter. Defaults to None.
        force_interactive (Optional[bool], optional): Enable/disable interactive mode, or None to auto detect. Defaults to None.
        soft_wrap (Optional[bool], optional): Set soft wrap default on print method. Defaults to False.
        theme (Theme, optional): An optional style theme object, or ``None`` for default theme.
        stderr (bool, optional): Use stderr rather than stdout if ``file`` is not specified. Defaults to False.
        file (IO, optional): A file object where the console should write to. Defaults to stdout.
        quiet (bool, Optional): Boolean to suppress all output. Defaults to False.
        width (int, optional): The width of the terminal. Leave as default to auto-detect width.
        height (int, optional): The height of the terminal. Leave as default to auto-detect height.
        style (StyleType, optional): Style to apply to all output, or None for no style. Defaults to None.
        no_color (Optional[bool], optional): Enabled no color mode, or None to auto detect. Defaults to None.
        tab_size (int, optional): Number of spaces used to replace a tab character. Defaults to 8.
        record (bool, optional): Boolean to enable recording of terminal output,
            required to call :meth:`export_html` and :meth:`export_text`. Defaults to False.
        markup (bool, optional): Boolean to enable :ref:`console_markup`. Defaults to True.
        emoji (bool, optional): Enable emoji code. Defaults to True.
        emoji_variant (str, optional): Optional emoji variant, either "text" or "emoji". Defaults to None.
        highlight (bool, optional): Enable automatic highlighting. Defaults to True.
        log_time (bool, optional): Boolean to enable logging of time by :meth:`log` methods. Defaults to True.
        log_path (bool, optional): Boolean to enable the logging of the caller by :meth:`log`. Defaults to True.
        log_time_format (Union[str, TimeFormatterCallable], optional): If ``log_time`` is enabled, either string for strftime or callable that formats the time. Defaults to "[%X] ".
        highlighter (HighlighterType, optional): Default highlighter.
        legacy_windows (bool, optional): Enable legacy Windows mode, or ``None`` to auto detect. Defaults to ``None``.
        safe_box (bool, optional): Restrict box options that don't render on legacy Windows.
        get_datetime (Callable[[], datetime], optional): Callable that gets the current time as a datetime.datetime object (used by Console.log),
            or None for datetime.now.
        get_time (Callable[[], time], optional): Callable that gets the current time in seconds, default uses time.monotonic.
    """

    _environ: Mapping[str, str] = os.environ

    def __init__(
        self,
        *,
        color_system: Optional[
            Literal["auto", "standard", "256", "truecolor", "windows"]
        ] = "auto",
        force_terminal: Optional[bool] = None,
        force_jupyter: Optional[bool] = None,
        force_interactive: Optional[bool] = None,
        soft_wrap: bool = False,
        theme: Optional[Theme] = None,
        stderr: bool = False,
        file: Optional[IO[str]] = None,
        quiet: bool = False,
        width: Optional[int] = None,
        height: Optional[int] = None,
        style: Optional[StyleType] = None,
        no_color: Optional[bool] = None,
        tab_size: int = 8,
        record: bool = False,
        markup: bool = True,
        emoji: bool = True,
        emoji_variant: Optional[EmojiVariant] = None,
        highlight: bool = True,
        log_time: bool = True,
        log_path: bool = True,
        log_time_format: Union[str, FormatTimeCallable] = "[%X]",
        highlighter: Optional["HighlighterType"] = ReprHighlighter(),
        legacy_windows: Optional[bool] = None,
        safe_box: bool = True,
        get_datetime: Optional[Callable[[], datetime]] = None,
        get_time: Optional[Callable[[], float]] = None,
        _environ: Optional[Mapping[str, str]] = None,
    ):
        # Copy of os.environ allows us to replace it for testing
        if _environ is not None:
            self._environ = _environ

        self.is_jupyter = _is_jupyter() if force_jupyter is None else force_jupyter
        if self.is_jupyter:
            width = width or 93
            height = height or 100

        if width is None:
            columns = self._environ.get("COLUMNS")
            if columns is not None and columns.isdigit():
                width = int(columns)
        if height is None:
            lines = self._environ.get("LINES")
            if lines is not None and lines.isdigit():
                height = int(lines)

        self.soft_wrap = soft_wrap
        self._width = width
        self._height = height
        self.tab_size = tab_size
        self.record = record
        self._markup = markup
        self._emoji = emoji
        self._emoji_variant = emoji_variant
        self._highlight = highlight
        self.legacy_windows: bool = (
            (detect_legacy_windows() and not self.is_jupyter)
            if legacy_windows is None
            else legacy_windows
        )

        self._color_system: Optional[ColorSystem]
        self._force_terminal = force_terminal
        self._file = file
        self.quiet = quiet
        self.stderr = stderr

        if color_system is None:
            self._color_system = None
        elif color_system == "auto":
            self._color_system = self._detect_color_system()
        else:
            self._color_system = COLOR_SYSTEMS[color_system]

        self._lock = threading.RLock()
        self._log_render = LogRender(
            show_time=log_time,
            show_path=log_path,
            time_format=log_time_format,
        )
        self.highlighter: HighlighterType = highlighter or _null_highlighter
        self.safe_box = safe_box
        self.get_datetime = get_datetime or datetime.now
        self.get_time = get_time or monotonic
        self.style = style
        self.no_color = (
            no_color if no_color is not None else "NO_COLOR" in self._environ
        )
        self.is_interactive = (
            (self.is_terminal and not self.is_dumb_terminal)
            if force_interactive is None
            else force_interactive
        )

        self._record_buffer_lock = threading.RLock()
        self._thread_locals = ConsoleThreadLocals(
            theme_stack=ThemeStack(themes.DEFAULT if theme is None else theme)
        )
        self._record_buffer: List[Segment] = []
        self._render_hooks: List[RenderHook] = []
        self._live: Optional["Live"] = None
        self._is_alt_screen = False

    def __repr__(self) -> str:
        return f"<console width={self.width} {str(self._color_system)}>"

    @property
    def file(self) -> IO[str]:
        """Get the file object to write to."""
        file = self._file or (sys.stderr if self.stderr else sys.stdout)
        file = getattr(file, "rich_proxied_file", file)
        return file

    @file.setter
    def file(self, new_file: IO[str]) -> None:
        """Set a new file object."""
        self._file = new_file

    @property
    def _buffer(self) -> List[Segment]:
        """Get a thread local buffer."""
        return self._thread_locals.buffer

    @property
    def _buffer_index(self) -> int:
        """Get a thread local buffer."""
        return self._thread_locals.buffer_index

    @_buffer_index.setter
    def _buffer_index(self, value: int) -> None:
        self._thread_locals.buffer_index = value

    @property
    def _theme_stack(self) -> ThemeStack:
        """Get the thread local theme stack."""
        return self._thread_locals.theme_stack

    def _detect_color_system(self) -> Optional[ColorSystem]:
        """Detect color system from env vars."""
        if self.is_jupyter:
            return ColorSystem.TRUECOLOR
        if not self.is_terminal or self.is_dumb_terminal:
            return None
        if WINDOWS:  # pragma: no cover
            if self.legacy_windows:  # pragma: no cover
                return ColorSystem.WINDOWS
            windows_console_features = get_windows_console_features()
            return (
                ColorSystem.TRUECOLOR
                if windows_console_features.truecolor
                else ColorSystem.EIGHT_BIT
            )
        else:
            color_term = self._environ.get("COLORTERM", "").strip().lower()
            if color_term in ("truecolor", "24bit"):
                return ColorSystem.TRUECOLOR
            term = self._environ.get("TERM", "").strip().lower()
            _term_name, _hyphen, colors = term.partition("-")
            color_system = _TERM_COLORS.get(colors, ColorSystem.STANDARD)
            return color_system

    def _enter_buffer(self) -> None:
        """Enter in to a buffer context, and buffer all output."""
        self._buffer_index += 1

    def _exit_buffer(self) -> None:
        """Leave buffer context, and render content if required."""
        self._buffer_index -= 1
        self._check_buffer()

    def set_live(self, live: "Live") -> None:
        """Set Live instance. Used by Live context manager.

        Args:
            live (Live): Live instance using this Console.

        Raises:
            exceptions.LiveError: If this Console has a Live context currently active.
        """
        with self._lock:
            if self._live is not None:
                raise exceptions.LiveError("Only one live display may be active at once")
            self._live = live

    def clear_live(self) -> None:
        """Clear the Live instance."""
        with self._lock:
            self._live = None

    def push_render_hook(self, hook: RenderHook) -> None:
        """Add a new render hook to the stack.

        Args:
            hook (RenderHook): Render hook instance.
        """

        self._render_hooks.append(hook)

    def pop_render_hook(self) -> None:
        """Pop the last renderhook from the stack."""
        self._render_hooks.pop()

    def __enter__(self) -> "Console":
        """Own context manager to enter buffer context."""
        self._enter_buffer()
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        """Exit buffer context."""
        self._exit_buffer()

    def begin_capture(self) -> None:
        """Begin capturing console output. Call :meth:`end_capture` to exit capture mode and return output."""
        self._enter_buffer()

    def end_capture(self) -> str:
        """End capture mode and return captured string.

        Returns:
            str: Console output.
        """
        render_result = self._render_buffer(self._buffer)
        del self._buffer[:]
        self._exit_buffer()
        return render_result

    def push_theme(self, theme: Theme, *, inherit: bool = True) -> None:
        """Push a new theme on to the top of the stack, replacing the styles from the previous theme.
        Generally speaking, you should call :meth:`~rich.console.Console.use_theme` to get a context manager, rather
        than calling this method directly.

        Args:
            theme (Theme): A theme instance.
            inherit (bool, optional): Inherit existing styles. Defaults to True.
        """
        self._theme_stack.push_theme(theme, inherit=inherit)

    def pop_theme(self) -> None:
        """Remove theme from top of stack, restoring previous theme."""
        self._theme_stack.pop_theme()

    def use_theme(self, theme: Theme, *, inherit: bool = True) -> ThemeContext:
        """Use a different theme for the duration of the context manager.

        Args:
            theme (Theme): Theme instance to user.
            inherit (bool, optional): Inherit existing console styles. Defaults to True.

        Returns:
            ThemeContext: [description]
        """
        return ThemeContext(self, theme, inherit)

    @property
    def color_system(self) -> Optional[str]:
        """Get color system string.

        Returns:
            Optional[str]: "standard", "256" or "truecolor".
        """

        if self._color_system is not None:
            return _COLOR_SYSTEMS_NAMES[self._color_system]
        else:
            return None

    @property
    def encoding(self) -> str:
        """Get the encoding of the console file, e.g. ``"utf-8"``.

        Returns:
            str: A standard encoding string.
        """
        return (getattr(self.file, "encoding", "utf-8") or "utf-8").lower()

    @property
    def is_terminal(self) -> bool:
        """Check if the console is writing to a terminal.

        Returns:
            bool: True if the console writing to a device capable of
            understanding terminal codes, otherwise False.
        """
        if self._force_terminal is not None:
            return self._force_terminal
        isatty: Optional[Callable[[], bool]] = getattr(self.file, "isatty", None)
        return False if isatty is None else isatty()

    @property
    def is_dumb_terminal(self) -> bool:
        """Detect dumb terminal.

        Returns:
            bool: True if writing to a dumb terminal, otherwise False.

        """
        _term = self._environ.get("TERM", "")
        is_dumb = _term.lower() in ("dumb", "unknown")
        return self.is_terminal and is_dumb

    @property
    def options(self) -> ConsoleOptions:
        """Get default console options."""
        return ConsoleOptions(
            max_height=self.size.height,
            size=self.size,
            legacy_windows=self.legacy_windows,
            min_width=1,
            max_width=self.width,
            encoding=self.encoding,
            is_terminal=self.is_terminal,
        )

    @property
    def size(self) -> ConsoleDimensions:
        """Get the size of the console.

        Returns:
            ConsoleDimensions: A named tuple containing the dimensions.
        """

        if self._width is not None and self._height is not None:
            return ConsoleDimensions(self._width, self._height)

        if self.is_dumb_terminal:
            return ConsoleDimensions(80, 25)

        width: Optional[int] = None
        height: Optional[int] = None
        if WINDOWS:  # pragma: no cover
            width, height = shutil.get_terminal_size()
        else:
            try:
                width, height = os.get_terminal_size(sys.__stdin__.fileno())
            except (AttributeError, ValueError, OSError):
                try:
                    width, height = os.get_terminal_size(sys.__stdout__.fileno())
                except (AttributeError, ValueError, OSError):
                    pass

        # get_terminal_size can report 0, 0 if run from pseudo-terminal
        width = width or 80
        height = height or 25
        return ConsoleDimensions(
            (width - self.legacy_windows) if self._width is None else self._width,
            height if self._height is None else self._height,
        )

    @size.setter
    def size(self, new_size: Tuple[int, int]) -> None:
        """Set a new size for the terminal.

        Args:
            new_size (Tuple[int, int]): New width and height.
        """
        width, height = new_size
        self._width = width
        self._height = height

    @property
    def width(self) -> int:
        """Get the width of the console.

        Returns:
            int: The width (in characters) of the console.
        """
        return self.size.width

    @width.setter
    def width(self, width: int) -> None:
        """Set width.

        Args:
            width (int): New width.
        """
        self._width = width

    @property
    def height(self) -> int:
        """Get the height of the console.

        Returns:
            int: The height (in lines) of the console.
        """
        return self.size.height

    @height.setter
    def height(self, height: int) -> None:
        """Set height.

        Args:
            height (int): new height.
        """
        self._height = height

    def bell(self) -> None:
        """Play a 'bell' sound (if supported by the terminal)."""
        self.control(Control.bell())

    def capture(self) -> Capture:
        """A context manager to *capture* the result of print() or log() in a string,
        rather than writing it to the console.

        Example:
            >>> from rich.console import Console
            >>> console = Console()
            >>> with console.capture() as capture:
            ...     console.echo("[bold magenta]Hello World[/]")
            >>> echo(capture.get())

        Returns:
            Capture: Context manager with disables writing to the terminal.
        """
        capture = Capture(self)
        return capture

    def pager(
        self, pager: Optional[Pager] = None, styles: bool = False, links: bool = False
    ) -> PagerContext:
        """A context manager to display anything printed within a "pager". The pager application
        is defined by the system and will typically support at least pressing a key to scroll.

        Args:
            pager (Pager, optional): A pager object, or None to use :class:~rich.pager.SystemPager`. Defaults to None.
            styles (bool, optional): Show styles in pager. Defaults to False.
            links (bool, optional): Show links in pager. Defaults to False.

        Example:
            >>> from rich.console import Console
            >>> from rich.__main__ import make_test_card
            >>> console = Console()
            >>> with console.pager():
                    console.echo(make_test_card())

        Returns:
            PagerContext: A context manager.
        """
        return PagerContext(self, pager=pager, styles=styles, links=links)

    def line(self, count: int = 1) -> None:
        """Write new line(s).

        Args:
            count (int, optional): Number of new lines. Defaults to 1.
        """

        assert count >= 0, "count must be >= 0"
        self.echo(NewLine(count))

    def clear(self, home: bool = True) -> None:
        """Clear the screen.

        Args:
            home (bool, optional): Also move the cursor to 'home' position. Defaults to True.
        """
        if home:
            self.control(Control.clear(), Control.home())
        else:
            self.control(Control.clear())

    def status(
        self,
        status: RenderableType,
        *,
        spinner: str = "dots",
        spinner_style: str = "status.spinner",
        speed: float = 1.0,
        refresh_per_second: float = 12.5,
    ) -> "Status":
        """Display a status and spinner.

        Args:
            status (RenderableType): A status renderable (str or Text typically).
            spinner (str, optional): Name of spinner animation (see python -m rich.spinner). Defaults to "dots".
            spinner_style (StyleType, optional): Style of spinner. Defaults to "status.spinner".
            speed (float, optional): Speed factor for spinner animation. Defaults to 1.0.
            refresh_per_second (float, optional): Number of refreshes per second. Defaults to 12.5.

        Returns:
            Status: A Status object that may be used as a context manager.
        """
        from .status import Status

        status_renderable = Status(
            status,
            console=self,
            spinner=spinner,
            spinner_style=spinner_style,
            speed=speed,
            refresh_per_second=refresh_per_second,
        )
        return status_renderable

    def show_cursor(self, show: bool = True) -> bool:
        """Show or hide the cursor.

        Args:
            show (bool, optional): Set visibility of the cursor.
        """
        if self.is_terminal and not self.legacy_windows:
            self.control(Control.show_cursor(show))
            return True
        return False

    def set_alt_screen(self, enable: bool = True) -> bool:
        """Enables alternative screen mode.

        Note, if you enable this mode, you should ensure that is disabled before
        the application exits. See :meth:`~rich.Console.screen` for a context manager
        that handles this for you.

        Args:
            enable (bool, optional): Enable (True) or disable (False) alternate screen. Defaults to True.

        Returns:
            bool: True if the control codes were written.

        """
        changed = False
        if self.is_terminal and not self.legacy_windows:
            self.control(Control.alt_screen(enable))
            changed = True
            self._is_alt_screen = enable
        return changed

    @property
    def is_alt_screen(self) -> bool:
        """Check if the alt screen was enabled.

        Returns:
            bool: True if the alt screen was enabled, otherwise False.
        """
        return self._is_alt_screen

    def screen(
        self, hide_cursor: bool = True, style: Optional[StyleType] = None
    ) -> "ScreenContext":
        """Context manager to enable and disable 'alternative screen' mode.

        Args:
            hide_cursor (bool, optional): Also hide the cursor. Defaults to False.
            style (Style, optional): Optional style for screen. Defaults to None.

        Returns:
            ~ScreenContext: Context which enables alternate screen on enter, and disables it on exit.
        """
        return ScreenContext(self, hide_cursor=hide_cursor, style=style or "")

    def measure(
        self, renderable: RenderableType, *, options: Optional[ConsoleOptions] = None
    ) -> Measurement:
        """Measure a renderable. Returns a :class:`~rich.measure.Measurement` object which contains
        information regarding the number of characters required to print the renderable.

        Args:
            renderable (RenderableType): Any renderable or string.
            options (Optional[ConsoleOptions], optional): Options to use when measuring, or None
                to use default options. Defaults to None.

        Returns:
            Measurement: A measurement of the renderable.
        """
        measurement = Measurement.get(self, options or self.options, renderable)
        return measurement

    def render(
        self, renderable: RenderableType, options: Optional[ConsoleOptions] = None
    ) -> Iterable[Segment]:
        """Render an object in to an iterable of `Segment` instances.

        This method contains the logic for rendering objects with the console protocol.
        You are unlikely to need to use it directly, unless you are extending the library.

        Args:
            renderable (RenderableType): An object supporting the console protocol, or
                an object that may be converted to a string.
            options (ConsoleOptions, optional): An options object, or None to use self.options. Defaults to None.

        Returns:
            Iterable[Segment]: An iterable of segments that may be rendered.
        """

        _options = options or self.options
        if _options.max_width < 1:
            # No space to render anything. This prevents potential recursion errors.
            return
        render_iterable: RenderResult
        if hasattr(renderable, "__rich__") and not isclass(renderable):
            renderable = renderable.__rich__()  # type: ignore
        if hasattr(renderable, "__rich_console__") and not isclass(renderable):
            render_iterable = renderable.__rich_console__(self, _options)  # type: ignore
        elif isinstance(renderable, str):
            text_renderable = self.render_str(
                renderable, highlight=_options.highlight, markup=_options.markup
            )
            render_iterable = text_renderable.__rich_console__(self, _options)
        else:
            raise exceptions.NotRenderableError(
                f"Unable to render {renderable!r}; "
                "A str, Segment or object with __rich_console__ method is required"
            )

        try:
            iter_render = iter(render_iterable)
        except TypeError:
            raise exceptions.NotRenderableError(
                f"object {render_iterable!r} is not renderable"
            )
        _Segment = Segment
        for render_output in iter_render:
            if isinstance(render_output, _Segment):
                yield render_output
            else:
                yield from self.render(render_output, _options)

    def render_lines(
        self,
        renderable: RenderableType,
        options: Optional[ConsoleOptions] = None,
        *,
        style: Optional[Style] = None,
        pad: bool = True,
        new_lines: bool = False,
    ) -> List[List[Segment]]:
        """Render objects in to a list of lines.

        The output of render_lines is useful when further formatting of rendered console text
        is required, such as the Panel class which draws a border around any renderable object.

        Args:
            renderable (RenderableType): Any object renderable in the console.
            options (Optional[ConsoleOptions], optional): Console options, or None to use self.options. Default to ``None``.
            style (Style, optional): Optional style to apply to renderables. Defaults to ``None``.
            pad (bool, optional): Pad lines shorter than render width. Defaults to ``True``.
            new_lines (bool, optional): Include "\n" characters at end of lines.

        Returns:
            List[List[Segment]]: A list of lines, where a line is a list of Segment objects.
        """
        with self._lock:
            render_options = options or self.options
            _rendered = self.render(renderable, render_options)
            if style:
                _rendered = Segment.apply_style(_rendered, style)
            lines = list(
                islice(
                    Segment.split_and_crop_lines(
                        _rendered,
                        render_options.max_width,
                        include_new_lines=new_lines,
                        pad=pad,
                    ),
                    None,
                    render_options.height,
                )
            )
            if render_options.height is not None:
                extra_lines = render_options.height - len(lines)
                if extra_lines > 0:
                    pad_line = [
                        [Segment(" " * render_options.max_width, style), Segment("\n")]
                        if new_lines
                        else [Segment(" " * render_options.max_width, style)]
                    ]
                    lines.extend(pad_line * extra_lines)

            return lines

    def render_str(
        self,
        text: str,
        *,
        style: Union[str, Style] = "",
        justify: Optional[JustifyMethod] = None,
        overflow: Optional[OverflowMethod] = None,
        emoji: Optional[bool] = None,
        markup: Optional[bool] = None,
        highlight: Optional[bool] = None,
        highlighter: Optional[HighlighterType] = None,
    ) -> "Text":
        """Convert a string to a Text instance. This is is called automatically if
        you print or log a string.

        Args:
            text (str): Text to render.
            style (Union[str, Style], optional): Style to apply to rendered text.
            justify (str, optional): Justify method: "default", "left", "center", "full", or "right". Defaults to ``None``.
            overflow (str, optional): Overflow method: "crop", "fold", or "ellipsis". Defaults to ``None``.
            emoji (Optional[bool], optional): Enable emoji, or ``None`` to use Console default.
            markup (Optional[bool], optional): Enable markup, or ``None`` to use Console default.
            highlight (Optional[bool], optional): Enable highlighting, or ``None`` to use Console default.
            highlighter (HighlighterType, optional): Optional highlighter to apply.
        Returns:
            ConsoleRenderable: Renderable object.

        """
        emoji_enabled = emoji or (emoji is None and self._emoji)
        markup_enabled = markup or (markup is None and self._markup)
        highlight_enabled = highlight or (highlight is None and self._highlight)

        if markup_enabled:
            rich_text = render_markup(
                text,
                style=style,
                emoji=emoji_enabled,
                emoji_variant=self._emoji_variant,
            )
            rich_text.justify = justify
            rich_text.overflow = overflow
        else:
            rich_text = Text(
                _emoji_replace(text, default_variant=self._emoji_variant)
                if emoji_enabled
                else text,
                justify=justify,
                overflow=overflow,
                style=style,
            )

        _highlighter = (highlighter or self.highlighter) if highlight_enabled else None
        if _highlighter is not None:
            highlight_text = _highlighter(str(rich_text))
            highlight_text.copy_styles(rich_text)
            return highlight_text

        return rich_text

    def get_style(
        self, name: Union[str, Style], *, default: Optional[Union[Style, str]] = None
    ) -> Style:
        """Get a Style instance by it's theme name or parse a definition.

        Args:
            name (str): The name of a style or a style definition.

        Returns:
            Style: A Style object.

        Raises:
            MissingStyle: If no style could be parsed from name.

        """
        if isinstance(name, Style):
            return name

        try:
            style = self._theme_stack.get(name)
            if style is None:
                style = Style.parse(name)
            return style.copy() if style.link else style
        except exceptions.StyleSyntaxError as error:
            if default is not None:
                return self.get_style(default)
            raise exceptions.MissingStyle(
                f"Failed to get style {name!r}; {error}"
            ) from None

    def _collect_renderables(
        self,
        objects: Iterable[Any],
        sep: str,
        end: str,
        *,
        justify: Optional[JustifyMethod] = None,
        emoji: Optional[bool] = None,
        markup: Optional[bool] = None,
        highlight: Optional[bool] = None,
    ) -> List[ConsoleRenderable]:
        """Combine a number of renderables and text into one renderable.

        Args:
            objects (Iterable[Any]): Anything that Rich can render.
            sep (str): String to write between print data.
            end (str): String to write at end of print data.
            justify (str, optional): One of "left", "right", "center", or "full". Defaults to ``None``.
            emoji (Optional[bool], optional): Enable emoji code, or ``None`` to use console default.
            markup (Optional[bool], optional): Enable markup, or ``None`` to use console default.
            highlight (Optional[bool], optional): Enable automatic highlighting, or ``None`` to use console default.

        Returns:
            List[ConsoleRenderable]: A list of things to render.
        """
        renderables: List[ConsoleRenderable] = []
        _append = renderables.append
        text: List[Text] = []
        append_text = text.append

        append = _append
        if justify in ("left", "center", "right"):

            def align_append(renderable: RenderableType) -> None:
                _append(Align(renderable, cast(AlignMethod, justify)))

            append = align_append

        _highlighter: HighlighterType = _null_highlighter
        if highlight or (highlight is None and self._highlight):
            _highlighter = self.highlighter

        def check_text() -> None:
            if text:
                sep_text = Text(sep, justify=justify, end=end)
                append(sep_text.join(text))
                del text[:]

        for renderable in objects:
            # I promise this is sane
            # This detects an object which claims to have all attributes, such as MagicMock.mock_calls
            if hasattr(
                renderable, "jwevpw_eors4dfo6mwo345ermk7kdnfnwerwer"
            ):  # pragma: no cover
                renderable = repr(renderable)
            rich_cast = getattr(renderable, "__rich__", None)
            if rich_cast:
                renderable = rich_cast()
            if isinstance(renderable, str):
                append_text(
                    self.render_str(
                        renderable, emoji=emoji, markup=markup, highlighter=_highlighter
                    )
                )
            elif isinstance(renderable, ConsoleRenderable):
                check_text()
                append(renderable)
            elif is_expandable(renderable):
                check_text()
                append(Pretty(renderable, highlighter=_highlighter))
            else:
                append_text(_highlighter(str(renderable)))

        check_text()

        if self.style is not None:
            style = self.get_style(self.style)
            renderables = [Styled(renderable, style) for renderable in renderables]

        return renderables

    def rule(
        self,
        title: TextType = "",
        *,
        characters: str = "─",
        style: Union[str, Style] = "rule.line",
        align: AlignMethod = "center",
    ) -> None:
        """Draw a line with optional centered title.

        Args:
            title (str, optional): Text to render over the rule. Defaults to "".
            characters (str, optional): Character(s) to form the line. Defaults to "─".
            style (str, optional): Style of line. Defaults to "rule.line".
            align (str, optional): How to align the title, one of "left", "center", or "right". Defaults to "center".
        """
        from .rule import Rule

        rule = Rule(title=title, characters=characters, style=style, align=align)
        self.echo(rule)

    def control(self, *control: Control) -> None:
        """Insert non-printing control codes.

        Args:
            control_codes (str): Control codes, such as those that may move the cursor.
        """
        if not self.is_dumb_terminal:
            for _control in control:
                self._buffer.append(_control.segment)
            self._check_buffer()

    def out(
        self,
        *objects: Any,
        sep: str = " ",
        end: str = "\n",
        style: Optional[Union[str, Style]] = None,
        highlight: Optional[bool] = None,
    ) -> None:
        """Output to the terminal. This is a low-level way of writing to the terminal which unlike
        :meth:`~rich.console.Console.echo` won't pretty print, wrap text, or apply markup, but will
        optionally apply highlighting and a basic style.

        Args:
            sep (str, optional): String to write between print data. Defaults to " ".
            end (str, optional): String to write at end of print data. Defaults to "\\\\n".
            style (Union[str, Style], optional): A style to apply to output. Defaults to None.
            highlight (Optional[bool], optional): Enable automatic highlighting, or ``None`` to use
                console default. Defaults to ``None``.
        """
        raw_output: str = sep.join(str(_object) for _object in objects)
        self.echo(
            raw_output,
            style=style,
            highlight=highlight,
            emoji=False,
            markup=False,
            no_wrap=True,
            overflow="ignore",
            crop=False,
            end=end,
        )

    def echo(
        self,
        *objects: Any,
        sep: str = " ",
        end: str = "\n",
        style: Optional[Union[str, Style]] = None,
        justify: Optional[JustifyMethod] = None,
        overflow: Optional[OverflowMethod] = None,
        no_wrap: Optional[bool] = None,
        emoji: Optional[bool] = None,
        markup: Optional[bool] = None,
        highlight: Optional[bool] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        crop: bool = True,
        soft_wrap: Optional[bool] = None,
        new_line_start: bool = False,
    ) -> None:
        """Print to the console.

        Args:
            objects (positional args): Objects to log to the terminal.
            sep (str, optional): String to write between print data. Defaults to " ".
            end (str, optional): String to write at end of print data. Defaults to "\\\\n".
            style (Union[str, Style], optional): A style to apply to output. Defaults to None.
            justify (str, optional): Justify method: "default", "left", "right", "center", or "full". Defaults to ``None``.
            overflow (str, optional): Overflow method: "ignore", "crop", "fold", or "ellipsis". Defaults to None.
            no_wrap (Optional[bool], optional): Disable word wrapping. Defaults to None.
            emoji (Optional[bool], optional): Enable emoji code, or ``None`` to use console default. Defaults to ``None``.
            markup (Optional[bool], optional): Enable markup, or ``None`` to use console default. Defaults to ``None``.
            highlight (Optional[bool], optional): Enable automatic highlighting, or ``None`` to use console default. Defaults to ``None``.
            width (Optional[int], optional): Width of output, or ``None`` to auto-detect. Defaults to ``None``.
            crop (Optional[bool], optional): Crop output to width of terminal. Defaults to True.
            soft_wrap (bool, optional): Enable soft wrap mode which disables word wrapping and cropping of text or ``None`` for
                Console default. Defaults to ``None``.
            new_line_start (bool, False): Insert a new line at the start if the output contains more than one line. Defaults to ``False``.
        """
        if not objects:
            objects = (NewLine(),)

        if soft_wrap is None:
            soft_wrap = self.soft_wrap
        if soft_wrap:
            if no_wrap is None:
                no_wrap = True
            if overflow is None:
                overflow = "ignore"
            crop = False

        with self:
            renderables = self._collect_renderables(
                objects,
                sep,
                end,
                justify=justify,
                emoji=emoji,
                markup=markup,
                highlight=highlight,
            )
            for hook in self._render_hooks:
                renderables = hook.process_renderables(renderables)
            render_options = self.options.update(
                justify=justify,
                overflow=overflow,
                width=min(width, self.width) if width is not None else NO_CHANGE,
                height=height,
                no_wrap=no_wrap,
                markup=markup,
                highlight=highlight,
            )

            new_segments: List[Segment] = []
            extend = new_segments.extend
            render = self.render
            if style is None:
                for renderable in renderables:
                    extend(render(renderable, render_options))
            else:
                for renderable in renderables:
                    extend(
                        Segment.apply_style(
                            render(renderable, render_options), self.get_style(style)
                        )
                    )
            if new_line_start:
                if (
                    len("".join(segment.text for segment in new_segments).splitlines())
                    > 1
                ):
                    new_segments.insert(0, Segment.line())
            if crop:
                buffer_extend = self._buffer.extend
                for line in Segment.split_and_crop_lines(
                    new_segments, self.width, pad=False
                ):
                    buffer_extend(line)
            else:
                self._buffer.extend(new_segments)

    def print_json(
        self,
        json: Optional[str] = None,
        *,
        data: Any = None,
        indent: int = 2,
        highlight: bool = True,
    ) -> None:
        """Pretty prints JSON. Output will be valid JSON.

        Args:
            json (Optional[str]): A string containing JSON.
            data (Any): If json is not supplied, then encode this data.
            indent (int, optional): Number of spaces to indent. Defaults to 2.
            highlight (bool, optional): Enable highlighting of output: Defaults to True.
        """
        from rich.json import JSON

        if json is None:
            json_renderable = JSON.from_data(data, indent=indent, highlight=highlight)
        else:
            if not isinstance(json, str):
                raise TypeError(
                    f"json must be str. Did you mean print_json(data={json!r}) ?"
                )
            json_renderable = JSON(json, indent=indent, highlight=highlight)
        self.echo(json_renderable)

    def update_screen(
        self,
        renderable: RenderableType,
        *,
        region: Optional[Region] = None,
        options: Optional[ConsoleOptions] = None,
    ) -> None:
        """Update the screen at a given offset.

        Args:
            renderable (RenderableType): A Rich renderable.
            region (Region, optional): Region of screen to update, or None for entire screen. Defaults to None.
            x (int, optional): x offset. Defaults to 0.
            y (int, optional): y offset. Defaults to 0.

        Raises:
            exceptions.NoAltScreen: If the Console isn't in alt screen mode.

        """
        if not self.is_alt_screen:
            raise exceptions.NoAltScreen("Alt screen must be enabled to call update_screen")
        render_options = options or self.options
        if region is None:
            x = y = 0
            render_options = render_options.update_dimensions(
                render_options.max_width, render_options.height or self.height
            )
        else:
            x, y, width, height = region
            render_options = render_options.update_dimensions(width, height)

        lines = self.render_lines(renderable, options=render_options)
        self.update_screen_lines(lines, x, y)

    def update_screen_lines(
        self, lines: List[List[Segment]], x: int = 0, y: int = 0
    ) -> None:
        """Update lines of the screen at a given offset.

        Args:
            lines (List[List[Segment]]): Rendered lines (as produced by :meth:`~rich.Console.render_lines`).
            x (int, optional): x offset (column no). Defaults to 0.
            y (int, optional): y offset (column no). Defaults to 0.

        Raises:
            exceptions.NoAltScreen: If the Console isn't in alt screen mode.
        """
        if not self.is_alt_screen:
            raise exceptions.NoAltScreen("Alt screen must be enabled to call update_screen")
        screen_update = ScreenUpdate(lines, x, y)
        segments = self.render(screen_update)
        self._buffer.extend(segments)
        self._check_buffer()

    def print_exception(
        self,
        *,
        width: Optional[int] = 100,
        extra_lines: int = 3,
        theme: Optional[str] = None,
        word_wrap: bool = False,
        show_locals: bool = False,
        suppress: Iterable[Union[str, ModuleType]] = (),
        max_frames: int = 100,
    ) -> None:
        """Prints a rich render of the last exception and traceback.

        Args:
            width (Optional[int], optional): Number of characters used to render code. Defaults to 88.
            extra_lines (int, optional): Additional lines of code to render. Defaults to 3.
            theme (str, optional): Override pygments theme used in traceback
            word_wrap (bool, optional): Enable word wrapping of long lines. Defaults to False.
            show_locals (bool, optional): Enable display of local variables. Defaults to False.
            suppress (Iterable[Union[str, ModuleType]]): Optional sequence of modules or paths to exclude from traceback.
            max_frames (int): Maximum number of frames to show in a traceback, 0 for no maximum. Defaults to 100.
        """
        from .traceback import Traceback

        traceback = Traceback(
            width=width,
            extra_lines=extra_lines,
            theme=theme,
            word_wrap=word_wrap,
            show_locals=show_locals,
            suppress=suppress,
            max_frames=max_frames,
        )
        self.echo(traceback)

    @staticmethod
    def _caller_frame_info(
        offset: int,
        currentframe: Callable[[], Optional[FrameType]] = inspect.currentframe,
    ) -> Tuple[str, int, Dict[str, Any]]:
        """Get caller frame information.

        Args:
            offset (int): the caller offset within the current frame stack.
            currentframe (Callable[[], Optional[FrameType]], optional): the callable to use to
                retrieve the current frame. Defaults to ``inspect.currentframe``.

        Returns:
            Tuple[str, int, Dict[str, Any]]: A tuple containing the filename, the line number and
                the dictionary of local variables associated with the caller frame.

        Raises:
            RuntimeError: If the stack offset is invalid.
        """
        # Ignore the frame of this local helper
        offset += 1

        frame = currentframe()
        if frame is not None:
            # Use the faster currentframe where implemented
            while offset and frame:
                frame = frame.f_back
                offset -= 1
            assert frame is not None
            return frame.f_code.co_filename, frame.f_lineno, frame.f_locals
        else:
            # Fallback to the slower stack
            frame_info = inspect.stack()[offset]
            return frame_info.filename, frame_info.lineno, frame_info.frame.f_locals

    def log(
        self,
        *objects: Any,
        sep: str = " ",
        end: str = "\n",
        style: Optional[Union[str, Style]] = None,
        justify: Optional[JustifyMethod] = None,
        emoji: Optional[bool] = None,
        markup: Optional[bool] = None,
        highlight: Optional[bool] = None,
        log_locals: bool = False,
        _stack_offset: int = 1,
    ) -> None:
        """Log rich content to the terminal.

        Args:
            objects (positional args): Objects to log to the terminal.
            sep (str, optional): String to write between print data. Defaults to " ".
            end (str, optional): String to write at end of print data. Defaults to "\\\\n".
            style (Union[str, Style], optional): A style to apply to output. Defaults to None.
            justify (str, optional): One of "left", "right", "center", or "full". Defaults to ``None``.
            overflow (str, optional): Overflow method: "crop", "fold", or "ellipsis". Defaults to None.
            emoji (Optional[bool], optional): Enable emoji code, or ``None`` to use console default. Defaults to None.
            markup (Optional[bool], optional): Enable markup, or ``None`` to use console default. Defaults to None.
            highlight (Optional[bool], optional): Enable automatic highlighting, or ``None`` to use console default. Defaults to None.
            log_locals (bool, optional): Boolean to enable logging of locals where ``log()``
                was called. Defaults to False.
            _stack_offset (int, optional): Offset of caller from end of call stack. Defaults to 1.
        """
        if not objects:
            objects = (NewLine(),)

        with self:
            renderables = self._collect_renderables(
                objects,
                sep,
                end,
                justify=justify,
                emoji=emoji,
                markup=markup,
                highlight=highlight,
            )
            if style is not None:
                renderables = [Styled(renderable, style) for renderable in renderables]

            filename, line_no, locals = self._caller_frame_info(_stack_offset)
            link_path = None if filename.startswith("<") else os.path.abspath(filename)
            path = filename.rpartition(os.sep)[-1]
            if log_locals:
                locals_map = {
                    key: value
                    for key, value in locals.items()
                    if not key.startswith("__")
                }
                renderables.append(render_scope(locals_map, title="[i]locals"))

            renderables = [
                self._log_render(
                    self,
                    renderables,
                    log_time=self.get_datetime(),
                    path=path,
                    line_no=line_no,
                    link_path=link_path,
                )
            ]
            for hook in self._render_hooks:
                renderables = hook.process_renderables(renderables)
            new_segments: List[Segment] = []
            extend = new_segments.extend
            render = self.render
            render_options = self.options
            for renderable in renderables:
                extend(render(renderable, render_options))
            buffer_extend = self._buffer.extend
            for line in Segment.split_and_crop_lines(
                new_segments, self.width, pad=False
            ):
                buffer_extend(line)

    def _check_buffer(self) -> None:
        """Check if the buffer may be rendered."""
        if self.quiet:
            del self._buffer[:]
            return
        with self._lock:
            if self._buffer_index == 0:
                if self.is_jupyter:  # pragma: no cover
                    from .jupyter import display

                    display(self._buffer, self._render_buffer(self._buffer[:]))
                    del self._buffer[:]
                else:
                    text = self._render_buffer(self._buffer[:])
                    del self._buffer[:]
                    if text:
                        try:
                            if WINDOWS:  # pragma: no cover
                                # https://bugs.python.org/issue37871
                                write = self.file.write
                                for line in text.splitlines(True):
                                    write(line)
                            else:
                                self.file.write(text)
                            self.file.flush()
                        except UnicodeEncodeError as error:
                            error.reason = f"{error.reason}\n*** You may need to add PYTHONIOENCODING=utf-8 to your environment ***"
                            raise

    def _render_buffer(self, buffer: Iterable[Segment]) -> str:
        """Render buffered output, and clear buffer."""
        output: List[str] = []
        append = output.append
        color_system = self._color_system
        legacy_windows = self.legacy_windows
        if self.record:
            with self._record_buffer_lock:
                self._record_buffer.extend(buffer)
        not_terminal = not self.is_terminal
        if self.no_color and color_system:
            buffer = Segment.remove_color(buffer)
        for text, style, control in buffer:
            if style:
                append(
                    style.render(
                        text,
                        color_system=color_system,
                        legacy_windows=legacy_windows,
                    )
                )
            elif not (not_terminal and control):
                append(text)

        rendered = "".join(output)
        return rendered

    def input(
        self,
        prompt: TextType = "",
        *,
        markup: bool = True,
        emoji: bool = True,
        password: bool = False,
        stream: Optional[TextIO] = None,
    ) -> str:
        """Displays a prompt and waits for input from the user. The prompt may contain color / style.

        Args:
            prompt (Union[str, Text]): Text to render in the prompt.
            markup (bool, optional): Enable console markup (requires a str prompt). Defaults to True.
            emoji (bool, optional): Enable emoji (requires a str prompt). Defaults to True.
            password: (bool, optional): Hide typed text. Defaults to False.
            stream: (TextIO, optional): Optional file to read input from (rather than stdin). Defaults to None.

        Returns:
            str: Text read from stdin.
        """
        prompt_str = ""
        if prompt:
            with self.capture() as capture:
                self.echo(prompt, markup=markup, emoji=emoji, end="")
            prompt_str = capture.get()
        if self.legacy_windows:
            # Legacy windows doesn't like ANSI codes in getpass or input (colorama bug)?
            self.file.write(prompt_str)
            prompt_str = ""
        if password:
            result = getpass(prompt_str, stream=stream)
        else:
            if stream:
                self.file.write(prompt_str)
                result = stream.readline()
            else:
                result = input(prompt_str)
        return result

    def export_text(self, *, clear: bool = True, styles: bool = False) -> str:
        """Generate text from console contents (requires record=True argument in constructor).

        Args:
            clear (bool, optional): Clear record buffer after exporting. Defaults to ``True``.
            styles (bool, optional): If ``True``, ansi escape codes will be included. ``False`` for plain text.
                Defaults to ``False``.

        Returns:
            str: String containing console contents.

        """
        assert (
            self.record
        ), "To export console contents set record=True in the constructor or instance"

        with self._record_buffer_lock:
            if styles:
                text = "".join(
                    (style.render(text) if style else text)
                    for text, style, _ in self._record_buffer
                )
            else:
                text = "".join(
                    segment.text
                    for segment in self._record_buffer
                    if not segment.control
                )
            if clear:
                del self._record_buffer[:]
        return text

    def save_text(self, path: str, *, clear: bool = True, styles: bool = False) -> None:
        """Generate text from console and save to a given location (requires record=True argument in constructor).

        Args:
            path (str): Path to write text files.
            clear (bool, optional): Clear record buffer after exporting. Defaults to ``True``.
            styles (bool, optional): If ``True``, ansi style codes will be included. ``False`` for plain text.
                Defaults to ``False``.

        """
        text = self.export_text(clear=clear, styles=styles)
        with open(path, "wt", encoding="utf-8") as write_file:
            write_file.write(text)

    def export_html(
        self,
        *,
        theme: Optional[TerminalTheme] = None,
        clear: bool = True,
        code_format: Optional[str] = None,
        inline_styles: bool = False,
    ) -> str:
        """Generate HTML from console contents (requires record=True argument in constructor).

        Args:
            theme (TerminalTheme, optional): TerminalTheme object containing console colors.
            clear (bool, optional): Clear record buffer after exporting. Defaults to ``True``.
            code_format (str, optional): Format string to render HTML, should contain {foreground}
                {background} and {code}.
            inline_styles (bool, optional): If ``True`` styles will be inlined in to spans, which makes files
                larger but easier to cut and paste markup. If ``False``, styles will be embedded in a style tag.
                Defaults to False.

        Returns:
            str: String containing console contents as HTML.
        """
        assert (
            self.record
        ), "To export console contents set record=True in the constructor or instance"
        fragments: List[str] = []
        append = fragments.append
        _theme = theme or DEFAULT_TERMINAL_THEME
        stylesheet = ""

        render_code_format = CONSOLE_HTML_FORMAT if code_format is None else code_format

        with self._record_buffer_lock:
            if inline_styles:
                for text, style, _ in Segment.filter_control(
                    Segment.simplify(self._record_buffer)
                ):
                    text = escape(text)
                    if style:
                        rule = style.get_html_style(_theme)
                        if style.link:
                            text = f'<a href="{style.link}">{text}</a>'
                        text = f'<span style="{rule}">{text}</span>' if rule else text
                    append(text)
            else:
                styles: Dict[str, int] = {}
                for text, style, _ in Segment.filter_control(
                    Segment.simplify(self._record_buffer)
                ):
                    text = escape(text)
                    if style:
                        rule = style.get_html_style(_theme)
                        style_number = styles.setdefault(rule, len(styles) + 1)
                        if style.link:
                            text = f'<a class="r{style_number}" href="{style.link}">{text}</a>'
                        else:
                            text = f'<span class="r{style_number}">{text}</span>'
                    append(text)
                stylesheet_rules: List[str] = []
                stylesheet_append = stylesheet_rules.append
                for style_rule, style_number in styles.items():
                    if style_rule:
                        stylesheet_append(f".r{style_number} {{{style_rule}}}")
                stylesheet = "\n".join(stylesheet_rules)

            rendered_code = render_code_format.format(
                code="".join(fragments),
                stylesheet=stylesheet,
                foreground=_theme.foreground_color.hex,
                background=_theme.background_color.hex,
            )
            if clear:
                del self._record_buffer[:]
        return rendered_code

    def save_html(
        self,
        path: str,
        *,
        theme: Optional[TerminalTheme] = None,
        clear: bool = True,
        code_format: str = CONSOLE_HTML_FORMAT,
        inline_styles: bool = False,
    ) -> None:
        """Generate HTML from console contents and write to a file (requires record=True argument in constructor).

        Args:
            path (str): Path to write html file.
            theme (TerminalTheme, optional): TerminalTheme object containing console colors.
            clear (bool, optional): Clear record buffer after exporting. Defaults to ``True``.
            code_format (str, optional): Format string to render HTML, should contain {foreground}
                {background} and {code}.
            inline_styles (bool, optional): If ``True`` styles will be inlined in to spans, which makes files
                larger but easier to cut and paste markup. If ``False``, styles will be embedded in a style tag.
                Defaults to False.

        """
        html = self.export_html(
            theme=theme,
            clear=clear,
            code_format=code_format,
            inline_styles=inline_styles,
        )
        with open(path, "wt", encoding="utf-8") as write_file:
            write_file.write(html)


if __name__ == "__main__":  # pragma: no cover
    console = Console()

    console.log(
        "JSONRPC [i]request[/i]",
        5,
        1.3,
        True,
        False,
        None,
        {
            "jsonrpc": "2.0",
            "method": "subtract",
            "params": {"minuend": 42, "subtrahend": 23},
            "id": 3,
        },
    )

    console.log("Hello, World!", "{'a': 1}", repr(console))

    console.echo(
        {
            "name": None,
            "empty": [],
            "quiz": {
                "sport": {
                    "answered": True,
                    "q1": {
                        "question": "Which one is correct team name in NBA?",
                        "options": [
                            "New York Bulls",
                            "Los Angeles Kings",
                            "Golden State Warriors",
                            "Huston Rocket",
                        ],
                        "answer": "Huston Rocket",
                    },
                },
                "maths": {
                    "answered": False,
                    "q1": {
                        "question": "5 + 7 = ?",
                        "options": [10, 11, 12, 13],
                        "answer": 12,
                    },
                    "q2": {
                        "question": "12 - 8 = ?",
                        "options": [1, 2, 3, 4],
                        "answer": 4,
                    },
                },
            },
        }
    )
    console.log("foo")


# *****'''''*************

def _get_console() -> "Console":
    """Get a global :class:`~quo.console.Console` instance. This function is used when Quo requires a Console,
    and hasn't been explicitly given one.

    Returns:
        Console: A console instance.
    """
    global _console
    if _console is None:

        _console = Console()

    return _console

def _is_attr_object(obj: Any) -> bool:
    """Check if an object was created with attrs module."""
    return _attr_module is not None and _attr_module.has(type(obj))


def _get_attr_fields(obj: Any) -> Iterable["_attr_module.Attribute[Any]"]:
    """Get fields for an attrs object."""
    return _attr_module.fields(type(obj)) if _attr_module is not None else []


def _is_dataclass_repr(obj: object) -> bool:
    """Check if an instance of a dataclass contains the default repr.

    Args:
        obj (object): A dataclass instance.

    Returns:
        bool: True if the default repr is used, False if there is a custom repr.
    """
    # Digging in to a lot of internals here
    # Catching all exceptions in case something is missing on a non CPython implementation
    try:
        return obj.__repr__.__code__.co_filename == dataclasses.__file__
    except Exception:
        return False


def install(
    console: Optional["Console"] = None,
    overflow: "OverflowMethod" = "ignore",
    crop: bool = False,
    indent_guides: bool = False,
    max_length: Optional[int] = None,
    max_string: Optional[int] = None,
    expand_all: bool = False,
) -> None:
    """Install automatic pretty printing in the Python REPL.

    Args:
        console (Console, optional): Console instance or ``None`` to use global console. Defaults to None.
        overflow (Optional[OverflowMethod], optional): Overflow method. Defaults to "ignore".
        crop (Optional[bool], optional): Enable cropping of long lines. Defaults to False.
        indent_guides (bool, optional): Enable indentation guides. Defaults to False.
        max_length (int, optional): Maximum length of containers before abbreviating, or None for no abbreviation.
            Defaults to None.
        max_string (int, optional): Maximum length of string before truncating, or None to disable. Defaults to None.
        expand_all (bool, optional): Expand all containers. Defaults to False.
        max_frames (int): Maximum number of frames to show in a traceback, 0 for no maximum. Defaults to 100.
    """
    from rich import get_console

    from .console import ConsoleRenderable  # needed here to prevent circular import

    console = console or get_console()
    assert console is not None

    def display_hook(value: Any) -> None:
        """Replacement sys.displayhook which prettifies objects with Rich."""
        if value is not None:
            assert console is not None
            builtins._ = None  # type: ignore
            console.print(
                value
                if isinstance(value, RichRenderable)
                else Pretty(
                    value,
                    overflow=overflow,
                    indent_guides=indent_guides,
                    max_length=max_length,
                    max_string=max_string,
                    expand_all=expand_all,
                ),
                crop=crop,
            )
            builtins._ = value  # type: ignore

    def ipy_display_hook(value: Any) -> None:  # pragma: no cover
        assert console is not None
        # always skip rich generated jupyter renderables or None values
        if isinstance(value, JupyterRenderable) or value is None:
            return
        # on jupyter rich display, if using one of the special representations don't use rich
        if console.is_jupyter and any(
            _re_jupyter_repr.match(attr) for attr in dir(value)
        ):
            return

        # certain renderables should start on a new line
        if isinstance(value, ConsoleRenderable):
            console.line()

        console.print(
            value
            if isinstance(value, RichRenderable)
            else Pretty(
                value,
                overflow=overflow,
                indent_guides=indent_guides,
                max_length=max_length,
                max_string=max_string,
                expand_all=expand_all,
                margin=12,
            ),
            crop=crop,
            new_line_start=True,
        )

    try:  # pragma: no cover
        ip = get_ipython()  # type: ignore
        from IPython.core.formatters import BaseFormatter

        # replace plain text formatter with rich formatter
        rich_formatter = BaseFormatter()
        rich_formatter.for_type(object, func=ipy_display_hook)
        ip.display_formatter.formatters["text/plain"] = rich_formatter
    except Exception:
        sys.displayhook = display_hook


class Pretty(JupyterMixin):
    """A rich renderable that pretty prints an object.

    Args:
        _object (Any): An object to pretty print.
        highlighter (HighlighterType, optional): Highlighter object to apply to result, or None for ReprHighlighter. Defaults to None.
        indent_size (int, optional): Number of spaces in indent. Defaults to 4.
        justify (JustifyMethod, optional): Justify method, or None for default. Defaults to None.
        overflow (OverflowMethod, optional): Overflow method, or None for default. Defaults to None.
        no_wrap (Optional[bool], optional): Disable word wrapping. Defaults to False.
        indent_guides (bool, optional): Enable indentation guides. Defaults to False.
        max_length (int, optional): Maximum length of containers before abbreviating, or None for no abbreviation.
            Defaults to None.
        max_string (int, optional): Maximum length of string before truncating, or None to disable. Defaults to None.
        expand_all (bool, optional): Expand all containers. Defaults to False.
        margin (int, optional): Subtrace a margin from width to force containers to expand earlier. Defaults to 0.
        insert_line (bool, optional): Insert a new line if the output has multiple new lines. Defaults to False.
    """

    def __init__(
        self,
        _object: Any,
        highlighter: Optional["HighlighterType"] = None,
        *,
        indent_size: int = 4,
        justify: Optional["JustifyMethod"] = None,
        overflow: Optional["OverflowMethod"] = None,
        no_wrap: Optional[bool] = False,
        indent_guides: bool = False,
        max_length: Optional[int] = None,
        max_string: Optional[int] = None,
        expand_all: bool = False,
        margin: int = 0,
        insert_line: bool = False,
    ) -> None:
        self._object = _object
        self.highlighter = highlighter or ReprHighlighter()
        self.indent_size = indent_size
        self.justify = justify
        self.overflow = overflow
        self.no_wrap = no_wrap
        self.indent_guides = indent_guides
        self.max_length = max_length
        self.max_string = max_string
        self.expand_all = expand_all
        self.margin = margin
        self.insert_line = insert_line

    def __rich_console__(
        self, console: "Console", options: "ConsoleOptions"
    ) -> "RenderResult":
        pretty_str = pretty_repr(
            self._object,
            max_width=options.max_width - self.margin,
            indent_size=self.indent_size,
            max_length=self.max_length,
            max_string=self.max_string,
            expand_all=self.expand_all,
        )
        pretty_text = Text(
            pretty_str,
            justify=self.justify or options.justify,
            overflow=self.overflow or options.overflow,
            no_wrap=pick_bool(self.no_wrap, options.no_wrap),
            style="pretty",
        )
        pretty_text = (
            self.highlighter(pretty_text)
            if pretty_text
            else Text(
                f"{type(self._object)}.__repr__ returned empty string",
                style="dim italic",
            )
        )
        if self.indent_guides and not options.ascii_only:
            pretty_text = pretty_text.with_indent_guides(
                self.indent_size, style="repr.indent"
            )
        if self.insert_line and "\n" in pretty_text:
            yield ""
        yield pretty_text

    def __rich_measure__(
        self, console: "Console", options: "ConsoleOptions"
    ) -> "Measurement":
        pretty_str = pretty_repr(
            self._object,
            max_width=options.max_width,
            indent_size=self.indent_size,
            max_length=self.max_length,
            max_string=self.max_string,
        )
        text_width = (
            max(cell_len(line) for line in pretty_str.splitlines()) if pretty_str else 0
        )
        return Measurement(text_width, text_width)


def _get_braces_for_defaultdict(_object: DefaultDict[Any, Any]) -> Tuple[str, str, str]:
    return (
        f"defaultdict({_object.default_factory!r}, {{",
        "})",
        f"defaultdict({_object.default_factory!r}, {{}})",
    )


def _get_braces_for_array(_object: "array[Any]") -> Tuple[str, str, str]:
    return (f"array({_object.typecode!r}, [", "])", "array({_object.typecode!r})")


_BRACES: Dict[type, Callable[[Any], Tuple[str, str, str]]] = {
    os._Environ: lambda _object: ("environ({", "})", "environ({})"),
    array: _get_braces_for_array,
    defaultdict: _get_braces_for_defaultdict,
    Counter: lambda _object: ("Counter({", "})", "Counter()"),
    deque: lambda _object: ("deque([", "])", "deque()"),
    dict: lambda _object: ("{", "}", "{}"),
    UserDict: lambda _object: ("{", "}", "{}"),
    frozenset: lambda _object: ("frozenset({", "})", "frozenset()"),
    list: lambda _object: ("[", "]", "[]"),
    UserList: lambda _object: ("[", "]", "[]"),
    set: lambda _object: ("{", "}", "set()"),
    tuple: lambda _object: ("(", ")", "()"),
    MappingProxyType: lambda _object: ("mappingproxy({", "})", "mappingproxy({})"),
}
_CONTAINERS = tuple(_BRACES.keys())
_MAPPING_CONTAINERS = (dict, os._Environ, MappingProxyType, UserDict)


def is_expandable(obj: Any) -> bool:
    """Check if an object may be expanded by pretty print."""
    return (
        isinstance(obj, _CONTAINERS)
        or (is_dataclass(obj))
        or (hasattr(obj, "__rich_repr__"))
        or _is_attr_object(obj)
    ) and not isclass(obj)


@dataclass
class Node:
    """A node in a repr tree. May be atomic or a container."""

    key_repr: str = ""
    value_repr: str = ""
    open_brace: str = ""
    close_brace: str = ""
    empty: str = ""
    last: bool = False
    is_tuple: bool = False
    children: Optional[List["Node"]] = None
    key_separator = ": "
    separator: str = ", "

    def iter_tokens(self) -> Iterable[str]:
        """Generate tokens for this node."""
        if self.key_repr:
            yield self.key_repr
            yield self.key_separator
        if self.value_repr:
            yield self.value_repr
        elif self.children is not None:
            if self.children:
                yield self.open_brace
                if self.is_tuple and len(self.children) == 1:
                    yield from self.children[0].iter_tokens()
                    yield ","
                else:
                    for child in self.children:
                        yield from child.iter_tokens()
                        if not child.last:
                            yield self.separator
                yield self.close_brace
            else:
                yield self.empty

    def check_length(self, start_length: int, max_length: int) -> bool:
        """Check the length fits within a limit.

        Args:
            start_length (int): Starting length of the line (indent, prefix, suffix).
            max_length (int): Maximum length.

        Returns:
            bool: True if the node can be rendered within max length, otherwise False.
        """
        total_length = start_length
        for token in self.iter_tokens():
            total_length += cell_len(token)
            if total_length > max_length:
                return False
        return True

    def __str__(self) -> str:
        repr_text = "".join(self.iter_tokens())
        return repr_text

    def render(
        self, max_width: int = 80, indent_size: int = 4, expand_all: bool = False
    ) -> str:
        """Render the node to a pretty repr.

        Args:
            max_width (int, optional): Maximum width of the repr. Defaults to 80.
            indent_size (int, optional): Size of indents. Defaults to 4.
            expand_all (bool, optional): Expand all levels. Defaults to False.

        Returns:
            str: A repr string of the original object.
        """
        lines = [_Line(node=self, is_root=True)]
        line_no = 0
        while line_no < len(lines):
            line = lines[line_no]
            if line.expandable and not line.expanded:
                if expand_all or not line.check_length(max_width):
                    lines[line_no : line_no + 1] = line.expand(indent_size)
            line_no += 1

        repr_str = "\n".join(str(line) for line in lines)
        return repr_str


@dataclass
class _Line:
    """A line in repr output."""

    parent: Optional["_Line"] = None
    is_root: bool = False
    node: Optional[Node] = None
    text: str = ""
    suffix: str = ""
    whitespace: str = ""
    expanded: bool = False
    last: bool = False

    @property
    def expandable(self) -> bool:
        """Check if the line may be expanded."""
        return bool(self.node is not None and self.node.children)

    def check_length(self, max_length: int) -> bool:
        """Check this line fits within a given number of cells."""
        start_length = (
            len(self.whitespace) + cell_len(self.text) + cell_len(self.suffix)
        )
        assert self.node is not None
        return self.node.check_length(start_length, max_length)

    def expand(self, indent_size: int) -> Iterable["_Line"]:
        """Expand this line by adding children on their own line."""
        node = self.node
        assert node is not None
        whitespace = self.whitespace
        assert node.children
        if node.key_repr:
            new_line = yield _Line(
                text=f"{node.key_repr}{node.key_separator}{node.open_brace}",
                whitespace=whitespace,
            )
        else:
            new_line = yield _Line(text=node.open_brace, whitespace=whitespace)
        child_whitespace = self.whitespace + " " * indent_size
        tuple_of_one = node.is_tuple and len(node.children) == 1
        for last, child in loop_last(node.children):
            separator = "," if tuple_of_one else node.separator
            line = _Line(
                parent=new_line,
                node=child,
                whitespace=child_whitespace,
                suffix=separator,
                last=last and not tuple_of_one,
            )
            yield line

        yield _Line(
            text=node.close_brace,
            whitespace=whitespace,
            suffix=self.suffix,
            last=self.last,
        )

    def __str__(self) -> str:
        if self.last:
            return f"{self.whitespace}{self.text}{self.node or ''}"
        else:
            return (
                f"{self.whitespace}{self.text}{self.node or ''}{self.suffix.rstrip()}"
            )


def traverse(
    _object: Any, max_length: Optional[int] = None, max_string: Optional[int] = None
) -> Node:
    """Traverse object and generate a tree.

    Args:
        _object (Any): Object to be traversed.
        max_length (int, optional): Maximum length of containers before abbreviating, or None for no abbreviation.
            Defaults to None.
        max_string (int, optional): Maximum length of string before truncating, or None to disable truncating.
            Defaults to None.

    Returns:
        Node: The root of a tree structure which can be used to render a pretty repr.
    """

    def to_repr(obj: Any) -> str:
        """Get repr string for an object, but catch errors."""
        if (
            max_string is not None
            and isinstance(obj, (bytes, str))
            and len(obj) > max_string
        ):
            truncated = len(obj) - max_string
            obj_repr = f"{obj[:max_string]!r}+{truncated}"
        else:
            try:
                obj_repr = repr(obj)
            except Exception as error:
                obj_repr = f"<repr-error {str(error)!r}>"
        return obj_repr

    visited_ids: Set[int] = set()
    push_visited = visited_ids.add
    pop_visited = visited_ids.remove

    def _traverse(obj: Any, root: bool = False) -> Node:
        """Walk the object depth first."""
        obj_type = type(obj)
        py_version = (sys.version_info.major, sys.version_info.minor)
        children: List[Node]

        def iter_rich_args(rich_args: Any) -> Iterable[Union[Any, Tuple[str, Any]]]:
            for arg in rich_args:
                if isinstance(arg, tuple):
                    if len(arg) == 3:
                        key, child, default = arg
                        if default == child:
                            continue
                        yield key, child
                    elif len(arg) == 2:
                        key, child = arg
                        yield key, child
                    elif len(arg) == 1:
                        yield arg[0]
                else:
                    yield arg

        try:
            fake_attributes = hasattr(
                obj, "awehoi234_wdfjwljet234_234wdfoijsdfmmnxpi492"
            )
        except Exception:
            fake_attributes = False

        rich_repr_result: Optional[RichReprResult] = None
        if not fake_attributes:
            try:
                if hasattr(obj, "__rich_repr__") and not isclass(obj):
                    rich_repr_result = obj.__rich_repr__()
            except Exception:
                pass

        if rich_repr_result is not None:
            angular = getattr(obj.__rich_repr__, "angular", False)
            args = list(iter_rich_args(rich_repr_result))
            class_name = obj.__class__.__name__

            if args:
                children = []
                append = children.append
                if angular:
                    node = Node(
                        open_brace=f"<{class_name} ",
                        close_brace=">",
                        children=children,
                        last=root,
                        separator=" ",
                    )
                else:
                    node = Node(
                        open_brace=f"{class_name}(",
                        close_brace=")",
                        children=children,
                        last=root,
                    )
                for last, arg in loop_last(args):
                    if isinstance(arg, tuple):
                        key, child = arg
                        child_node = _traverse(child)
                        child_node.last = last
                        child_node.key_repr = key
                        child_node.key_separator = "="
                        append(child_node)
                    else:
                        child_node = _traverse(arg)
                        child_node.last = last
                        append(child_node)
            else:
                node = Node(
                    value_repr=f"<{class_name}>" if angular else f"{class_name}()",
                    children=[],
                    last=root,
                )
        elif _is_attr_object(obj) and not fake_attributes:
            children = []
            append = children.append

            attr_fields = _get_attr_fields(obj)
            if attr_fields:
                node = Node(
                    open_brace=f"{obj.__class__.__name__}(",
                    close_brace=")",
                    children=children,
                    last=root,
                )

                def iter_attrs() -> Iterable[
                    Tuple[str, Any, Optional[Callable[[Any], str]]]
                ]:
                    """Iterate over attr fields and values."""
                    for attr in attr_fields:
                        if attr.repr:
                            try:
                                value = getattr(obj, attr.name)
                            except Exception as error:
                                # Can happen, albeit rarely
                                yield (attr.name, error, None)
                            else:
                                yield (
                                    attr.name,
                                    value,
                                    attr.repr if callable(attr.repr) else None,
                                )

                for last, (name, value, repr_callable) in loop_last(iter_attrs()):
                    if repr_callable:
                        child_node = Node(value_repr=str(repr_callable(value)))
                    else:
                        child_node = _traverse(value)
                    child_node.last = last
                    child_node.key_repr = name
                    child_node.key_separator = "="
                    append(child_node)
            else:
                node = Node(
                    value_repr=f"{obj.__class__.__name__}()", children=[], last=root
                )

        elif (
            is_dataclass(obj)
            and not isinstance(obj, type)
            and not fake_attributes
            and (_is_dataclass_repr(obj) or py_version == (3, 6))
        ):
            obj_id = id(obj)
            if obj_id in visited_ids:
                # Recursion detected
                return Node(value_repr="...")
            push_visited(obj_id)

            children = []
            append = children.append
            node = Node(
                open_brace=f"{obj.__class__.__name__}(",
                close_brace=")",
                children=children,
                last=root,
            )

            for last, field in loop_last(fields(obj)):
                if field.repr:
                    child_node = _traverse(getattr(obj, field.name))
                    child_node.key_repr = field.name
                    child_node.last = last
                    child_node.key_separator = "="
                    append(child_node)

            pop_visited(obj_id)

        elif isinstance(obj, _CONTAINERS):
            for container_type in _CONTAINERS:
                if isinstance(obj, container_type):
                    obj_type = container_type
                    break

            obj_id = id(obj)
            if obj_id in visited_ids:
                # Recursion detected
                return Node(value_repr="...")
            push_visited(obj_id)

            open_brace, close_brace, empty = _BRACES[obj_type](obj)

            if obj_type.__repr__ != type(obj).__repr__:
                node = Node(value_repr=to_repr(obj), last=root)
            elif obj:
                children = []
                node = Node(
                    open_brace=open_brace,
                    close_brace=close_brace,
                    children=children,
                    last=root,
                )
                append = children.append
                num_items = len(obj)
                last_item_index = num_items - 1

                if isinstance(obj, _MAPPING_CONTAINERS):
                    iter_items = iter(obj.items())
                    if max_length is not None:
                        iter_items = islice(iter_items, max_length)
                    for index, (key, child) in enumerate(iter_items):
                        child_node = _traverse(child)
                        child_node.key_repr = to_repr(key)
                        child_node.last = index == last_item_index
                        append(child_node)
                else:
                    iter_values = iter(obj)
                    if max_length is not None:
                        iter_values = islice(iter_values, max_length)
                    for index, child in enumerate(iter_values):
                        child_node = _traverse(child)
                        child_node.last = index == last_item_index
                        append(child_node)
                if max_length is not None and num_items > max_length:
                    append(Node(value_repr=f"... +{num_items-max_length}", last=True))
            else:
                node = Node(empty=empty, children=[], last=root)

            pop_visited(obj_id)
        else:
            node = Node(value_repr=to_repr(obj), last=root)
        node.is_tuple = isinstance(obj, tuple)
        return node

    node = _traverse(_object, root=True)
    return node


def pretty_repr(
    _object: Any,
    *,
    max_width: int = 80,
    indent_size: int = 4,
    max_length: Optional[int] = None,
    max_string: Optional[int] = None,
    expand_all: bool = False,
) -> str:
    """Prettify repr string by expanding on to new lines to fit within a given width.

    Args:
        _object (Any): Object to repr.
        max_width (int, optional): Desired maximum width of repr string. Defaults to 80.
        indent_size (int, optional): Number of spaces to indent. Defaults to 4.
        max_length (int, optional): Maximum length of containers before abbreviating, or None for no abbreviation.
            Defaults to None.
        max_string (int, optional): Maximum length of string before truncating, or None to disable truncating.
            Defaults to None.
        expand_all (bool, optional): Expand all containers regardless of available width. Defaults to False.

    Returns:
        str: A possibly multi-line representation of the object.
    """

    if isinstance(_object, Node):
        node = _object
    else:
        node = traverse(_object, max_length=max_length, max_string=max_string)
    repr_str = node.render(
        max_width=max_width, indent_size=indent_size, expand_all=expand_all
    )
    return repr_str


def pprint(
    _object: Any,
    *,
    console: Optional["Console"] = None,
    indent_guides: bool = True,
    max_length: Optional[int] = None,
    max_string: Optional[int] = None,
    expand_all: bool = False,
) -> None:
    """A convenience function for pretty printing.

    Args:
        _object (Any): Object to pretty print.
        console (Console, optional): Console instance, or None to use default. Defaults to None.
        max_length (int, optional): Maximum length of containers before abbreviating, or None for no abbreviation.
            Defaults to None.
        max_string (int, optional): Maximum length of strings before truncating, or None to disable. Defaults to None.
        indent_guides (bool, optional): Enable indentation guides. Defaults to True.
        expand_all (bool, optional): Expand all containers. Defaults to False.
    """
    _console = get_console() if console is None else console
    _console.print(
        Pretty(
            _object,
            max_length=max_length,
            max_string=max_string,
            indent_guides=indent_guides,
            expand_all=expand_all,
            overflow="ignore",
        ),
        soft_wrap=True,
    )


if __name__ == "__main__":  # pragma: no cover

    class BrokenRepr:
        def __repr__(self) -> str:
            1 / 0
            return "this will fail"

    d = defaultdict(int)
    d["foo"] = 5
    data = {
        "foo": [
            1,
            "Hello World!",
            100.123,
            323.232,
            432324.0,
            {5, 6, 7, (1, 2, 3, 4), 8},
        ],
        "bar": frozenset({1, 2, 3}),
        "defaultdict": defaultdict(
            list, {"crumble": ["apple", "rhubarb", "butter", "sugar", "flour"]}
        ),
        "counter": Counter(
            [
                "apple",
                "orange",
                "pear",
                "kumquat",
                "kumquat",
                "durian" * 100,
            ]
        ),
        "atomic": (False, True, None),
        "Broken": BrokenRepr(),
    }
    data["foo"].append(data)  # type: ignore

    from quo import evoke

    evoke(Pretty(data, indent_guides=True, max_string=20))

# *********************

def render_scope(
    scope: "Mapping[str, Any]",
    *,
    title: Optional[TextType] = None,
    sort_keys: bool = True,
    indent_guides: bool = False,
    max_length: Optional[int] = None,
    max_string: Optional[int] = None,
) -> "ConsoleRenderable":
    """Render python variables in a given scope.

    Args:
        scope (Mapping): A mapping containing variable names and values.
        title (str, optional): Optional title. Defaults to None.
        sort_keys (bool, optional): Enable sorting of items. Defaults to True.
        indent_guides (bool, optional): Enable indentaton guides. Defaults to False.
        max_length (int, optional): Maximum length of containers before abbreviating, or None for no abbreviation.
            Defaults to None.
        max_string (int, optional): Maximum length of string before truncating, or None to disable. Defaults to None.

    Returns:
        ConsoleRenderable: A renderable object.
    """
    highlighter = ReprHighlighter()
    items_table = Table.grid(padding=(0, 1), expand=False)
    items_table.add_column(justify="right")

    def sort_items(item: Tuple[str, Any]) -> Tuple[bool, str]:
        """Sort special variables first, then alphabetically."""
        key, _ = item
        return (not key.startswith("__"), key.lower())

    items = sorted(scope.items(), key=sort_items) if sort_keys else scope.items()
    for key, value in items:
        key_text = Text.assemble(
            (key, "scope.key.special" if key.startswith("__") else "scope.key"),
            (" =", "scope.equals"),
        )
        items_table.add_row(
            key_text,
            Pretty(
                value,
                highlighter=highlighter,
                indent_guides=indent_guides,
                max_length=max_length,
                max_string=max_string,
            ),
        )
    return Panel.fit(
        items_table,
        title=title,
        border_style="scope.border",
        padding=(0, 1),
    )


if __name__ == "__main__":  # pragma: no cover
    from quo import Console

    console = Console() 


    def test(foo: float, bar: float) -> None:
        list_of_things = [1, 2, 3, None, 4, True, False, "Hello World"]
        dict_of_things = {
            "version": "1.1",
            "method": "confirmFruitPurchase",
            "params": [["apple", "orange", "mangoes", "pomelo"], 1.123],
            "id": "194521489",
        }
        console.echo(render_scope(locals(), title="[i]locals", sort_keys=False))

    test(20.3423, 3.1427)
    console.echo()
