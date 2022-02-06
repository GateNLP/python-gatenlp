#!/usr/bin/env python
# encoding: utf-8

from setup_defs import get_install_extras_require

if __name__ == "__main__":
    with open("requirements-all.txt", "wt", encoding="utf8") as outfp:
        rqs = get_install_extras_require()
        rall = rqs["all"]
        for req in rall:
            print(req, file=outfp)
