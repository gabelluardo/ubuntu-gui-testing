*** Settings ***
Documentation       Shared resources for application testing

Resource            kvm.resource
Resource            ${Y}/common/common.resource


*** Variables ***
${Y}    ${CURDIR}


*** Keywords ***
Open Security Center
    [Documentation]    Open the security center
    Start Application    desktop-security-center
    Match Text    Security Center    60

Enable Prompting
    [Documentation]    Enable snap prompting in the security center
    BuiltIn.Sleep    5
    Move Pointer To ${Y}/generic/prompting-toggle-disabled.png
    EzClick
    Handle PolKit Prompt
    Match    ${Y}/generic/prompting-toggle-enabled.png    60

Handle PolKit Prompt
    [Documentation]    Handle a PolKit prompt
    Match Text    Authentication Required
    Type String    ubuntu
    Keys Combo    Return

Open Firefox
    [Documentation]    Open Firefox
    Start Application    firefox
    Match Text    Firefox    60

Open Example Domain
    [Documentation]    Open a new tab in Firefox and navigate to example.com
    Keys Combo    Ctrl    t
    Type String    example.com
    Keys Combo    Return
    Match Text    Example Domain 60

Save File
    [Documentation]    Download current website in Firefox
    Keys Combo    Ctrl    s
    Match Text    Save
    BuiltIn.Sleep    1
    Keys Combo    Return
    BuiltIn.Sleep    1

Allow Firefox Download Prompt
    [Documentation]    Give Firefox write access when downloading a file
    Match Text    Firefox wants to get write access
    Click LEFT Button On Allow always
    BuiltIn.Sleep    1

Verify Download
    [Documentation]    Verify successful download of a file in Firefox
    Click LEFT Button On ${Y}/generic/home/downloads.png
    Match Text    Completed 60

Focus Prompt
    [Documentation]    Focus the prompting-client UI
    Move Pointer To ${Y}/generic/shield-icon.png
    EzClick

Ensure No Prompts
    [Documentation]    Ensure there are no active prompts
    Ensure ${Y}/generic/shield-icon.png Does Not Match

Trigger First yq Prompt
    [Documentation]    Open a terminal, run yq on a test file and wait for a prompt
    Open Terminal
    Type String    echo 'a
    Keys Combo    Shift_L    ;
    Type String    1'
    Keys Combo    Shift_L    .
    Type String    a.yaml
    Keys Combo    Return
    Type String    yq a.yaml
    Keys Combo    Return
    Match Text    yq wants to get read access to a.yaml

Trigger Second yq Prompt
    [Documentation]    Open a terminal, run yq on a second test file and wait for another prompt
    Open Terminal
    Type String    echo 'b
    Keys Combo    Shift_L    ;
    Type String    2'
    Keys Combo    Shift_L    .
    Type String    b.yaml
    Keys Combo    Return
    Type String    yq b.yaml
    Keys Combo    Return
    Match Text    yq wants to get read access to b.yaml

Deny Second yq Prompt
    [Documentation]    Deny prompt for second yq command, verify that read access is denied
    Click LEFT Button On Deny once
    Match Text    Error: open b.yaml: permission denied
    Type String    exit
    Keys Combo    Return

Allow First yq Prompt
    [Documentation]    Allow the prompt for the first yq command, verify that the command succeeds
    Focus Prompt
    Click LEFT Button On Allow until logout
    Match Text    a: 1

Answer Both yq Prompts
    [Documentation]    Answer the prompt for the second yq command so that it also resolves the first prompt, verify that both commands succeed
    Click LEFT Button On More options
    Click LEFT Button On Everything in the
    Click LEFT Button On Allow
    Match Text    b: 2
    Type String    exit
    Keys Combo    Return
    Match Text    a: 1
    Ensure No Prompts

# imported from prompting-client

User Log In
    [Documentation]    Log in a given user with password
    [Arguments]    ${username}    ${password}
    Match Text    ${username}    30
    Keys Combo    Return
    Match Text    Password    30
    Type String    ${password}
    BuiltIn.Sleep    0.5
    Keys Combo    Return
    BuiltIn.Sleep    5

Clear Terminal
    [Documentation]    Clear terminal from previous commands
    Type String    clear
    Keys Combo    Return
    Match Text    ${PROMPT}    30

Delete Request Rules
    [Documentation]    Delete current request rules for prompting
    Open Terminal
    Run Sudo Command In Terminal
    ...    echo '{"action": "remove", "selector": {"interface": "camera"}}' | sudo snap debug api -X POST -H 'Content-Type: application/json' "/v2/interfaces/requests/rules?user-id=$UID"
    Match Text    ${PROMPT}    30
    Close Terminal

Run Simple Command
    [Documentation]    Run command in terminal without verifying the exit status
    [Arguments]    ${cmd}
    Type String    ${cmd}
    Keys Combo    Return

Press Button
    [Documentation]    Press action button on the prompt
    [Arguments]    ${text}
    Click LEFT Button On ${text}

Cheese Prompt Is Present
    [Documentation]    Find camera prompt for "cheese"
    Match Text    Allow cheese to access your camera?    30

Cheese No Device
    [Documentation]    Find "cheese" application open with no device message
    Match    ${Y}/generic/camera/cheese_no_device.png    30

Cheese With Video
    [Documentation]    Find "cheese" application open with fake test video
    Match    ${Y}/generic/camera/cheese_with_video.png    30
