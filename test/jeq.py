#!/usr/bin/env python3

import json
import os
import sys

with open(sys.argv[1]) as f:
    if not json.load(sys.stdin) == json.load(f):
        sys.exit(1)
