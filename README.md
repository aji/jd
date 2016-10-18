# `jd` BETA -- JSON dereferencer

**This is beta-level software. Do not expect quality or stability, but
feel free to be cautiously optimistic.**

Dereferences `$ref`-style references.

This is an implementation of the [JSON Reference][json-ref] and associated
[JSON Pointer][json-pointer] draft standards that resolves all references
statically.

[json-ref]: https://tools.ietf.org/html/draft-pbryan-zyp-json-ref-03
[json-pointer]: https://tools.ietf.org/html/draft-ietf-appsawg-json-pointer-04

# Usage

`jd` statically resolves references in JSON documents, outputting a plain,
reference-free JSON document. Command line arguments are interpreted as
JSON pointers, i.e. values you would put in a `$ref`. If the path portion
of a command line pointer is missing, then it's treated as a reference to
standard input. With no arguments, `jd` will simply resolve standard input.
In other words, the following invocations are all equivalent:

```
$ jd 'document.json#/fragment'
$ cat document.json | jd '#/fragment'
$ echo '{ "$ref": "document.json#/fragment" }' | jd
```

`jd` can follow references through other references. That is, if following a
reference leads to another reference, that reference will also be followed.

See the "Examples" section below for examples of `jd` usage. The tests in the
`test` directory are also useful as examples of both correct and incorrect
usage.

# Deviations from specifications

`jd` deviates from the JSON Reference and JSON Pointer standards in a few
ways, described here.

## Definition of a reference

The JSON reference specification describes a reference as simply being any JSON
object containing a `$ref` property with a string value. `jd` goes one step
further and requires that `$ref` be the *only* property in the object. This
allows you to force `jd` to ignore what would otherwise be a reference by
adding a separate dummy property:

```
{ "$ref": "something.json", "__ignore_this_ref": true }
```

This object will be left untouched.

If the object has only a `$ref` property and a `__jd_keep_ref` property, and the
value of `__jd_keep_ref` is `true`, then `jd` will delete the `__jd_keep_ref`
property while leaving the `$ref` property untouched. That is, this

```
{ "$ref": "something.json", "__jd_keep_ref": true }
```

becomes this

```
{ "$ref": "something.json" }
```

## Following JSON pointers

The rules for following a JSON pointer do not specify any interaction with JSON
references. A strict interpretation of the standard indicates that resolving a
pointer should never resolve a reference. Consider the following document.

```
$ echo '{ "$ref": "file.json" }' | jd '#/something'
```

According to the standard, this should result in an error, since the document
that `#/somesomething` points to (standard input) has no property `something`.
`jd`, however, would resolve the reference first, then check the resolved
document for a `something` property.

Relatedly, the JSON pointer specification defines a pointer to be a URI.
Although the `jd` source frequently uses the term `uri`, `jd` only ever resolves
these URIs as filenames. Support for complete URIs may be added in the future,
but only as an opt-in feature.

# Installation

Get `jd.py` in your `PATH` somehow. My favorite way is with a symlink:

```
$ git clone https://github.com/aji/jd
$ ln -s $PWD/jd/jd.py ~/local/bin/jd
$ export PATH="$HOME/local/bin:$PATH"
```

# Examples

For these examples, I'll be using the following files:

#### `users.json`

```
{
  "alex": {
    "name": "Alex Iadicicco",
    "city": { "$ref": "places.json#/states/wa/seattle" }
  }
}
```

#### `places.json`

```
{
  "states": {
    "wa": {
      "tacoma": { "$ref": "#/cities/tacoma" },
      "seattle": { "$ref": "#/cities/seattle" }
    }
  },
  "cities": {
    "tacoma": {
      "name": "Tacoma",
      "lat": "47.2529",
      "lon": "-122.4443"
    },
    "seattle": {
      "name": "Seattle",
      "lat": "47.6062",
      "lon": "-122.3321"
    }
  }
}
```

## Basic use

Running

```
jd users.json
```

Produces

```
{
  "alex": {
    "name": "Alex Iadicicco",
    "city": {
      "name": "Seattle",
      "lat": "47.6062",
      "lon": "-122.3321"
    }
  }
}
```

## Command line references

Running

```
jd places.json#/states
```

Produces

```
{
  "wa": {
    "tacoma": {
      "name": "Tacoma",
      "lat": "47.2529",
      "lon": "-122.4443"
    },
    "seattle": {
      "name": "Seattle",
      "lat": "47.6062",
      "lon": "-122.3321"
    }
  }
}
```

# Shortcomings

This software is very young and has many shortcomings. It usually will crash
instead of give a useful error message, and should **never** be used with
untrusted input.
