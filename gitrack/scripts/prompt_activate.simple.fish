#!/usr/bin/env fish

set GITRACK_DATA '{{DATA_PATH}}'

functions -c fish_prompt _old_gitracks_fish_prompt

function gitrack_status
    set depth (math (string length (pwd)) - (string length (string replace -a '/' '' (pwd))))
    set repo ''
    set directory (pwd)

    for x in (seq $depth)
      if test -e "$directory/.git"
        set repo $directory
        break
      end

      set directory "$directory/.."
    end

    [ ! $repo ]; and return 2 # No Git repo in the current folder's tree

    set repo_name (string sub -s 2 (string replace -a '/' '_' $repo))
    [ ! -d $repo ]; and return 2 # Unknown repo

    set gitrack_data "$GITRACK_DATA/$repo_name/status"
    [ ! -e $gitrack_data ]; and return 1

    set start_time (cat $gitrack_data)
    [ ! $start_time ]; and return 1 # The status file is present but no time inside it

    return 0
end

function fish_prompt
    # Save the current $status, for fish_prompts that display it.
    set -l old_status $status

    gitrack_status
    set -l gitrack_status_exit $status

    if test $gitrack_status_exit -ne 2
        if test $gitrack_status_exit -eq 0
            set color 'green'
        else
            set color 'red'
        end

        printf '%s⬤ %s' (set_color $color) (set_color 'normal')
    end

    # Restore the original $status
    echo "exit $old_status" | source
    _old_gitracks_fish_prompt
end