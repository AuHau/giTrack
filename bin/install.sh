#!/usr/bin/env bash

# Installer script v1.0
# =====================
# Script that will install command from repo hosted on GitHub and its latest release.
# It will take the build command that is attached as Asset to the GitHub's release,
# download it and store it to the configured destination

set -e

#####################
## Config

# Repo name from where will be the command downloaded from
REPO_NAME="auhau/gitrack"

# Name of resulting command to be installed
CMD_NAME="gitrack"

# Name of release's asset that will be downloaded; platform name will be appended
DOWNLOAD_FILE_NAME_BASE=${CMD_NAME}

# Place where the command will be installed
DESTINATION="/usr/local/bin"

#####################
## Helpers

echoerr() { cat <<< "$@" 1>&2; }

get_latest_release() {
  curl --silent "https://api.github.com/repos/$1/releases/latest" |
    grep '"tag_name":' |
    sed -E 's/.*"([^"]+)".*/\1/'
}

fetch_pex(){
    platform=""
    unamestr=$(uname)
    if [[ "$unamestr" == "Linux" ]]; then
       platform="linux"
    elif [[ "$unamestr" == "Darwin" ]]; then
       platform="macosx"
    else
        echoerr "Unsupported platform!"
        exit 1
    fi
    platform="${platform}-x86_64"

    version=$1
    destination=$2

    url="https://github.com/${REPO_NAME}/releases/download/${version}/${DOWNLOAD_FILE_NAME_BASE}.${platform}"
    curl --silent -L ${url} > ${destination}
}

#####################
## Main code

version=$(get_latest_release ${REPO_NAME})
tmp_destination="/tmp/${CMD_NAME}"

echo "Downloading '${CMD_NAME}' in latest version ${version}"
fetch_pex ${version} ${tmp_destination}
chmod +x ${tmp_destination}

echo "Installing it to: ${DESTINATION}"

if [[ -e "${DESTINATION}/${CMD_NAME}" ]]; then
    echo "Detected previous version; it will be rewritten."
fi

sudo cp ${tmp_destination} "${DESTINATION}/${CMD_NAME}"

echo "Successfully installed!"