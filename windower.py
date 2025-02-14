#!/usr/bin/env python3
"""
File: windower.py
Authors: Johan Sääskilahti, Atte Rajavaara, Minna Repo, Topias Hämäläinen
Description: This tool was designed to create windows from preprocessed JSON data
"""

import argparse
import orjson
import datetime
import sys

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
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbosity',
                        default=False)
    parser.add_argument('-f', '--file', type=str, help='Path to the JSON file',
                        required=True)

    return parser.parse_args(args=None if sys.argv[1:] else ['--help'])

def main():
    """
        The entrypoint
    """
    args = handle_args()
    
    if args.file:
        try:
            with open(args.file, 'r') as file:
                data = orjson.loads(file.read())
        except FileNotFoundError:
            raise Exception(f"File {args.file} not found")

        print(data)
        if args.verbose:
            print(f"Loaded {args.file} successfully")


if __name__ == '__main__':
    main()
