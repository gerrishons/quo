from typing import Iterator, List, Optional, Tuple

from ._loop import loop_first, loop_last
from .terminal import Terminal, ConsoleOptions, RenderableType, RenderResult
from .jupyter import JupyterMixin
from quo.width import Measurement
from .segment import Segment
from .style import Style, StyleStack, StyleType
from .styled import Styled


class Tree(JupyterMixin):
    """A renderable for a tree structure.

    Args:
        label (RenderableType): The renderable or str for the tree label.
        style (StyleType, optional): Style of this tree. Defaults to "tree".
        guide_style (StyleType, optional): Style of the guide lines. Defaults to "tree.line".
        expanded (bool, optional): Also display children. Defaults to True.
        highlight (bool, optional): Highlight renderable (if str). Defaults to False.
    """

    def __init__(
        self,
        label: RenderableType,
        *,
        style: StyleType = "tree",
        guide_style: StyleType = "tree.line",
        expanded: bool = True,
        highlight: bool = False,
    ) -> None:
        self.label = label
        self.style = style
        self.guide_style = guide_style
        self.children: List[Tree] = []
        self.expanded = expanded
        self.highlight = highlight

    def add(
        self,
        label: RenderableType,
        *,
        style: Optional[StyleType] = None,
        guide_style: Optional[StyleType] = None,
        expanded: bool = True,
        highlight: bool = False,
    ) -> "Tree":
        """Add a child tree.

        Args:
            label (RenderableType): The renderable or str for the tree label.
            style (StyleType, optional): Style of this tree. Defaults to "tree".
            guide_style (StyleType, optional): Style of the guide lines. Defaults to "tree.line".
            expanded (bool, optional): Also display children. Defaults to True.
            highlight (Optional[bool], optional): Highlight renderable (if str). Defaults to False.

        Returns:
            Tree: A new child Tree, which may be further modified.
        """
        node = Tree(
            label,
            style=self.style if style is None else style,
            guide_style=self.guide_style if guide_style is None else guide_style,
            expanded=expanded,
            highlight=self.highlight if highlight is None else highlight,
        )
        self.children.append(node)
        return node

    def __quo_console__(
        self, console: "Terminal", options: "ConsoleOptions"
    ) -> "RenderResult":

        stack: List[Iterator[Tuple[bool, Tree]]] = []
        pop = stack.pop
        push = stack.append
        new_line = Segment.line()

        get_style = console.get_style
        null_style = Style.null()
        guide_style = get_style(self.guide_style, default="") or null_style
        SPACE, CONTINUE, FORK, END = range(4)

        ASCII_GUIDES = ("    ", "|   ", "+-- ", "`-- ")
        TREE_GUIDES = [
            ("    ", "│   ", "├── ", "└── "),
            ("    ", "┃   ", "┣━━ ", "┗━━ "),
            ("    ", "║   ", "╠══ ", "╚══ "),
        ]
        _Segment = Segment

        def make_guide(index: int, style: Style) -> Segment:
            """Make a Segment for a level of the guide lines."""
            if options.ascii_only:
                line = ASCII_GUIDES[index]
            else:
                guide = 1 if style.bold else (2 if style.underline2 else 0)
                line = TREE_GUIDES[0 if options.legacy_windows else guide][index]
            return _Segment(line, style)

        levels: List[Segment] = [make_guide(CONTINUE, guide_style)]
        push(iter(loop_last([self])))

        guide_style_stack = StyleStack(get_style(self.guide_style))
        style_stack = StyleStack(get_style(self.style))
        remove_guide_styles = Style(bold=False, underline2=False)

        while stack:
            stack_node = pop()
            try:
                last, node = next(stack_node)
            except StopIteration:
                levels.pop()
                if levels:
                    guide_style = levels[-1].style or null_style
                    levels[-1] = make_guide(FORK, guide_style)
                    guide_style_stack.pop()
                    style_stack.pop()
                continue
            push(stack_node)
            if last:
                levels[-1] = make_guide(END, levels[-1].style or null_style)

            guide_style = guide_style_stack.current + get_style(node.guide_style)
            style = style_stack.current + get_style(node.style)
            prefix = levels[1:]
            renderable_lines = console.render_lines(
                Styled(node.label, style),
                options.update(
                    width=options.max_width
                    - sum(level.cell_length for level in prefix),
                    highlight=self.highlight,
                    height=None,
                ),
            )
            for first, line in loop_first(renderable_lines):
                if prefix:
                    yield from _Segment.apply_style(
                        prefix,
                        style.background_style,
                        post_style=remove_guide_styles,
                    )
                yield from line
                yield new_line
                if first and prefix:
                    prefix[-1] = make_guide(
                        SPACE if last else CONTINUE, prefix[-1].style or null_style
                    )

            if node.expanded and node.children:
                levels[-1] = make_guide(
                    SPACE if last else CONTINUE, levels[-1].style or null_style
                )
                levels.append(
                    make_guide(END if len(node.children) == 1 else FORK, guide_style)
                )
                style_stack.push(get_style(node.style))
                guide_style_stack.push(get_style(node.guide_style))
                push(iter(loop_last(node.children)))

    def __quo_measure__(
        self, console: "Terminal", options: "ConsoleOptions"
    ) -> "Measurement":
        stack: List[Iterator[Tree]] = [iter([self])]
        pop = stack.pop
        push = stack.append
        minimum = 0
        maximum = 0
        measure = Measurement.get
        level = 0
        while stack:
            iter_tree = pop()
            try:
                tree = next(iter_tree)
            except StopIteration:
                level -= 1
                continue
            push(iter_tree)
            min_measure, max_measure = measure(console, options, tree.label)
            indent = level * 4
            minimum = max(min_measure + indent, minimum)
            maximum = max(max_measure + indent, maximum)
            if tree.expanded and tree.children:
                push(iter(tree.children))
                level += 1
        return Measurement(minimum, maximum)


