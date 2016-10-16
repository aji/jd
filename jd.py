#!/usr/bin/env python3

import json
import os
import sys

def is_ref(node):
    return isinstance(node, type({})) and list(node.keys()) == ['$ref']

def frag_unesc(s):
    return s\
        .replace('~1', '/')\
        .replace('~0', '~')

class Resolver(object):
    def __init__(self, path=None):
        self.path = path
        self._loaded_doc = None

    def deref(self, ref):
        path, _, frag = ref.partition('#')

        if path:
            path = os.path.join(self._root(), path)
            return Resolver(path).deref('#' + frag)

        frag = [frag_unesc(x) for x in frag.split('/') if x]
        return self.resolve(self._follow_frag(self._doc(), frag))

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

    def _root(self):
        return os.path.dirname(self.path) if self.path is not None else '.'

    def _doc(self):
        if self._loaded_doc is None:
            if self.path is not None:
                with open(self.path, 'r') as f:
                    self._loaded_doc = json.load(f)
            else:
                self._loaded_doc = json.load(sys.stdin)
        return self._loaded_doc

    def _follow_frag(self, node, frag):
        for el in frag:
            if is_ref(node):
                node = self.deref(node['$ref'])
            node = node[int(el) if el.isdigit() else el]
        return node

if __name__ == '__main__':
    resolver = Resolver()
    for arg in sys.argv[1:]:
        json.dump(resolver.deref(arg), sys.stdout, indent=2)
        print()
