## Walnut 8-Camera Capture GUI

A PyQt5 GUI to preview up to eight USB cameras and capture synchronized images for Front, Back, Left, Right, Top, Down, Additional1, Additional2.

### Install
```bash
python -m venv .venv
. .venv/Scripts/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Run

#### Method 1: Desktop Shortcut (Recommended)
Double-click the "Camera Capture" shortcut on your desktop.

#### Method 2: Batch File
Double-click `run_camera_capture.bat`

#### Method 3: Command Line
```bash
python main.py
```

### Usage
- Select detected camera indices for each role from the dropdowns.
- Click "Open All" to start previews.
- Enter an ID like 0001 (auto-pads). Optionally enable Auto Increment.
- Click "Capture All" to save images simultaneously into `images/<Role>/` as `0001_F.jpg`, `0001_B.jpg`, etc.
- Click "Close All" to release cameras.

### Notes
- During tests, you can assign only 2-3 cameras; unassigned roles are skipped.
- Naming suffix map: F, B, L, R, T, D, A1, A2.
- Each camera can only be assigned to one window to prevent conflicts.
- Default resolution attempts 1280x720; adjust in code if needed.