if __name__ == "__main__":  # pragma: no cover

    from quo.terminal import Group
    from quo.markdown import Markdown
    from quo.panel import Panel
    from quo.syntax import Syntax
    from quo.tabulate import Table

    table = Table(row_styles=["", "dim"])

    table.add_column("Released", style="cyan", no_wrap=True)
    table.add_column("Title", style="magenta")
    table.add_column("Box Office", justify="right", style="green")

    table.add_row("Dec 20, 2019", "Star Wars: The Rise of Skywalker", "$952,110,690")
    table.add_row("May 25, 2018", "Solo: A Star Wars Story", "$393,151,347")
    table.add_row("Dec 15, 2017", "Star Wars Ep. V111: The Last Jedi", "$1,332,539,889")
    table.add_row("Dec 16, 2016", "Rogue One: A Star Wars Story", "$1,332,439,889")

    code = """\
class Segment(NamedTuple):
    text: str = ""    
    style: Optional[Style] = None    
    is_control: bool = False    
"""
    syntax = Syntax(code, "python", theme="monokai", line_numbers=True)

    markdown = Markdown(
        """\
### example.md
> Hello, World!
> 
> Markdown _all_ the things
"""
    )

    root = Tree("🌲 [b green]Quo Tree", highlight=True)

    node = root.add(":file_folder: Renderables", guide_style="red")
    simple_node = node.add(":file_folder: [bold yellow]Atomic", guide_style="uu green")
    simple_node.add(Group("📄 Syntax", syntax))
    simple_node.add(Group("📄 Markdown", Panel(markdown, border_style="green")))

    containers_node = node.add(
        ":file_folder: [bold magenta]Containers", guide_style="bold magenta"
    )
    containers_node.expanded = True
    panel = Panel.fit("Just a panel", border_style="red")
    containers_node.add(Group("📄 Panels", panel))

    containers_node.add(Group("📄 [b magenta]Table", table))

    console = Terminal()
    console.print(root)
