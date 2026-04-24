*** Settings ***
Documentation       Tests for snap-tpmctl

Library             String
Resource            ${Z}/../snap-tpmctl.resource

Test Tags           robot:exit-on-failure    # robocop: off=tag-with-reserved-word


*** Variables ***
${Z}            ${CURDIR}

${DIRECTORY}    /media/my-vol


*** Test Cases ***
Log In
    [Documentation]    Log in to desktop session
    Log In

Install snap-tpmctl
    [Documentation]    Install the snap-tpmctl snap
    Install Snap Package    snap-tpmctl

Print Status
    [Documentation]    Print TPM/FDE status
    Open Terminal
    Run Sudo Command In Terminal    sudo snap-tpmctl status
    Match Text    ACTIVE

Mount LUKS Volume With Fail
    [Documentation]    Mount a LUKS volume portected with a passphrase
    Run Command With Prompt    sudo snap-tpmctl mount-volume ${DEVICE} test
    Match Text    unable to create directory

Mount LUKS Volume
    [Documentation]    Mount a LUKS volume portected with a passphrase
    Run Command With Prompt    sudo snap-tpmctl mount-volume ${DEVICE} ${DIRECTORY}
    Answer Prompt    Enter recovery key:    ${RECOVERY_KEY}
    BuiltIn.Sleep    3
    Run Simple Command    clear && lsblk | grep ${DIRECTORY}
    BuiltIn.Sleep    1
    Match Text    crypt ${DIRECTORY}    10

Unmount LUKS Volume
    [Documentation]    Unmount a LUKS volume
    Run Command In Terminal    sudo snap-tpmctl unmount-volume ${DIRECTORY}
    Run Simple Command    clear && lsblk | grep ${DIRECTORY}
    BuiltIn.Sleep    1
    Run Simple Command    echo $?
    Match Text    1

Unmount LUKS Volume With Fail
    [Documentation]    Unmount a LUKS volume
    Run Simple Command   clear && sudo snap-tpmctl unmount-volume ${DIRECTORY}
    Match Text    the mount point doesn't exist
