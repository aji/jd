#!/usr/bin/env python3

import json
import os
import sys

def is_ref(node):
    return isinstance(node, type({})) and list(node.keys()) == ['$ref']

def deref(ref, root='.', doc=None):
    path, _, frag = ref.partition('#')

    if path:
        path = os.path.join(root, path)
        root = os.path.dirname(path)
        with open(path, 'r') as f:
            doc = json.load(f)
        return deref('#' + frag, root, doc)

    if doc is None:
        doc = json.load(sys.stdin)

    node = doc
    for el in [x for x in frag.split('/') if x]:
        if is_ref(node):
            node = deref(node['$ref'], root, doc)
        node = node[int(el) if el.isdigit() else el]

    return resolve(node, root, doc)

def resolve(node, root='.', doc=None):
    if doc is None:
        doc = node
    if is_ref(node):
        return deref(node['$ref'], root, doc)
    if isinstance(node, type([])):
        return [resolve(x, root, doc) for x in node]
    if isinstance(node, type({})):
        return { k: resolve(v, root, doc) for k, v in node.items() }
    return node

if __name__ == '__main__':
    for arg in sys.argv[1:]:
        json.dump(deref(arg), sys.stdout, indent=2)
        print()
