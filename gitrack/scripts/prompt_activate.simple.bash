
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

    return 0
}

function gitrack_prompt() {
    gitrack_status
    gitrack_exit_status=$?

    if [[ ${gitrack_exit_status} -eq 2 ]];
    then
        export PS1="${_OLD_GITRACK_PS1}"
    else
        if [[ ${gitrack_exit_status} -eq 0 ]];
        then
            export PS1="\e[0;32m⬤\e[m ${_OLD_GITRACK_PS1}"
        else
            export PS1="\e[0;31m⬤\e[m ${_OLD_GITRACK_PS1}"
        fi
    fi
}

export GITRACK_DATA="{{DATA_PATH}}"
export _OLD_GITRACK_PS1="$PS1"
export -f gitrack_prompt
export -f gitrack_status

# TODO: [Feature/Low] Validation that PROMPT_COMMAND does not exists & handling existing one
export PROMPT_COMMAND=gitrack_prompt