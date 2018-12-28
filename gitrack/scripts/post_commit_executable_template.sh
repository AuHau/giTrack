#!/usr/bin/env bash

CMD='{{CMD_PATH}}'

if env $CMD init --check; then
    env $CMD hooks post-commit
fi