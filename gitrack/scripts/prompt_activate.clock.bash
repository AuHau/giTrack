#!/usr/bin/env bash


    function gitrack_status() {
        local slashes=${PWD//[^\/]/}
        local directory="$PWD"
        local repo=""
        for (( n=${#slashes}; n>0; --n ))
        do
          if [ -e "$directory/.git" ]
          then
            repo="$directory"
            break
          fi

          directory="$directory/.."
        done

        [[ ! ${repo} ]] && return 2 # No Git repo in the current folder's tree

        local repo_name=$(sed "s/\//_/g" <<<"$repo" | cut -b 2-)
        [[ ! -d "${GITRACK_DATA}/${repo_name}" ]] && return 2 # Unknown repo

        local gitrack_data="${GITRACK_DATA}/${repo_name}/status"
        [[ ! -e "${gitrack_data}" ]] && return 1 # Repo is known and initialized, but nothing is running

        start_time=$(cat ${gitrack_data})
        [[ ! ${start_time} ]] && return 1 # The status file is present but no time inside it

        elapsedseconds=$(expr $(date +%s) - ${start_time})

        if [[ $elapsedseconds -lt 3600 ]]; then
            echo $elapsedseconds | awk '{printf "%02d:%02d\n",int($1/60), int($1%60)}'
        else
            echo $elapsedseconds | awk '{printf "%d:%02d:%02d\n",int($1/3600), int(($1-int(($1/3600))*3600)/60), int(($1-int(($1/3600))*3600)%60)}'
        fi

        return 0
    }

    function gitrack_prompt() {
        current_time=$(gitrack_status)
        gitrack_exit_status=$?

        if [[ ${gitrack_exit_status} -eq 2 ]];
        then
            PS1="${_OLD_GITRACK_PS1}"
        else
            if [[ ${gitrack_exit_status} -eq 0 ]];
            then
                PS1="\e[0;32m${current_time}\e[m ${_OLD_GITRACK_PS1}"
            else
                PS1="\e[0;31m00:00\e[m ${_OLD_GITRACK_PS1}"
            fi
        fi

    }

    GITRACK_DATA="{{DATA_PATH}}"
    _OLD_GITRACK_PS1="$PS1"

    # TODO: [Feature/Low] Validation that PROMPT_COMMAND does not exists & handling existing one
    PROMPT_COMMAND=gitrack_prompt