set -x GITRACK_CMD '{{CMD_PATH}}'

functions -c fish_prompt _old_gitracks_fish_prompt

function fish_prompt
    # Save the current $status, for fish_prompts that display it.
    set -l old_status $status

    env $GITRACK_CMD > /dev/null
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