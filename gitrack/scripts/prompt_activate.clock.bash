
function gitrack_prompt() {

    current_time="$(env ${GITRACK_CMD})"
    gitrack_exit_status="$?"

    if [[ ${gitrack_exit_status} -eq 2 ]];
    then
        export PS1="${_OLD_GITRACK_PS1}"
    else
        if [[ ${gitrack_exit_status} -eq 0 ]];
        then
            export PS1="\e[0;32m${current_time}\e[m ${_OLD_GITRACK_PS1}"
        else
            export PS1="\e[0;31m${current_time}\e[m ${_OLD_GITRACK_PS1}"
        fi
    fi

}

export GITRACK_CMD="{{CMD_PATH}}"
export _OLD_GITRACK_PS1="$PS1"
export -f gitrack_prompt

# TODO: [Feature/Low] Validation that PROMPT_COMMAND does not exists & handling existing one
export PROMPT_COMMAND=gitrack_prompt