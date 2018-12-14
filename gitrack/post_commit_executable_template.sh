#!/usr/bin/env bash

CMD='{{CMD_PATH}}'

if $CMD init --check; then
    $CMD hooks post-commit
fi