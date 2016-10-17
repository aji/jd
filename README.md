# `jd` -- JSON dereferencer

Dereferences `$ref`-style references.

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
