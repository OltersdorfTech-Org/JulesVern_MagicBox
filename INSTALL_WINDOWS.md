# INSTALL_WINDOWS.md
Install Jules Verne Magic Box on a Raspberry Pi Zero 2 W (Windows)

This guide walks you through preparing a microSD card on **Windows**, performing a first boot on a **Raspberry Pi Zero 2 W**, and installing the **Jules Verne Magic Box** software as a managed system service.

This guide assumes **no SSH is required initially**. A temporary on-device desktop can be used for setup.

---

## What you will end with

- Raspberry Pi OS (64-bit) installed
- Wi-Fi configured
- Jules Verne Magic Box project files present on the SD card
- Software installed as a system service
- Web UI accessible from another device on your network
- Logs exported to a Windows-readable location on the SD card

---

## What you need

### Hardware
- Raspberry Pi Zero 2 W
- microSD card (16 GB or larger recommended)
- microSD card reader for Windows PC
- USB power cable
- Mini-HDMI adapter + monitor (temporary setup)
- USB keyboard + mouse (temporary setup)

### Windows software
- Raspberry Pi Imager (official)
- Optional: WinSCP or File Explorer

### Network
- 2.4 GHz Wi-Fi network
- Wi-Fi SSID and password

---

## Step 1 — Install Raspberry Pi Imager (Windows)

1. Download Raspberry Pi Imager from the official Raspberry Pi website
2. Install and launch the application

---

## Step 2 — Prepare the SD card (OS + headless settings)

1. Insert the microSD card into your Windows PC
2. Open Raspberry Pi Imager
3. Click **CHOOSE DEVICE** → Raspberry Pi Zero 2 W
4. Click **CHOOSE OS** → Raspberry Pi OS (64-bit)
5. Click **CHOOSE STORAGE** → your SD card

### Configure basic options

Open **Advanced Options** (gear icon or Ctrl + Shift + X):

- Set **hostname** (example: `jv-magicbox`)
- Set **username and password**
- Configure **Wi-Fi**
- Enable **SSH** (optional, can be skipped)
- Set locale/timezone

Write the card and safely eject it.

> Important: The SD card contains **only Raspberry Pi OS** at this point.

---

## Step 3 — First boot (desktop mode)

1. Insert the SD card into the Raspberry Pi
2. Connect monitor, keyboard, and mouse
3. Apply power via USB
4. Wait for the Raspberry Pi desktop to appear

This first boot initializes the OS only. Project LEDs are **not meaningful yet**.

---

## Step 3.5 — Get the project code onto the Pi (CRITICAL STEP)

You must now place the **Jules Verne Magic Box project files onto the Pi’s SD card**.

### Option A — Download from GitHub using the Pi’s browser

1. On the Pi desktop, open **Chromium**
2. Go to:
   https://github.com/OltersdorfTech-Org/JulesVern_MagicBox
3. Click **Code → Download ZIP**
4. Open the **Downloads** folder
5. Right-click the ZIP file → **Extract Here**
6. Move the extracted `JulesVern_MagicBox` folder to:
   - `/home/<username>/`

---

### Option B — Copy from Windows using the SD card (NO NETWORK REQUIRED)

1. Power off the Pi
2. Remove the SD card and insert it into your Windows PC
3. Open the SD card’s **Linux partition** using a Linux-capable reader or tool
4. Copy the entire `JulesVern_MagicBox` folder to:
   - `/home/<username>/`
5. Safely eject the SD card and return it to the Pi
6. Power the Pi back on

---

## Step 4 — Find the Pi’s IP address (GUI method)

On the Pi desktop:

### Method A — Network icon

1. Click the **network icon** (top-right corner)
2. Select **Connection Information**
3. Write down the IPv4 address (example: `192.168.1.42`)

### Method B — Terminal (GUI)

1. Open **Terminal**
2. Run:
   ```bash
   hostname -I
   ```

---

## Step 5 — Install the Magic Box software

Open **Terminal** on the Pi desktop:

```bash
cd ~/JulesVern_MagicBox/src
chmod +x installer.sh
sudo ./installer.sh
```

---

## Step 6 — Verify the service

```bash
sudo systemctl status magicbox.service --no-pager
```

Additional service commands:

```bash
sudo systemctl restart magicbox.service
sudo journalctl -u magicbox.service -n 200 --no-pager
ls -la /var/log/magicbox/
ls -la /boot/firmware/
```

Expected:
- Active (running)

---

## Step 7 — Access the Web UI (from another device)

Do NOT use a browser on the Pi (low RAM).

From a phone, laptop, or desktop on the same network, open:

- http://<pi_ip_address>:5000/  
or  
- http://<hostname>.local:5000/

Example:
- http://192.168.1.42:5000/

---

## Step 8 — Export logs to Windows-readable storage

In the web UI, click **Export Logs**. The service runs as root and writes logs to:

```
/boot/firmware/MAGICBOX_LOGS/
```

This includes `magicbox.log`, `installer.log`, and `export_manifest.txt`.

### Read logs on Windows

1. Shut down the Pi
2. Remove the SD card
3. Insert into Windows
4. Open the **boot** drive
5. Open `MAGICBOX_LOGS/`

---

## Uninstall

```bash
cd ~/JulesVern_MagicBox/src
chmod +x uninstall.sh
sudo ./uninstall.sh
```

---

## Next steps

- WIRING_GUIDE.md
- USAGE_GUIDE.md
