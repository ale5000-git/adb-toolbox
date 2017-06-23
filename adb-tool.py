#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""ADB Toolbox"""

import sys
import os
import subprocess

__app__ = "ADB Toolbox"
__author__ = "ale5000"


def init():
    global SCRIPT_DIR, PREVIOUS_DIR, DUMB_MODE
    SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))

    sys.path.append(os.path.join(SCRIPT_DIR, "libs"))
    import atexit
    import pycompatlayer

    if sys.platform == "win32":
        os.system("TITLE "+__app__)

    # Activate Python compatibility layer
    pycompatlayer.fix_all()

    # Add tools folder to search path (used from subprocess)
    os.environ["PATH"] = SCRIPT_DIR+os.sep+"tools" + os.pathsep + os.environ.get("PATH", "")

    # Set constants (they won't be changed again)
    PREVIOUS_DIR = os.getcwd()
    DUMB_MODE = False
    if os.environ.get("TERM") == "dumb":
        DUMB_MODE = True

    # Register exit handler
    atexit.register(on_exit)


def on_exit():
    # Return to the previous working directory
    os.chdir(PREVIOUS_DIR)
    # Kill ADB server
    subprocess.check_call(["adb", "kill-server"])

    if sys.platform == "win32" and not DUMB_MODE:
        import msvcrt
        msvcrt.getch()  # Wait a keypress before exit (useful when the script is running from a double click)


def exit(error_code):
    if error_code != 0:
        print_(os.linesep+"ERROR CODE:", error_code)
    sys.exit(error_code)


def verify_dependencies():
    from distutils.spawn import find_executable

    def exec_exists(exec_name):
        if find_executable(exec_name) is not None:
            return True
        print_(os.linesep+"ERROR: Missing executable =>", exec_name)
        return False

    if not exec_exists("adb"):
        exit(65)


def debug(msg):
    print_("      DEBUG:", msg)


def warning(msg, first_line=True):
    if first_line:
        print_("      WARNING:", msg)
    else:
        print_("              ", msg)


def get_OS():
    import platform
    return platform.system()+" "+platform.release()


def display_info():
    print_(os.linesep+"-----------------------")
    print_("Name: "+__app__)
    print_("Author: "+__author__+os.linesep)


def input_byte(msg):
    print_(msg, end="", flush=True)
    if DUMB_MODE:
        print_()
        return ""
    try:
        val = sys.stdin.readline()
        # KeyboardInterrupt leave a "", instead an empty value leave a "\n"
        if val == "":
            import time
            time.sleep(0.02)  # Give some time for the exception to being caught
    except KeyboardInterrupt:
        raise EOFError
    else:
        return val.strip()[:1]


def user_question(msg, max_val, default_val=1, show_question=True):
    if show_question:
        print_(msg)
    try:
        val = input_byte("> ")
    except EOFError:
        print_(os.linesep+os.linesep+"Killed by the user, now exiting ;)")
        sys.exit(130)

    if(val == ""):
        print_("Used default value.")
        return default_val
    elif(val == "i"):
        display_info()
        return user_question(msg, max_val, default_val, True)

    try:
        val = int(val)
        if val > 0 and val <= max_val:
            return val
    except ValueError:
        pass

    print_("Invalid value, try again...")
    return user_question(msg, max_val, default_val, False)


def select_device():
    subprocess.check_output(["adb", "start-server"])
    devices = subprocess.check_output(["adb", "devices"]).decode("utf-8")
    if devices.count(os.linesep) <= 2:
        print_(os.linesep+"ERROR: No device detected! Please connect your device first.")
        exit(0)

    devices = devices.split(os.linesep)[1:-2]
    devices = [a.split("\t")[0] for a in devices]

    if len(devices) > 1:
        print_()
        question = "Enter id of device to target:"+os.linesep+os.linesep+"    "+(os.linesep+"    ").join([str(i)+" - "+a for i, a in zip(range(1, len(devices)+1), devices)])+os.linesep
        id = user_question(question, len(devices))
        chosen_device = devices[id-1]
    else:
        chosen_device = devices[0]
    return chosen_device


def root_adbd(chosen_device):
    print_(" *** Rooting adbd...")
    root_check = subprocess.check_output(["adb", "-s", chosen_device, "root"]).decode("utf-8")
    if root_check.find("root access is disabled") == 0 or root_check.find("adbd cannot run as root") == 0:
        print_(os.linesep+"ERROR: You do NOT have root or root access is disabled.")
        print_(os.linesep+"Enable it in Settings -> Developer options -> Root access -> Apps and ADB.")
        exit(80)
    debug(root_check.rstrip())
    subprocess.check_call(["adb", "-s", chosen_device, "wait-for-device"])


def enable_device_writing(chosen_device):
    root_adbd(chosen_device)
    remount_check = subprocess.check_output(["adb", "-s", chosen_device, "remount", "/system"]).decode("utf-8")
    debug(remount_check.rstrip())
    if("remount failed" in remount_check) and ("Success" not in remount_check):  # Do NOT stop with "remount failed: Success"
        print_(os.linesep+"ERROR: Remount failed.")
        exit(81)


init()
verify_dependencies()
chosen_device = select_device()

question = "MENU"+os.linesep+os.linesep+"    1 - Uninstall GApps / microG (minimal)"+os.linesep+"    2 - Exit"+os.linesep
action = user_question(question, 2, 2)

print_(os.linesep+" *** OS:", get_OS(), "("+sys.platform+")")
print_(" *** Selected device:", chosen_device)
print_(" *** Action:", action)


def uninstall_gapps():
    enable_device_writing(chosen_device)
    removal_list = [
        "/system/priv-app/GooglePartnerSetup.apk", "/system/priv-app/Phonesky.apk", "/system/priv-app/Vending.apk", "/system/priv-app/GoogleLoginService.apk", "/system/priv-app/GoogleServicesFramework.apk", "/system/priv-app/GsfProxy.apk", "/system/priv-app/GmsCore.apk", "/system/priv-app/NetworkLocation.apk",
        "/system/app/GooglePartnerSetup.apk", "/system/app/Phonesky.apk", "/system/app/Vending.apk", "/system/app/GoogleLoginService.apk", "/system/app/GoogleServicesFramework.apk", "/system/app/GsfProxy.apk", "/system/app/GmsCore.apk", "/system/app/NetworkLocation.apk"
    ]

    print_(" *** Uninstalling GApps / microG...")
    subprocess.check_output(["adb", "uninstall", "org.microg.gms.droidguard"])
    subprocess.check_output(["adb", "uninstall", "com.google.android.youtube"])
    subprocess.check_output(["adb", "uninstall", "com.android.vending"])
    subprocess.check_output(["adb", "uninstall", "com.google.android.gsf.login"])
    subprocess.check_output(["adb", "uninstall", "com.google.android.gsf"])
    subprocess.check_output(["adb", "uninstall", "com.google.android.gms"])
    subprocess.check_call(["adb", "shell", "rm", "-f", "/system/app/YouTube.apk"])
    subprocess.check_call(["adb", "shell", "rm", "-f"] + removal_list)


if action == 1:
    uninstall_gapps()
else:
    exit(0)

print_(" *** Done!")
