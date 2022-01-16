#!/usr/bin/env python
"""
Example of using the control-space key binding for auto completion.
"""
import quo

animal_completer = quo.completion.WordCompleter(
    [
        "alligator",
        "ant",
        "ape",
        "bat",
        "bear",
        "beaver",
        "bee",
        "bison",
        "butterfly",
        "cat",
        "chicken",
        "crocodile",
        "dinosaur",
        "dog",
        "dolphin",
        "dove",
        "duck",
        "eagle",
        "elephant",
        "fish",
        "goat",
        "gorilla",
        "kangaroo",
        "leopard",
        "lion",
        "mouse",
        "rabbit",
        "rat",
        "snake",
        "spider",
        "turkey",
        "turtle",
    ],
    ignore_case=True,
)

session = quo.Prompt()
kb = quo.keys.KeyBinder()


@kb.add("ctrl-space")
def _(event):
    """
    Start auto completion. If the menu is showing already, select the next
    completion.
    """
    b = event.app.current_buffer
    if b.complete_state:
        b.complete_next()
    else:
        b.start_completion(select_first=False)


def main():
    text = session.prompt(
        "Give some animals: ",
        completer=animal_completer,
        complete_while_typing=False,
        bind=kb,
    )
    print("You said: %s" % text)


if __name__ == "__main__":
    main()
