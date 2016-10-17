#!/usr/bin/env python3

import json
import os
import sys

with open(sys.argv[1]) as f:
    try:
        if not json.load(sys.stdin) == json.load(f):
            sys.exit(1)
    except Exception:
        sys.exit(2)
