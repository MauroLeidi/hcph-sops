#!/usr/bin/env python3
# From: https://gist.github.com/jannismain/e96666ca4f059c3e5bc28abb711b5c92
from __future__ import annotations

import json


class CompactJSONEncoder(json.JSONEncoder):
    """A JSON Encoder that puts small containers on single lines."""

    CONTAINER_TYPES = (list, tuple, dict)
    """Container datatypes include primitives or other containers."""

    MAX_WIDTH = 99
    """Maximum width of a container that might be put on a single line."""

    MAX_ITEMS = 5
    """Maximum number of items in container that might be put on single line."""

    DISABLE_MULTILINE_ITEMS = 20
    """
    A threshold for the number of items above which lines will not be broken by ``MAX_ITEMS``.
    """

    def __init__(self, *args, **kwargs):
        # using this class without indentation is pointless
        if kwargs.get("indent") is None:
            kwargs["indent"] = 4

        super().__init__(*args, **kwargs)
        self.indentation_level = 0

    def encode(self, o):
        """Encode JSON object *o* with respect to single line lists."""
        if isinstance(o, (list, tuple)):
            return self._encode_list(o)
        if isinstance(o, dict):
            if self.sort_keys:
                o = dict(sorted(o.items()))
            return self._encode_object(o)

        return json.dumps(
            o,
            skipkeys=self.skipkeys,
            ensure_ascii=self.ensure_ascii,
            check_circular=self.check_circular,
            allow_nan=self.allow_nan,
            sort_keys=self.sort_keys,
            indent=self.indent,
            separators=(self.item_separator, self.key_separator),
            default=self.default if hasattr(self, "default") else None,
        )

    def _encode_list(self, o):
        if self._put_on_single_line(o):  # single line
            return "[" + ", ".join(self.encode(el) for el in o) + "]"

        max_width = 0 if len(o) < self.DISABLE_MULTILINE_ITEMS else self.MAX_WIDTH

        self.indentation_level += 1
        output = (
            self._stack_list(o, max_width=max_width)
            if self._primitives_only(o)
            else [self.indent_str + self.encode(el) for el in o]
        )
        self.indentation_level -= 1
        return "[\n" + ",\n".join(output) + "\n" + self.indent_str + "]"

    def _stack_list(self, inlist, max_width=0):
        lines = [[]]
        for item in inlist:
            last_line = lines[-1]

            if last_line and len(str(last_line + [item])) - 2 > max_width:
                lines.append([item])
            else:
                last_line.append(item)

        output = [
            self.indent_str + ", ".join(self.encode(el) for el in line)
            for line in lines
        ]
        return output

    def _encode_object(self, o):
        if not o:
            return "{}"
        if self._put_on_single_line(o):
            return (
                "{ "
                + ", ".join(
                    f"{self.encode(k)}: {self.encode(el)}" for k, el in o.items()
                )
                + " }"
            )
        self.indentation_level += 1
        output = [
            f"{self.indent_str}{json.dumps(k)}: {self.encode(v)}" for k, v in o.items()
        ]

        self.indentation_level -= 1
        return "{\n" + ",\n".join(output) + "\n" + self.indent_str + "}"

    def iterencode(self, o, **kwargs):
        """Required to also work with `json.dump`."""
        return self.encode(o)

    def _put_on_single_line(self, o):
        return (
            self._primitives_only(o)
            and len(o) <= self.MAX_ITEMS
            and len(str(o)) - 2 <= self.MAX_WIDTH
        )

    def _primitives_only(self, o: list | tuple | dict):
        if isinstance(o, (list, tuple)):
            return not any(isinstance(el, self.CONTAINER_TYPES) for el in o)
        elif isinstance(o, dict):
            return not any(isinstance(el, self.CONTAINER_TYPES) for el in o.values())

    @property
    def indent_str(self) -> str:
        if isinstance(self.indent, int):
            return " " * (self.indentation_level * self.indent)
        elif isinstance(self.indent, str):
            return self.indentation_level * self.indent
        else:
            raise ValueError(
                f"indent must either be of type int or str (is: {type(self.indent)})"
            )
