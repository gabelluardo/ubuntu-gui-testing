*** Settings ***
Documentation       Spawns a single prompt and replies to it

Resource            ${Z}/../prompting.resource

Test Tags           robot:exit-on-failure    # robocop: off=tag-with-reserved-word


*** Variables ***
${Z}    ${CURDIR}


*** Test Cases ***
Log In
    [Documentation]    Log in to desktop session
    Log In

Enable Prompting
    [Documentation]    Enable prompting
    Enable Prompting

Download Example File
    [Documentation]    Download example.com as html
    Open Firefox
    Open Example Domain
    Save File
    Allow Firefox Download Prompt
    Verify Download
