#!/usr/bin/env fish

set -e GITRACK_DATA

functions -e fish_prompt
functions -c _old_gitracks_fish_prompt fish_prompt
functions -e _old_gitracks_fish_prompt