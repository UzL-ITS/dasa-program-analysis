#!/bin/bash

cd "$(dirname "$0")"
output="$("bash" "run_dasa.sh" "SUTs/Smoketest1")"
if echo "$output" | grep -q "DASA_VERDICT: VIOLATION"; then
    echo "$output"
else
    exit 1
fi

output="$("bash" "run_dasa.sh" "SUTs/Smoketest2")"
if echo "$output" | grep -q "DASA_VERDICT: VIOLATION"; then
    echo "$output"
else
    exit 1
fi