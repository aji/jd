#!/bin/bash

root="$PWD/$(dirname "$0")"
jeq="$root/jeq.py"

cd "$root"

failed=0
for dir in "$root/test_"*; do
  cd "$dir"
  echo "$(basename "$dir")"
  if ! sh ./command.sh | "$jeq" ./output.json; then
    echo "  EXPECTED:"
    cat ./output.json | sed 's/^/    /'
    echo "  GOT:"
    sh ./command.sh | sed 's/^/    /'
    let failed=failed+1
  fi
done

if [ "$failed" != "0" ]; then
  echo "$failed test(s) failed"
  exit 1
fi
