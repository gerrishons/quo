[![Downloads](https://pepy.tech/badge/quo)](https://pepy.tech/project/quo)
[![PyPI version](https://badge.fury.io/py/quo.svg)](https://badge.fury.io/py/quo)
[![Wheel](https://img.shields.io/pypi/wheel/quo.svg)](https://pypi.com/project/quo)
[![Windows Build Status](https://img.shields.io/appveyor/build/gerrishons/quo/master?logo=appveyor&cacheSeconds=600)](https://ci.appveyor.com/project/gerrishons/quo)
[![pyimp](https://img.shields.io/pypi/implementation/quo.svg)](https://pypi.com/project/quo)
[![RTD](https://readthedocs.org/projects/quo/badge/)](https://quo.readthedocs.io)
[![licence](https://img.shields.io/pypi/l/quo.svg)](https://opensource.org/licenses/MIT)
[![Twitter Follow](https://img.shields.io/twitter/follow/gerrishon_s.svg?style=social)](https://twitter.com/gerrishon_s)


[![Logo](pics/quo.png)](https://github.com/secretum-inc/quo)


`Forever Scalable`

**Quo** is a Python based toolkit for writing Command-Line Interface(CLI) applications.
Quo is making headway towards composing speedy and orderly CLI applications while forestalling any disappointments brought about by the failure to execute a CLI API.
Simple to code, easy to learn, and does not come with needless baggage. 

Quo requires Python `3.6.1` or later. 


## Features
- Support for ANSI and RGB color models
- Support for tabular presentation of data
- Interactive progressbars
- Nesting of commands
- A function that displays asterisks instead of the actual characters, helpful when typing passwords
- Automatic help page generation
- Lightweight

## Installation
You can install quo via the Python Package Index (PyPI)

```
pip install -U quo
```


## Quo print
```python
   from quo import quo
   echo(f"Hello, World!", fg="red", italic=True, bold=True))
```
![Hello World](https://github.com/secretum-inc/quo/raw/master/pics/print.png)

This will print ``"Hello World!"`` plus a new line to the terminal. 
Unlike the builtin print function, ``echo`` function has improved support for handling Unicode and binary data.
If ![colorama](https://pypi.org/project/colorama/) is installed, the echo function will also support handling of ANSI color sequences.

## Quo prompt
```python
   from quo import prompt
   prompt("What is your name?")
```
![prompt](https://github.com/secretum-inc/quo/raw/master/pics/prompt.png)

**Example 5**

```python
   from quo import command, app, echo

   @command()
   @app("--name", prompt="What is your name?", type=str)
   @app("--age", prompt="How old are you?", type=int)
   def hello(name, age):
        echo(f"Hello {name}, nice to meet ya")
        echo(f"{name}, {age} is not that bad"
```

**Example 6**



For more intricate  examples, have a look in the ``tutorials`` directory and the documentation.



## Donate🎁

In order to for us to maintain this project and grow our community of contributors.
[Donate](https://www.paypal.com/donate?hosted_button_id=KP893BC2EKK54)



## Quo is...

**Simple**
     If you know Python you can  easily use quo and it can integrate with just about anything.




## Getting Help

### Gitter

For discussions about the usage, development, and future of quo, please join our Gitter community

* [Join](https://gitter.im/secretum-inc/quo)

## Resources

### Bug tracker

If you have any suggestions, bug reports, or annoyances please report them
to our issue tracker at 
[Bug tracker](https://github.com/secretum-inc/quo/issues/)


## License📑

This software is licensed under the `MIT License`. See the [License](https://github.com/secretum-inc/quo/blob/master/License) file in the top distribution directory for the full license text.


## Code of Conduct
Code of Conduct is adapted from the Contributor Covenant,
version 1.2.0 available at
[Code of Conduct](http://contributor-covenant.org/version/1/2/0/)



The [Rich API](https://rich.readthedocs.io/en/latest/) makes it easy to add color and style to terminal output. Rich can also render pretty tables, progress bars, markdown, syntax highlighted source code, tracebacks, and more — out of the box.

![Features](https://github.com/willmcgugan/rich/raw/master/imgs/features.png)

For a video introduction to Rich see [calmcode.io](https://calmcode.io/rich/introduction.html) by [@fishnets88](https://twitter.com/fishnets88).

See what [people are saying about Rich](https://www.willmcgugan.com/blog/pages/post/rich-tweets/).

## Compatibility

Quo works with [Jupyter notebooks](https://jupyter.org/) with no additional configuration required.





## Rich REPL

Rich can be installed in the Python REPL, so that any data structures will be pretty printed and highlighted.

```python
>>> from rich import pretty
>>> pretty.install()
```

![REPL](https://github.com/willmcgugan/rich/raw/master/imgs/repl.png)

## Using the Console

For more control over rich terminal content, import and construct a [Console](https://rich.readthedocs.io/en/latest/reference/console.html#rich.console.Console) object.

```python
from rich.console import Console

console = Console()
```

The Console object has a `print` method which has an intentionally similar interface to the builtin `print` function. Here's an example of use:

```python
console.print("Hello", "World!")
```

As you might expect, this will print `"Hello World!"` to the terminal. Note that unlike the builtin `print` function, Rich will word-wrap your text to fit within the terminal width.

There are a few ways of adding color and style to your output. You can set a style for the entire output by adding a `style` keyword argument. Here's an example:

```python
console.print("Hello", "World!", style="bold red")
```

The output will be something like the following:

![Hello World](https://github.com/willmcgugan/rich/raw/master/imgs/hello_world.png)

That's fine for styling a line of text at a time. For more finely grained styling, Rich renders a special markup which is similar in syntax to [bbcode](https://en.wikipedia.org/wiki/BBCode). Here's an example:

```python
console.print("Where there is a [bold cyan]Will[/bold cyan] there [u]is[/u] a [i]way[/i].")
```

![Console Markup](https://github.com/willmcgugan/rich/raw/master/imgs/where_there_is_a_will.png)

You can use a Console object to generate sophisticated output with minimal effort. See the [Console API](https://rich.readthedocs.io/en/latest/console.html) docs for details.

## Rich Inspect

Rich has an [inspect](https://rich.readthedocs.io/en/latest/reference/init.html?highlight=inspect#rich.inspect) function which can produce a report on any Python object, such as class, instance, or builtin.

```python
>>> my_list = ["foo", "bar"]
>>> from rich import inspect
>>> inspect(my_list, methods=True)
```

![Log](https://github.com/willmcgugan/rich/raw/master/imgs/inspect.png)

See the [inspect docs](https://rich.readthedocs.io/en/latest/reference/init.html#rich.inspect) for details.

# Rich Library

Rich contains a number of builtin _renderables_ you can use to create elegant output in your CLI and help you debug your code.

Click the following headings for details:

<details>
<summary>Log</summary>

The Console object has a `log()` method which has a similar interface to `print()`, but also renders a column for the current time and the file and line which made the call. By default Rich will do syntax highlighting for Python structures and for repr strings. If you log a collection (i.e. a dict or a list) Rich will pretty print it so that it fits in the available space. Here's an example of some of these features.

```python
from rich.console import Console
console = Console()

test_data = [
    {"jsonrpc": "2.0", "method": "sum", "params": [None, 1, 2, 4, False, True], "id": "1",},
    {"jsonrpc": "2.0", "method": "notify_hello", "params": [7]},
    {"jsonrpc": "2.0", "method": "subtract", "params": [42, 23], "id": "2"},
]

def test_log():
    enabled = False
    context = {
        "foo": "bar",
    }
    movies = ["Deadpool", "Rise of the Skywalker"]
    console.log("Hello from", console, "!")
    console.log(test_data, log_locals=True)


test_log()
```

The above produces the following output:

![Log](https://github.com/willmcgugan/rich/raw/master/imgs/log.png)

Note the `log_locals` argument, which outputs a table containing the local variables where the log method was called.

The log method could be used for logging to the terminal for long running applications such as servers, but is also a very nice debugging aid.

</details>
<details>
<summary>Logging Handler</summary>

You can also use the builtin [Handler class](https://rich.readthedocs.io/en/latest/logging.html) to format and colorize output from Python's logging module. Here's an example of the output:

![Logging](https://github.com/willmcgugan/rich/raw/master/imgs/logging.png)

</details>

<details>
<summary>Emoji</summary>

To insert an emoji in to console output place the name between two colons. Here's an example:

```python
>>> console.print(":smiley: :vampire: :pile_of_poo: :thumbs_up: :raccoon:")
😃 🧛 💩 👍 🦝
```

Please use this feature wisely.

</details>

<details>
<summary>Tables</summary>

Rich can render flexible [tables](https://rich.readthedocs.io/en/latest/tables.html) with unicode box characters. There is a large variety of formatting options for borders, styles, cell alignment etc.

![table movie](https://github.com/willmcgugan/rich/raw/master/imgs/table_movie.gif)

The animation above was generated with [table_movie.py](https://github.com/willmcgugan/rich/blob/master/examples/table_movie.py) in the examples directory.

Here's a simpler table example:

```python
from rich.console import Console
from rich.table import Table

console = Console()

table = Table(show_header=True, header_style="bold magenta")
table.add_column("Date", style="dim", width=12)
table.add_column("Title")
table.add_column("Production Budget", justify="right")
table.add_column("Box Office", justify="right")
table.add_row(
    "Dev 20, 2019", "Star Wars: The Rise of Skywalker", "$275,000,000", "$375,126,118"
)
table.add_row(
    "May 25, 2018",
    "[red]Solo[/red]: A Star Wars Story",
    "$275,000,000",
    "$393,151,347",
)
table.add_row(
    "Dec 15, 2017",
    "Star Wars Ep. VIII: The Last Jedi",
    "$262,000,000",
    "[bold]$1,332,539,889[/bold]",
)

console.print(table)
```

This produces the following output:

![table](https://github.com/willmcgugan/rich/raw/master/imgs/table.png)

Note that console markup is rendered in the same way as `print()` and `log()`. In fact, anything that is renderable by Rich may be included in the headers / rows (even other tables).

The `Table` class is smart enough to resize columns to fit the available width of the terminal, wrapping text as required. Here's the same example, with the terminal made smaller than the table above:

![table2](https://github.com/willmcgugan/rich/raw/master/imgs/table2.png)

</details>

<details>
<summary>Progress Bars</summary>

Rich can render multiple flicker-free [progress](https://rich.readthedocs.io/en/latest/progress.html) bars to track long-running tasks.

For basic usage, wrap any sequence in the `track` function and iterate over the result. Here's an example:

```python
from rich.progress import track

for step in track(range(100)):
    do_step(step)
```

It's not much harder to add multiple progress bars. Here's an example taken from the docs:

![progress](https://github.com/willmcgugan/rich/raw/master/imgs/progress.gif)

The columns may be configured to show any details you want. Built-in columns include percentage complete, file size, file speed, and time remaining. Here's another example showing a download in progress:

![progress](https://github.com/willmcgugan/rich/raw/master/imgs/downloader.gif)

To try this out yourself, see [examples/downloader.py](https://github.com/willmcgugan/rich/blob/master/examples/downloader.py) which can download multiple URLs simultaneously while displaying progress.

</details>

<details>
<summary>Status</summary>

For situations where it is hard to calculate progress, you can use the [status](https://rich.readthedocs.io/en/latest/reference/console.html#rich.console.Console.status) method which will display a 'spinner' animation and message. The animation won't prevent you from using the console as normal. Here's an example:

```python
from time import sleep
from rich.console import Console

console = Console()
tasks = [f"task {n}" for n in range(1, 11)]

with console.status("[bold green]Working on tasks...") as status:
    while tasks:
        task = tasks.pop(0)
        sleep(1)
        console.log(f"{task} complete")
```

This generates the following output in the terminal.

![status](https://github.com/willmcgugan/rich/raw/master/imgs/status.gif)

The spinner animations were borrowed from [cli-spinners](https://www.npmjs.com/package/cli-spinners). You can select a spinner by specifying the `spinner` parameter. Run the following command to see the available values:

```
python -m rich.spinner
```

The above command generates the following output in the terminal:

![spinners](https://github.com/willmcgugan/rich/raw/master/imgs/spinners.gif)

</details>

<details>
<summary>Tree</summary>

Rich can render a [tree](https://rich.readthedocs.io/en/latest/tree.html) with guide lines. A tree is ideal for displaying a file structure, or any other hierarchical data.

The labels of the tree can be simple text or anything else Rich can render. Run the following for a demonstration:

```
python -m rich.tree
```

This generates the following output:

![markdown](https://github.com/willmcgugan/rich/raw/master/imgs/tree.png)

See the [tree.py](https://github.com/willmcgugan/rich/blob/master/examples/tree.py) example for a script that displays a tree view of any directory, similar to the linux `tree` command.

</details>

<details>
<summary>Columns</summary>

Rich can render content in neat [columns](https://rich.readthedocs.io/en/latest/columns.html) with equal or optimal width. Here's a very basic clone of the (MacOS / Linux) `ls` command which displays a directory listing in columns:

```python
import os
import sys

from rich import print
from rich.columns import Columns

directory = os.listdir(sys.argv[1])
print(Columns(directory))
```

The following screenshot is the output from the [columns example](https://github.com/willmcgugan/rich/blob/master/examples/columns.py) which displays data pulled from an API in columns:

![columns](https://github.com/willmcgugan/rich/raw/master/imgs/columns.png)

</details>

<details>
<summary>Markdown</summary>

Rich can render [markdown](https://rich.readthedocs.io/en/latest/markdown.html) and does a reasonable job of translating the formatting to the terminal.

To render markdown import the `Markdown` class and construct it with a string containing markdown code. Then print it to the console. Here's an example:

```python
from rich.console import Console
from rich.markdown import Markdown

console = Console()
with open("README.md") as readme:
    markdown = Markdown(readme.read())
console.print(markdown)
```

This will produce output something like the following:

![markdown](https://github.com/willmcgugan/rich/raw/master/imgs/markdown.png)

</details>

<details>
<summary>Syntax Highlighting</summary>

Rich uses the [pygments](https://pygments.org/) library to implement [syntax highlighting](https://rich.readthedocs.io/en/latest/syntax.html). Usage is similar to rendering markdown; construct a `Syntax` object and print it to the console. Here's an example:

```python
from rich.console import Console
from rich.syntax import Syntax

my_code = '''
def iter_first_last(values: Iterable[T]) -> Iterable[Tuple[bool, bool, T]]:
    """Iterate and generate a tuple with a flag for first and last value."""
    iter_values = iter(values)
    try:
        previous_value = next(iter_values)
    except StopIteration:
        return
    first = True
    for value in iter_values:
        yield first, False, previous_value
        first = False
        previous_value = value
    yield first, True, previous_value
'''
syntax = Syntax(my_code, "python", theme="monokai", line_numbers=True)
console = Console()
console.print(syntax)
```

This will produce the following output:

![syntax](https://github.com/willmcgugan/rich/raw/master/imgs/syntax.png)

</details>

<details>
<summary>Tracebacks</summary>

Rich can render [beautiful tracebacks](https://rich.readthedocs.io/en/latest/traceback.html) which are easier to read and show more code than standard Python tracebacks. You can set Rich as the default traceback handler so all uncaught exceptions will be rendered by Rich.

Here's what it looks like on OSX (similar on Linux):

![traceback](https://github.com/willmcgugan/rich/raw/master/imgs/traceback.png)

</details>

All Rich renderables make use of the [Console Protocol](https://rich.readthedocs.io/en/latest/protocol.html), which you can also use to implement your own Rich content.

# Rich for enterprise

Available as part of the Tidelift Subscription.

The maintainers of Rich and thousands of other packages are working with Tidelift to deliver commercial support and maintenance for the open source packages you use to build your applications. Save time, reduce risk, and improve code health, while paying the maintainers of the exact packages you use. [Learn more.](https://tidelift.com/subscription/pkg/pypi-rich?utm_source=pypi-rich&utm_medium=referral&utm_campaign=enterprise&utm_term=repo)

# Projects using Rich

Here are a few projects using Rich:

- [BrancoLab/BrainRender](https://github.com/BrancoLab/BrainRender)
  a python package for the visualization of three dimensional neuro-anatomical data
- [Ciphey/Ciphey](https://github.com/Ciphey/Ciphey)
  Automated decryption tool
- [emeryberger/scalene](https://github.com/emeryberger/scalene)
  a high-performance, high-precision CPU and memory profiler for Python
- [hedythedev/StarCli](https://github.com/hedythedev/starcli)
  Browse GitHub trending projects from your command line
- [intel/cve-bin-tool](https://github.com/intel/cve-bin-tool)
  This tool scans for a number of common, vulnerable components (openssl, libpng, libxml2, expat and a few others) to let you know if your system includes common libraries with known vulnerabilities.
- [nf-core/tools](https://github.com/nf-core/tools)
  Python package with helper tools for the nf-core community.
- [cansarigol/pdbr](https://github.com/cansarigol/pdbr)
  pdb + Rich library for enhanced debugging
- [plant99/felicette](https://github.com/plant99/felicette)
  Satellite imagery for dummies.
- [seleniumbase/SeleniumBase](https://github.com/seleniumbase/SeleniumBase)
  Automate & test 10x faster with Selenium & pytest. Batteries included.
- [smacke/ffsubsync](https://github.com/smacke/ffsubsync)
  Automagically synchronize subtitles with video.
- [tryolabs/norfair](https://github.com/tryolabs/norfair)
  Lightweight Python library for adding real-time 2D object tracking to any detector.
- [ansible/ansible-lint](https://github.com/ansible/ansible-lint) Ansible-lint checks playbooks for practices and behaviour that could potentially be improved
- [ansible-community/molecule](https://github.com/ansible-community/molecule) Ansible Molecule testing framework
- +[Many more](https://github.com/willmcgugan/rich/network/dependents)!

<!-- This is a test, no need to translate -->
