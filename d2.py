#!/usr/bin/env python3
# coding: utf-8

import os
import sys
import re
import argparse
import subprocess
import json
import requests
from tabulate import tabulate

version = "0.6"


def http_get_json(url, params=None, is_json=True, encoding="utf8"):
    res = requests.get(url, params=params)
    if encoding:
        res.encoding = encoding

    err = False if res.status_code == 200 else res.status_code
    data = res.json() if is_json else res.text
    return err, data


def cli(args):
    err, data = http_get_json(args.url, args.params)
    if err:
        print(err)
        sys.exit(1)
    if args.data_path:
        for x in args.data_path.split("."):
            try:
                data = data[x]
            except KeyError as e:
                print(e)
                sys.eixt(1)

    if args.pure:
        out = json.dumps(
            data, ensure_ascii=False, indent=int(os.getenv("JSON_INDENT", 0)) or None
        )
        if args.jq:
            write_to_jq(out)
        else:
            print(out)

        return

    headers = args.include_fields
    headers = headers or (data and list(data[0].keys()))
    if not headers:
        print("missing headers and data is blank")
        sys.exit(2)

    headers = [x for x in headers if x not in args.exclude_fields]
    data = [[str(x[k]) for k in headers if k not in args.exclude_fields] for x in data]
    out = tabulate(data, headers=headers, tablefmt=args.format)
    write_to_less(out, True)


def write_to_jq(text):
    cmd = ["jq"]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    try:
        p.stdin.write(text.encode("utf-8"))
    except BrokenPipeError as e:
        print(e)
        sys.exit(1)


def write_to_less(text, line_numbers):
    less_cmd = ["less", "-S"]
    if line_numbers:
        less_cmd.append("-N")

    p = subprocess.Popen(less_cmd, stdin=subprocess.PIPE)

    try:
        p.stdin.write(text.encode("utf-8"))
    except BrokenPipeError as e:
        print(e)
        sys.exit(1)

    p.communicate()


def parse_params(args, name):
    def remove_quote(text):
        if not text:
            return text
        if text[0] == text[-1] and text[0] in ['"', "'"]:
            return text[1:-1]
        return text

    origin = getattr(args, name)
    if not origin:
        return

    t1 = r"'.+'"
    t2 = r'".+"'
    t3 = r"\S+"
    t123 = "{t1}|{t2}|{t3}".format(t1=t1, t2=t2, t3=t3)
    pat = "(({t})=({t}))( ({t})=({t}))*".format(t=t123)
    reg = re.compile(pat)
    result = reg.search(origin)
    if result:
        groups = result.groups()
        groups = [x for i, x in enumerate(groups) if i % 3 in [1, 2]]
        # remove quotes
        groups = [remove_quote(x) for x in groups]

        keys = [x for i, x in enumerate(groups) if i % 2 == 0]
        values = [x for i, x in enumerate(groups) if i % 2 == 1]
        params = {}
        for k, v in zip(keys, values):
            if None in [k, v]:
                continue
            # support list
            if k in params:
                if not isinstance(params, list):
                    params[k] = [params[k], v]
                else:
                    params[k].append(v)
            else:
                params[k] = v

        DEBUG = os.getenv("DEBUG")
        if DEBUG:
            print(groups)
            print(keys)
            print(values)
            print(params)

        # update property
        setattr(args, name, params)


def main():
    parser = argparse.ArgumentParser(
        description="Get API and show results in table or origin text format"
    )
    parser.add_argument("url")
    parser.add_argument(
        "-d", "--data-path", help="path to extract data from origin response"
    )
    parser.add_argument("-e", "--exclude-fields", nargs="*")
    parser.add_argument("-i", "--include-fields", nargs="*")
    parser.add_argument(
        "-f",
        "--format",
        default="psql",
        choices=[
            "plain",
            "simple",
            "github",
            "grid",
            "fancy_grid",
            "pipe",
            "orgtbl",
            "jira",
            "presto",
            "psql",
            "rst",
            "mediawiki",
            "moinmoin",
            "youtrack",
            "html",
            "latex",
            "latex_raw",
            "latex_booktabs",
            "textile",
        ],
        help="`tabulate` format",
    )
    parser.add_argument(
        "-p", "--pure", action="store_true", help="print origin JSON response"
    )
    parser.add_argument(
        "-j",
        "--jq",
        action="store_true",
        help="write to jq to highlight JSON, combine with -p",
    )
    parser.add_argument(
        "--params",
        help="""params passed to requests in format `a=b ' a b c'=" a 2 b "`""",
    )
    args = parser.parse_args()

    parse_params(args, "params")
    cli(args)


if __name__ == "__main__":
    main()
