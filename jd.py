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

def frag_parse(s):
    if s == '':
        return []
    if not s.startswith('/'):
        raise ValueError('invalid fragment identifier: ' + repr(s))
    return [frag_unesc(x) for x in s[1:].split('/')]

def format_exception(e):
    if isinstance(e, RecursionError):
        return 'maximum recursion depth exceeded'
    if isinstance(e, ValueError):
        return str(e)
    return '{}: {}'.format(type(e).__name__, str(e))

class Location(object):
    def __init__(self, uri, at=[]):
        self.uri = uri
        self.at = at
    def describe(self):
        return 'at {}#{}'.format(self.uri, '/'.join([''] + self.at))
    def descend(self, to):
        return Location(self.uri, self.at + [to])

class StdinLocation(Location):
    def __init__(self):
        super().__init__('<stdin>')

class ArgvLocation(Location):
    def __init__(self):
        pass
    def describe(self):
        return 'on command line'
    def descend(self, to):
        raise ValueError('cannot descend an argv location')

class Node(object):
    def __init__(self, j, doc, loc):
        self.j = j
        self.doc = doc
        self.loc = loc

    @staticmethod
    def of(j, doc, loc):
        if is_ref(j):
            return Reference(j, doc, loc)
        if isinstance(j, type([])):
            return Array(j, doc, loc)
        if isinstance(j, type({})):
            return Object(j, doc, loc)
        return Node(j, doc, loc)

    def descend(self, to):
        raise ValueError('cannot descend into a value')

    def resolve(self):
        return self.j

class Reference(Node):
    def __init__(self, j, doc, loc):
        super().__init__(j, doc, loc)

        self.spec = j['$ref']
        uri, _, frag = self.spec.partition('#')
        self.uri = uri
        self.frag = frag

        self._target_doc = None
        self._target = None

    def descend(self, to):
        return self._deref().descend(to)

    def resolve(self):
        return self._deref().resolve()

    def _deref(self):
        try:
            return self._deref_unprotected()
        except Exception as e:
            err = format_exception(e)
            loc = self.loc.describe()
            msg = 'bad reference {} {}: {}'.format(repr(self.spec), loc, err)
            sys.stderr.write(msg + '\n')
            sys.exit(1)

    def _deref_unprotected(self):
        if self._target is None:
            if self._target_doc is None:
                doc = self.doc.load(self.uri) if self.uri else self.doc
                self._target_doc = doc
            node = self._target_doc.node()
            for el in frag_parse(self.frag):
                node = node.descend(el)
            self._target = node
        return self._target

class Array(Node):
    def descend(self, to):
        return Node.of(self.j[int(to)], self.doc, self.loc.descend(to))

    def resolve(self):
        return [
            Node.of(x, self.doc, self.loc.descend(str(i))).resolve()
            for x, i in enumerate(self.j)]

class Object(Node):
    def descend(self, to):
        return Node.of(self.j[to], self.doc, self.loc.descend(to))

    def resolve(self):
        return {
            k: Node.of(v, self.doc, self.loc.descend(k)).resolve()
            for k, v in self.j.items()}

class Document(object):
    def __init__(self, j, uri):
        self._node = Node.of(j, self, Location(uri))
        self._root = os.path.dirname(uri)

    def node(self):
        return self._node

    def root(self):
        return self._root

    def load(self, uri):
        fulluri = os.path.join(self.root(), uri)
        with open(fulluri, 'r') as f:
            j = json.load(f)
        return Document(j, fulluri)

class StdinDocument(Document):
    def __init__(self):
        self._node = None
        self._root = '.'

    def node(self):
        if self._node is None:
            self._node = Node.of(json.load(sys.stdin), self, StdinLocation())
        return self._node

if __name__ == '__main__':
    stdin = StdinDocument()
    args = sys.argv[1:]
    if len(args) == 0:
        args = ['#']
    for arg in args:
        node = Node.of({ '$ref': arg }, stdin, ArgvLocation())
        json.dump(node.resolve(), sys.stdout, indent=2)
        print()
