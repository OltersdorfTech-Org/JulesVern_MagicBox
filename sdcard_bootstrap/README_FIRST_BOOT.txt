JulesVern Magic Box — SD Card Bootstrap (Pi Zero 2 W)
====================================================

Purpose
- Make the first boot require only one command on the Pi after copying this folder onto the SD card's boot partition.

Contents
- install.sh — copies the repo out of /boot/firmware, then runs the full installer.

How to use (Windows drag-and-drop)
1) Download and extract the repo ZIP on your PC.
2) Copy the entire JulesVern_MagicBox folder (including this sdcard_bootstrap directory) to the SD card's boot/firmware partition (visible in File Explorer as a small FAT drive).
3) Safely eject the SD card and boot the Pi with it.
4) On the Pi, open a terminal and run one command:
   sudo /boot/firmware/JulesVern_MagicBox/sdcard_bootstrap/install.sh
5) Wait for the installer to finish. It will set up the virtual environment and systemd service, then print what to do next.

Notes
- The script copies the repo to /home/pi/JulesVern_MagicBox by default. Override with MAGICBOX_TARGET=/some/path if needed.
- Re-running the command is safe; it will refresh the install.
