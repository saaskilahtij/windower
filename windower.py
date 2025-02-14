#!/usr/bin/env python3
"""
File: windower.py
Authors: Johan Sääskilahti, Atte Rajavaara, Minna Repo, Topias Hämäläinen
Description: This tool was designed to create windows from preprocessed JSON data
"""

import sys
import argparse
import orjson

DESC = r"""
     _     _     _   O             ___        __     _     _     _   ____
     \    | \    |  /|\  __    _  | ___\    /    \    \    | \    |  |   \
      \   |  \   |   |   | \   |  | ^ ^ \  / 0  0 \    \   |  \   |  |____\
       \  |   \  |   |   |  \  |  |   _ /  \   \  /     \  |   \  |  |   \
        \ |    \ |   |   |   \ |  | ___/    \ __ /       \ |    \ |  |    \
         \|     \|   |   |    \|  |___/      \__/         \|     \|  |     \
                         windows made quick and easy
"""

def handle_args():
    """
    This function parses the arguments

    Returns:
        Parsed args
    Note:
        The return can seem a bit funny. However, it makes sure that
        if the tool is ran without args, it will print the help message.
        This is because argparse does not support this out of the box.
    """
    parser = argparse.ArgumentParser(description=DESC, prog='windower.py',
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-f', '--file', type=str, help='Path to the JSON file',
                        required=True)
    parser.add_argument('-o', '--output', type=str, help='Output file name')

    return parser.parse_args(args=None if sys.argv[1:] else ['--help'])

def main():
    """
        The entrypoint
    """
    args = handle_args()
    data = {}

    if args.file:
        try:
            with open(args.file, 'r', encoding='UTF-8') as file:
                # pylint: disable-no-member
                data = orjson.loads(file.read())
        except FileNotFoundError as exc:
            raise FileNotFoundError(f"File {args.file} not found") from exc
        except ValueError as exc:
            raise ValueError(f"Malformed JSON while reading {args.file}") from exc

    if args.output:
        try:
            with open(args.output, 'w', encoding='UTF-8') as f:
                f.write(orjson.dumps(data).decode('UTF-8'))
        except FileNotFoundError as exc:
            raise FileNotFoundError(f"File {args.output} not found") from exc
        except ValueError as exc:
            raise ValueError(f"Malformed JSON while writing to {args.output}") from exc

if __name__ == '__main__':
    main()
