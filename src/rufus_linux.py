#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rufus for Linux - Native Port
Exact UI Replica using CustomTkinter
Functional: Uses dd, mkfs, lsblk
Requires Root: Handled via pkexec/gksudo in launcher
"""
import os, sys, subprocess, threading, glob

try:
    import customtkinter as ctk
    from tkinter import filedialog, messagebox
except ImportError:
    print("Error: customtkinter missing. Install via: pip3 install customtkinter --break-system-packages")
    sys.exit(1)

APP_NAME = "Rufus 4.4 (Linux)"
WIDTH, HEIGHT = 460, 560
COLOR_BG = "#f0f0f0"
COLOR_FRAME = "#d9d9d9"
COLOR_BTN_NORMAL = "#e1e1e1"
COLOR_BTN_PRIMARY = "#0078d7"
COLOR_PROGRESS_BAR = "#00cc00"


class RufusApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(f"{APP_NAME}")
        self.geometry(f"{WIDTH}x{HEIGHT}")
        self.resizable(False, False)
        self.configure(fg_color=COLOR_BG)
        self.font_normal = ("Arial", 9)
        self.font_title = ("Arial", 10, "bold")

        self.devices = []
        self.selected_device = None
        self.image_path = None
        self.is_root = (os.geteuid() == 0)

        self._create_ui()
        self._refresh_devices()

        if not self.is_root:
            self.lbl_status.configure(
                text="WARNING: not running as root - disk operations will fail"
            )

    def _create_ui(self):
        main_frame = ctk.CTkFrame(self, fg_color=COLOR_BG, border_width=0)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Device Selection
        ctk.CTkLabel(main_frame, text="Device:", font=self.font_normal, anchor="w").pack(fill="x", pady=(0, 2))
        self.device_var = ctk.StringVar(value="Select a device...")
        self.combo_device = ctk.CTkOptionMenu(main_frame, variable=self.device_var, values=[],
                                              font=self.font_normal, button_color=COLOR_BTN_NORMAL,
                                              command=lambda x: self._on_device_select(x))
        self.combo_device.pack(fill="x", pady=(0, 10))

        # Boot Selection Frame
        frame_boot = ctk.CTkFrame(main_frame, fg_color=COLOR_FRAME, border_width=1, border_color="#999999")
        frame_boot.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(frame_boot, text="Boot selection", font=self.font_title, anchor="w").pack(fill="x", padx=5, pady=5)
        self.boot_var = ctk.StringVar(value="Disk or ISO image (Please select)")
        ctk.CTkOptionMenu(frame_boot, variable=self.boot_var, values=["Disk or ISO image (Please select)", "FreeDOS", "ReactOS"],
                          font=self.font_normal, button_color=COLOR_BTN_NORMAL).pack(fill="x", padx=5, pady=(0, 5))
        ctk.CTkButton(frame_boot, text="SELECT", width=80, height=25, font=self.font_normal,
                      fg_color=COLOR_BTN_NORMAL, text_color="#000", hover_color="#d0d0d0",
                      command=self._browse_image).pack(pady=5)
        self.lbl_image = ctk.CTkLabel(frame_boot, text="", font=("Arial", 8), anchor="w", wraplength=400)
        self.lbl_image.pack(fill="x", padx=5, pady=(0, 5))

        # Image Options (Visual only for now)
        frame_img_opt = ctk.CTkFrame(main_frame, fg_color=COLOR_FRAME, border_width=1, border_color="#999999")
        frame_img_opt.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(frame_img_opt, text="Image Option", font=self.font_title, anchor="w").pack(fill="x", padx=5, pady=5)
        ctk.CTkOptionMenu(frame_img_opt, values=["Standard Windows installation", "Windows To Go"],
                          font=self.font_normal, button_color=COLOR_BTN_NORMAL, state="disabled").pack(fill="x", padx=5, pady=(0, 5))

        # Partition Scheme
        frame_part = ctk.CTkFrame(main_frame, fg_color=COLOR_FRAME, border_width=1, border_color="#999999")
        frame_part.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(frame_part, text="Partition scheme", font=self.font_title, anchor="w").pack(fill="x", padx=5, pady=5)
        self.part_var = ctk.StringVar(value="MBR")
        self.combo_part = ctk.CTkOptionMenu(frame_part, variable=self.part_var, values=["MBR", "GPT"],
                          font=self.font_normal, button_color=COLOR_BTN_NORMAL, command=self._update_target)
        self.combo_part.pack(fill="x", padx=5, pady=(0, 5))
        ctk.CTkLabel(frame_part, text="Target system", font=self.font_normal, anchor="w").pack(fill="x", padx=5, pady=(2, 0))
        self.lbl_target = ctk.CTkLabel(frame_part, text="BIOS (or UEFI-CSM)", font=self.font_normal, anchor="w")
        self.lbl_target.pack(fill="x", padx=5, pady=(0, 5))

        # File System
        frame_fs = ctk.CTkFrame(main_frame, fg_color=COLOR_FRAME, border_width=1, border_color="#999999")
        frame_fs.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(frame_fs, text="File system", font=self.font_title, anchor="w").pack(fill="x", padx=5, pady=5)
        self.fs_var = ctk.StringVar(value="FAT32")
        ctk.CTkOptionMenu(frame_fs, variable=self.fs_var, values=["FAT32", "NTFS", "ext4"],
                          font=self.font_normal, button_color=COLOR_BTN_NORMAL).pack(fill="x", padx=5, pady=(0, 5))
        ctk.CTkLabel(frame_fs, text="Cluster size", font=self.font_normal, anchor="w").pack(fill="x", padx=5, pady=(2, 0))
        ctk.CTkLabel(frame_fs, text="Default", font=self.font_normal, anchor="w").pack(fill="x", padx=5, pady=(0, 5))

        # Format Options
        frame_opt = ctk.CTkFrame(main_frame, fg_color=COLOR_FRAME, border_width=1, border_color="#999999")
        frame_opt.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(frame_opt, text="Format Options", font=self.font_title, anchor="w").pack(fill="x", padx=5, pady=5)
        self.vol_var = ctk.StringVar(value="MyUSB")
        ctk.CTkEntry(frame_opt, textvariable=self.vol_var, font=self.font_normal, height=25).pack(fill="x", padx=5, pady=(0, 5))
        ctk.CTkCheckBox(frame_opt, text="Quick format", font=self.font_normal, variable=ctk.BooleanVar(value=True)).pack(anchor="w", padx=5)
        ctk.CTkCheckBox(frame_opt, text="Create extended label and icon files", font=self.font_normal, variable=ctk.BooleanVar(value=True)).pack(anchor="w", padx=5)

        # Progress Bar
        self.progress = ctk.CTkProgressBar(main_frame, mode='determinate', progress_color=COLOR_PROGRESS_BAR, fg_color="#ffffff")
        self.progress.pack(fill="x", pady=(10, 5))
        self.progress.set(0)
        self.lbl_status = ctk.CTkLabel(main_frame, text="READY", font=self.font_normal, anchor="w")
        self.lbl_status.pack(fill="x", pady=(0, 10))

        # Buttons
        btn_frame = ctk.CTkFrame(main_frame, fg_color=COLOR_BG, border_width=0)
        btn_frame.pack(fill="x")
        ctk.CTkButton(btn_frame, text="CLOSE", height=40, font=("Arial", 10, "bold"),
                      fg_color=COLOR_BTN_NORMAL, text_color="#000", hover_color="#d0d0d0",
                      command=self.quit).pack(side="right", padx=5)
        self.btn_start = ctk.CTkButton(btn_frame, text="START", height=40, font=("Arial", 10, "bold"),
                                       fg_color=COLOR_BTN_PRIMARY, hover_color="#0063b1",
                                       command=self._start_process)
        self.btn_start.pack(side="right", padx=5)

    def _update_target(self, val=None):
        if self.part_var.get() == "GPT":
            self.lbl_target.configure(text="UEFI (non CSM)")
        else:
            self.lbl_target.configure(text="BIOS (or UEFI-CSM)")

    def _refresh_devices(self):
        try:
            res = subprocess.run(["lsblk", "-ndo", "NAME,SIZE,TYPE"], capture_output=True, text=True, check=True)
            devs = []
            for line in res.stdout.strip().split('\n'):
                parts = line.split()
                if len(parts) >= 3 and parts[2] == 'disk' and (parts[0].startswith('sd') or parts[0].startswith('nvme') or parts[0].startswith('mmcblk')):
                    devs.append({'path': f"/dev/{parts[0]}", 'display': f"/dev/{parts[0]} ({parts[1]})"})
            self.devices = devs
            vals = [d['display'] for d in devs] or ["No removable devices found"]
            self.combo_device.configure(values=vals)
            if devs and (not self.selected_device or self.selected_device not in devs):
                self.selected_device = devs[0]
                self.device_var.set(devs[0]['display'])
            elif not devs:
                self.selected_device = None
                self.device_var.set("No removable devices found")
        except Exception as e:
            print(f"Device scan error: {e}")

    def _on_device_select(self, val):
        for d in self.devices:
            if d['display'] == val:
                self.selected_device = d
                return
        self.selected_device = None

    def _browse_image(self):
        path = filedialog.askopenfilename(filetypes=[("ISO Images", "*.iso"), ("IMG Images", "*.img"), ("All", "*.*")])
        if path:
            self.image_path = path
            self.lbl_image.configure(text=os.path.basename(path))

    def _start_process(self):
        if not self.is_root:
            messagebox.showerror("Error", "This tool must be run as root (use the launcher / desktop icon).")
            return

        if not self.selected_device:
            messagebox.showerror("Error", "Select a device first")
            return

        confirm_msg = f"ALL DATA ON DEVICE {self.selected_device['path']} WILL BE DESTROYED!\n\nContinue?"
        if not messagebox.askyesno("WARNING", confirm_msg, icon='warning'):
            return

        self.btn_start.configure(state="disabled")
        self.progress.set(0)
        threading.Thread(target=self._run_task, daemon=True).start()

    def _run_task(self):
        dev = self.selected_device['path']
        try:
            # 1. Unmount any mounted partitions on this device
            self.lbl_status.configure(text="Unmounting...")
            for p in sorted(glob.glob(f"{dev}*")):
                if p != dev:
                    subprocess.run(["umount", p], stderr=subprocess.DEVNULL, timeout=5)

            # 2. Operation
            if self.image_path and os.path.exists(self.image_path):
                self.lbl_status.configure(text="Writing Image...")
                cmd = ["dd", f"if={self.image_path}", f"of={dev}", "bs=4M", "status=none", "conv=fsync"]
                result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            else:
                self.lbl_status.configure(text="Formatting...")
                fs = self.fs_var.get()
                label = self.vol_var.get()

                if fs == "FAT32":
                    cmd = ["mkfs.vfat", "-F32", "-n", label, dev]
                elif fs == "NTFS":
                    cmd = ["mkfs.ntfs", "-f", "-L", label, dev]
                elif fs == "ext4":
                    cmd = ["mkfs.ext4", "-F", "-L", label, dev]
                else:
                    raise ValueError("Unsupported FS")

                result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            self.progress.set(1.0)
            self.lbl_status.configure(text="COMPLETE")
            self.after(0, lambda: messagebox.showinfo("Success", "Operation completed successfully!"))

        except subprocess.CalledProcessError as e:
            err_msg = (e.stderr or e.stdout or str(e)).strip()
            self.lbl_status.configure(text="ERROR")
            self.after(0, lambda m=err_msg: messagebox.showerror("Error", m))
        except Exception as e:
            err_msg = str(e)
            self.lbl_status.configure(text=f"ERROR: {err_msg}")
            self.after(0, lambda m=err_msg: messagebox.showerror("Error", m))
        finally:
            self.btn_start.configure(state="normal")
            self.after(0, self._refresh_devices)


if __name__ == "__main__":
    ctk.set_appearance_mode("Light")
    ctk.set_default_color_theme("blue")
    app = RufusApp()
    app.mainloop()
