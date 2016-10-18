#!/usr/bin/env python3

# Copyright (c) 2016, Alex Iadicicco
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its contributors
#    may be used to endorse or promote products derived from this software
#    without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from collections import OrderedDict
import json
import os
import sys

def is_ref(node):
    return isinstance(node, type({})) \
        and list(node.keys()) == ['$ref'] \
        and isinstance(node['$ref'], type(''))

def frag_unesc(s):
    return s\
        .replace('~1', '/')\
        .replace('~0', '~')

def frag_esc(s):
    return s\
        .replace('~', '~0')\
        .replace('/', '~1')

def frag_parse(s):
    if s == '':
        return []
    if not s.startswith('/'):
        raise ValueError('invalid fragment identifier: ' + repr(s))
    return [frag_unesc(x) for x in s[1:].split('/')]

def json_load(f):
    return json.load(f, object_pairs_hook=OrderedDict)

def format_exception(e):
    if isinstance(e, RecursionError):
        return 'maximum recursion depth exceeded'
    if isinstance(e, FileNotFoundError):
        return '{}: {}'.format(e.strerror, e.filename)
    if isinstance(e, ValueError):
        return str(e)
    return '{}: {}'.format(type(e).__name__, str(e))

class RefError(object):
    def __init__(self, ref, exc):
        self.ref = ref
        self.exc = exc

    def format(self):
        if isinstance(self.exc, json.JSONDecodeError):
            return 'error reading {}: {}'.format(self.ref.target_uri(), str(self.exc))
        else:
            err = format_exception(self.exc)
            loc = self.ref.loc.describe()
            return 'bad reference {} {}: {}'.format(repr(self.ref.spec), loc, err)

    def write(self, f):
        f.write(self.format() + '\n')

class ResolverContext(object):
    def __init__(self):
        self._errors = []

    def assert_no_errors(self):
        if len(self._errors) == 0:
            return
        for err in self._errors:
            err.write(sys.stderr)
        sys.exit(1)

    def add_ref_error(self, ref, exc):
        self._errors.append(RefError(ref, exc))

class Location(object):
    def __init__(self, uri, at=[]):
        self.uri = uri
        self.at = at
    def describe(self):
        frag = '/'.join(frag_esc(x) for x in [''] + self.at)
        return 'at {}#{}'.format(self.uri, frag)
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

    def descend(self, ctx, to):
        raise ValueError('cannot descend into a value')

    def resolve(self, ctx):
        return self.j

class ErrNode(Node):
    def __init__(self):
        super().__init__(None, None, None)

    def descend(self, ctx, to):
        return self

    def resolve(self, ctx):
        return "(internal error)"

class Reference(Node):
    def __init__(self, j, doc, loc):
        super().__init__(j, doc, loc)

        self.spec = j['$ref']
        uri, _, frag = self.spec.partition('#')
        self.uri = uri
        self.frag = frag

        self._target_doc = None
        self._target = None

    def descend(self, ctx, to):
        return self._deref(ctx).descend(ctx, to)

    def resolve(self, ctx):
        return self._deref(ctx).resolve(ctx)

    def _deref(self, ctx):
        try:
            return self._deref_unprotected(ctx)
        except Exception as e:
            ctx.add_ref_error(self, e)
            return ErrNode()

    def _deref_unprotected(self, ctx):
        if self._target is None:
            if self._target_doc is None:
                doc = self.doc.load(self.uri) if self.uri else self.doc
                self._target_doc = doc
            node = self._target_doc.node()
            for el in frag_parse(self.frag):
                node = node.descend(ctx, el)
            self._target = node
        return self._target

    def target_uri(self):
        return self.uri if self.uri else self.doc.uri()

class Array(Node):
    def descend(self, ctx, to):
        return Node.of(self.j[int(to)], self.doc, self.loc.descend(to))

    def resolve(self, ctx):
        return [
            Node.of(x, self.doc, self.loc.descend(str(i))).resolve(ctx)
            for i, x in enumerate(self.j)]

class Object(Node):
    def descend(self, ctx, to):
        return Node.of(self.j[to], self.doc, self.loc.descend(to))

    def resolve(self, ctx):
        return OrderedDict(
            (k, Node.of(v, self.doc, self.loc.descend(k)).resolve(ctx))
            for k, v in self.j.items())

class Document(object):
    def __init__(self, j, uri):
        self._uri = uri
        self._node = Node.of(j, self, Location(uri))
        self._root = os.path.dirname(uri)

    def uri(self):
        return self._uri

    def node(self):
        return self._node

    def root(self):
        return self._root

    def load(self, uri):
        fulluri = os.path.join(self.root(), uri)
        with open(fulluri, 'r') as f:
            j = json_load(f)
        return Document(j, fulluri)

class StdinDocument(Document):
    def __init__(self):
        self._uri = 'standard input'
        self._node = None
        self._root = '.'

    def node(self):
        if self._node is None:
            self._node = Node.of(json_load(sys.stdin), self, StdinLocation())
        return self._node

if __name__ == '__main__':
    stdin = StdinDocument()
    args = sys.argv[1:]
    if len(args) == 0:
        args = ['#']
    ctx = ResolverContext()
    results = []
    for arg in args:
        node = Node.of({ '$ref': arg }, stdin, ArgvLocation())
        results.append(node.resolve(ctx))
    ctx.assert_no_errors()
    for result in results:
        json.dump(result, sys.stdout, indent=2)
        print()
