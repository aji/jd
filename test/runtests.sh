#!/bin/bash

root="$PWD/$(dirname "$0")"
jeq="$root/jeq.py"

cd "$root"

export PATH="$root/bin:$PATH"

failed=0

for dir in "$root/test_"*; do
  cd "$dir"
  echo "$(basename "$dir")" -- "$(cat ./command.sh)"
  if ! sh ./command.sh 2>/dev/null | "$jeq" ./output.json; then
    echo "  EXPECTED:"
    cat ./output.json | sed 's/^/    /'
    echo "  GOT:"
    sh ./command.sh | sed 's/^/    /'
    let failed=failed+1
  fi
done

for dir in "$root/fail_"*; do
  cd "$dir"
  echo "$(basename "$dir")" -- "$(cat ./command.sh)"
  actual="/tmp/output.txt"
  if sh ./command.sh 2> "$actual" > /dev/null; then
    echo "  EXPECTED command to fail"
    let failed=failed+1
  else
    if [ "$(cat ./output.txt)" != "$(cat "$actual")" ]; then
      echo "  EXPECTED:"
      cat ./output.txt | sed 's/^/    /'
      echo "  GOT:"
      cat "$actual" | sed 's/^/    /'
      let failed=failed+1
    fi
  fi
done

if [ "$failed" != "0" ]; then
  echo "$failed test(s) failed"
  exit 1
fi
