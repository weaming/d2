#!/usr/bin/env python3
# coding: utf-8

import sys
import argparse
import subprocess
import requests
from tabulate import tabulate

version = "0.2"


def http_get_json(url, params=None, is_json=True, encoding="utf8"):
    res = requests.get(url, params=params)
    if encoding:
        res.encoding = encoding

    err = False if res.status_code == 200 else res.status_code
    data = res.json() if is_json else res.text
    return err, data


def cli(args):
    err, data = http_get_json(args.url)
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
        print(data)
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("-d", "--data-path")
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
    )
    parser.add_argument("-p", "--pure", action="store_true")
    args = parser.parse_args()
    cli(args)


if __name__ == "__main__":
    main()
