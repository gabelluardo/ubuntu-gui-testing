*** Settings ***
Documentation   Basic tests for the prompting-client snap

Resource        ${Z}/../prompting-client.resource

Test Tags       robot:exit-on-failure    # robocop: off=tag-with-reserved-word


*** Variables ***
${Z}    ${CURDIR}


*** Test Cases ***
Setup
    [Documentation]         Use rapidocr rather than tesseract-ocr in yarf
    Set Ocr Method    rapidocr

System Log In
    [Documentation]         Log in to desktop environment
    User Log In    u    u

Prepare Test Enviroment
    [Documentation]         Prepare test enviroment
    Install Snap Package    cheese
    Install Debian Package    gstreamer1.0-tools
    Delete Request Rules
    Open Terminal
    Run Sudo Command In Terminal    sudo modprobe v4l2loopback devices=1 video_nr=0 exclusive_caps=1 && sudo snap set system experimental.apparmor-prompting=true
    Run Simple Command    gst-launch-1.0 videotestsrc ! videoconvert ! v4l2sink device=/dev/video0
    BuiltIn.Sleep    2

Deny Once
    [Documentation]         Deny access to camera interface
    Start Application    cheese
    Cheese Prompt Is Present
    Press Button    Deny once
    # The first attempt will spawn 3 prompts
    Cheese Prompt Is Present
    Press Button    Deny once
    Cheese Prompt Is Present
    Press Button    Deny once
    Cheese No Device
    Close Application
    BuiltIn.Sleep    2

Allow Until Logout
    [Documentation]         Allow access to camera interface until logout
    Start Application    cheese
    Cheese Prompt Is Present
    Press Button    Allow until logout
    Cheese With Video
    Close Application
    BuiltIn.Sleep    2

No Prompt
    [Documentation]         Verify no prompt is shown due the "Allow Until Logout"
    Start Application    cheese
    Cheese With Video
    Close Application
    BuiltIn.Sleep    2

Cleanup Test Enviroment
    [Documentation]         Clean up system state
    ${combo}    Create List    Control_L    c
    Keys Combo    ${combo}
    Close Terminal
