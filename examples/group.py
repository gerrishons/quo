from quo import Console, Panel
from quo.console.console import group

cc = Console()
@group()
def get_panels():
    yield Panel("Hello", style="on blue")
    yield Panel("World", style="on red")


cc.echo(Panel(get_panels()))
