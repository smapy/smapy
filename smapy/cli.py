# -*- coding: utf-8 -*-

import argparse
import sys

from smapy.application import SmapyApplication


def main():
    parser = argparse.ArgumentParser(description='Smapy CLI')
    parser.add_argument('config_file', help='Path to the config file')

    args = parser.parse_args()

    app = SmapyApplication(args.config_file)
    sys.exit(app.run())


if __name__ == '__main__':
    main()
