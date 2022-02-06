#!/usr/bin/env python
# encoding: utf-8

from setup_defs import get_install_extras_require

if __name__ == "__main__":
    with open("requirements-all.txt", "wt", encoding="utf8") as outfp:
        with open("requirements-github.txt", "wt", encoding="utf8") as outfp2:
            rqs = get_install_extras_require()
            rall = rqs["all"]
            written = set()
            for req in rall:
                if req not in written:
                    print(req, file=outfp)
                    written.add(req)
                    if not req.startswith("stanza"):
                        print(req, file=outfp2)
            for req in rqs["github"]:
                if req not in written:
                    print(req, file=outfp2)
                    written.add(req)
