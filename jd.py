#!/usr/bin/env python3

import json
import os
import sys

def is_ref(node):
    return isinstance(node, type({})) and list(node.keys()) == ['$ref']

class Resolver(object):
    def __init__(self, root='.', doc=None):
        self.root = root
        self._doc = doc

    def doc(self):
        if self._doc is None:
            self._doc = json.load(sys.stdin)
        return self._doc

    def deref(self, ref):
        path, _, frag = ref.partition('#')

        if path:
            path = os.path.join(self.root, path)
            root = os.path.dirname(path)
            with open(path, 'r') as f:
                doc = json.load(f)
            return Resolver(root, doc).deref('#' + frag)

        node = self.doc()
        for el in [x for x in frag.split('/') if x]:
            if is_ref(node):
                node = self.deref(node['$ref'])
            node = node[int(el) if el.isdigit() else el]

        return self.resolve(node)

    def resolve(self, node=None):
        if node is None:
            node = self.doc()
        if is_ref(node):
            return self.deref(node['$ref'])
        if isinstance(node, type([])):
            return [self.resolve(x) for x in node]
        if isinstance(node, type({})):
            return { k: self.resolve(v) for k, v in node.items() }
        return node

if __name__ == '__main__':
    resolver = Resolver()
    for arg in sys.argv[1:]:
        json.dump(resolver.deref(arg), sys.stdout, indent=2)
        print()
