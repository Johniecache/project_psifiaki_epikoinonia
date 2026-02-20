import tkinter as tk
from tkinter import ttk
import sounddevice as sd


class SettingsWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Settings")
        self.geometry("400x250")
        self.resizable(False, False)

        self.parent = parent

        # Headset/output selection
        tk.Label(self, text="Output Device (Headset):").pack(pady=(20, 5))
        self.output_combo = ttk.Combobox(self, state="readonly")
        self.output_combo.pack(pady=5, padx=20, fill="x")
        self.output_devices = [d['name'] for d in sd.query_devices() if d['max_output_channels'] > 0]
        self.output_combo['values'] = self.output_devices

        # Input/microphone selection
        tk.Label(self, text="Input Device (Microphone):").pack(pady=(20, 5))
        self.input_combo = ttk.Combobox(self, state="readonly")
        self.input_combo.pack(pady=5, padx=20, fill="x")
        self.input_devices = [d['name'] for d in sd.query_devices() if d['max_input_channels'] > 0]
        self.input_combo['values'] = self.input_devices

        # Set default devices (system default)
        default_input = sd.default.device[0]
        default_output = sd.default.device[1]
        if default_output is not None:
            self.output_combo.current(default_output)
        if default_input is not None:
            self.input_combo.current(default_input)

        # Apply button
        apply_btn = tk.Button(self, text="Apply", command=self.apply_settings)
        apply_btn.pack(pady=20)

    def apply_settings(self):
        selected_output = self.output_combo.get()
        selected_input = self.input_combo.get()

        # Apply to parent client_controller for voice
        if self.parent.client_controller:
            devices = sd.query_devices()
            # Match names to IDs
            for idx, dev in enumerate(devices):
                if dev['name'] == selected_output:
                    self.parent.client_controller.output_device_index = idx
                if dev['name'] == selected_input:
                    self.parent.client_controller.input_device_index = idx

        self.destroy()