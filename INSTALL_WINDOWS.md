# INSTALL_WINDOWS.md  
**Install Jules Verne Magic Box on a Raspberry Pi Zero 2 W (Windows, beginner-friendly)**

This guide walks you through preparing a microSD card on **Windows** using **Raspberry Pi Imager**, then booting a **Raspberry Pi Zero 2 W** into a headless setup (no monitor or keyboard required after install).

You will end with:
- A Pi running Raspberry Pi OS (64-bit)
- Wi-Fi configured
- SSH enabled
- The Magic Box software installed as a system service
- A clear visual confirmation of system health via the Status LED

---

## What you need

### Hardware
- Raspberry Pi **Zero 2 W**
- microSD card (16 GB or larger recommended)
- microSD card reader for your Windows PC
- USB power cable (wall adapter or battery pack)
- *(Optional for setup only)* keyboard, mouse, monitor

### Windows software
- **Raspberry Pi Imager** (official)
- *(Optional)* Windows Terminal or PuTTY for SSH

### Network
- 2.4 GHz Wi-Fi network
- Wi-Fi name (SSID) and password

---

## Step 1 — Install Raspberry Pi Imager (Windows)

1. Download **Raspberry Pi Imager** from the official Raspberry Pi website.
2. Install and launch the application.

---

## Step 2 — Prepare the SD card (OS + headless settings)

1. Insert the microSD card into your Windows PC.
2. Open **Raspberry Pi Imager**.
3. Click **CHOOSE DEVICE**
   - Select **Raspberry Pi Zero 2 W**
4. Click **CHOOSE OS**
   - Select **Raspberry Pi OS (64-bit)**  
     *(This project targets Raspberry Pi OS 64-bit, Debian Trixie–based.)*
5. Click **CHOOSE STORAGE**
   - Select your microSD card

---

### Configure headless options (IMPORTANT)

Before writing the card:

1. Open **Advanced Options**
   - Click the **gear icon**  
   - Or press **Ctrl + Shift + X**

Enable and configure the following:

#### Set hostname
- Example: `jv-magicbox`

#### Set username and password
- Choose a username and password you will remember
- Write them down

#### Configure Wi-Fi
- Enter your Wi-Fi SSID and password
- Set the correct Wi-Fi country

#### Enable SSH
- Enable **SSH**
- Select **password authentication**

#### Locale (recommended)
- Time zone
- Keyboard layout

2. Click **SAVE**
3. Click **WRITE**
4. Wait for the write to complete
5. Safely eject the SD card

---

## Step 3 — First boot

1. Insert the SD card into the Raspberry Pi Zero 2 W.
2. Connect power via USB.

The first boot may take several minutes.

### Verifying boot via Status LED
Once wired (see `WIRING_GUIDE.md`):

- Booting shows a repeating blink pattern
- A healthy system eventually indicates **Ready**
- Errors are shown via repeating blink codes

*(If LEDs are not yet wired, continue using SSH.)*

---

## Step 4 — Connect via SSH

### Option A — Hostname (recommended)

```bash
ssh <username>@<hostname>.local
```

Example:
```bash
ssh pi@jv-magicbox.local
```

---

### Option B — IP address

1. Check your router for connected devices
2. Find the Pi by hostname or “raspberrypi”
3. Connect using the IP address:

```bash
ssh <username>@192.168.x.x
```

---

## Step 5 — Update the Pi (recommended)

```bash
sudo apt update
sudo apt upgrade -y
```

---

## Step 6 — Install the Magic Box software

### Get the code onto the Pi

```bash
sudo apt install -y git
git clone <REPO_URL_HERE>
cd JulesVern_MagicBox
```

Replace `<REPO_URL_HERE>` with your GitHub repository URL.

### Run the installer

```bash
cd src
chmod +x installer.sh
sudo ./installer.sh
```

---

## Step 7 — Verify the service

```bash
sudo systemctl status magicbox.service --no-pager
```

---

## Step 8 — Access the Web UI

Open a browser on the same network:

```text
http://<hostname>.local
```

or

```text
http://<pi_ip_address>
```

---

## Step 9 — Export logs

Logs can be exported to:

```text
/boot/firmware/
```

This location is readable on Windows.

---

## Uninstall (if needed)

```bash
cd src
chmod +x uninstall.sh
sudo ./uninstall.sh
```

---

## Next steps

- Proceed to **WIRING_GUIDE.md**
- Then read **USAGE_GUIDE.md**
