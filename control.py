
import os
from tkinter import filedialog
import customtkinter as ctk

from exporter import export_polygon_to_zip


class ControlPanel(ctk.CTkFrame):

    MIN_POLYGON_POINTS = 4

    COLORS = {
        "panel": "#111827",
        "surface": "#1F2937",
        "border": "#374151",
        "text": "#F9FAFB",
        "muted": "#9CA3AF",

        "blue": "#2563EB",
        "blue_hover": "#1D4ED8",

        "green": "#059669",
        "green_hover": "#047857",

        "red": "#DC2626",
        "red_hover": "#B91C1C",

        "gray": "#374151",
        "gray_hover": "#4B5563",

        "entry": "#111827",

        "success_bg": "#064E3B",
        "success": "#34D399",

        "error_bg": "#7F1D1D",
        "error": "#FCA5A5",

        "warning_bg": "#78350F",
        "warning": "#FCD34D",

        "info_bg": "#1E3A8A",
        "info": "#93C5FD",
    }

    def __init__(self, master, map_widget, **kwargs):

        super().__init__(
            master,
            fg_color=self.COLORS["panel"],
            corner_radius=12,
            border_width=1,
            border_color=self.COLORS["border"],
            **kwargs
        )

        self.map_widget = map_widget

        self.grid_columnconfigure((0, 1, 2), weight=1)

        toolbar = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )
        toolbar.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=8
        )

        self._create_location_section(toolbar)
        self._create_drawing_section(toolbar)
        self._create_export_section(toolbar)

    # =====================================================
    # CUSTOM DIALOG
    # =====================================================

    def _show_dialog(
        self,
        title,
        message,
        dialog_type="info",
        confirm=False,
        details=None
    ):

        styles = {
            "success": {
                "icon": "✓",
                "color": self.COLORS["success"],
                "background": self.COLORS["success_bg"],
                "button": self.COLORS["green"],
                "hover": self.COLORS["green_hover"],
                "default": "Continue",
            },
            "error": {
                "icon": "✕",
                "color": self.COLORS["error"],
                "background": self.COLORS["error_bg"],
                "button": self.COLORS["red"],
                "hover": self.COLORS["red_hover"],
                "default": "Close",
            },
            "warning": {
                "icon": "!",
                "color": self.COLORS["warning"],
                "background": self.COLORS["warning_bg"],
                "button": "#D97706",
                "hover": "#B45309",
                "default": "Got it",
            },
            "info": {
                "icon": "i",
                "color": self.COLORS["info"],
                "background": self.COLORS["info_bg"],
                "button": self.COLORS["blue"],
                "hover": self.COLORS["blue_hover"],
                "default": "OK",
            },
        }

        style = styles[dialog_type]

        dialog = ctk.CTkToplevel(self)
        dialog.title(title)
        dialog.geometry("420x250" if not details else "460x310")
        dialog.resizable(False, False)
        dialog.configure(fg_color=self.COLORS["panel"])
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        # Center over application window
        dialog.update_idletasks()

        parent = self.winfo_toplevel()
        parent.update_idletasks()

        x = parent.winfo_rootx() + (
            parent.winfo_width() - dialog.winfo_width()
        ) // 2

        y = parent.winfo_rooty() + (
            parent.winfo_height() - dialog.winfo_height()
        ) // 2

        dialog.geometry(f"+{x}+{y}")

        dialog.grid_columnconfigure(0, weight=1)

        # Header icon
        icon_frame = ctk.CTkFrame(
            dialog,
            fg_color=style["background"],
            corner_radius=30,
            width=48,
            height=48
        )
        icon_frame.pack(pady=(22, 10))
        icon_frame.pack_propagate(False)

        ctk.CTkLabel(
            icon_frame,
            text=style["icon"],
            font=ctk.CTkFont(
                family="Segoe UI",
                size=24,
                weight="bold"
            ),
            text_color=style["color"]
        ).pack(expand=True)

        # Title
        ctk.CTkLabel(
            dialog,
            text=title,
            font=ctk.CTkFont(
                family="Segoe UI",
                size=17,
                weight="bold"
            ),
            text_color=self.COLORS["text"]
        ).pack(pady=(0, 7))

        # Message
        ctk.CTkLabel(
            dialog,
            text=message,
            font=ctk.CTkFont(
                family="Segoe UI",
                size=12
            ),
            text_color=self.COLORS["muted"],
            wraplength=380,
            justify="center"
        ).pack(
            padx=20,
            pady=(0, 10)
        )

        # Optional details
        if details:

            details_box = ctk.CTkFrame(
                dialog,
                fg_color=self.COLORS["surface"],
                corner_radius=8
            )
            details_box.pack(
                fill="x",
                padx=25,
                pady=(0, 10)
            )

            ctk.CTkLabel(
                details_box,
                text=details,
                font=ctk.CTkFont(
                    family="Segoe UI",
                    size=10
                ),
                text_color=self.COLORS["muted"],
                wraplength=380,
                justify="left"
            ).pack(
                padx=10,
                pady=8
            )

        # Buttons
        result = {"confirmed": False}

        buttons = ctk.CTkFrame(
            dialog,
            fg_color="transparent"
        )
        buttons.pack(
            fill="x",
            padx=25,
            pady=(5, 18)
        )

        def close_dialog():
            dialog.destroy()

        if confirm:

            def confirm_action():
                result["confirmed"] = True
                dialog.destroy()

            ctk.CTkButton(
                buttons,
                text="Cancel",
                width=105,
                height=34,
                corner_radius=8,
                fg_color=self.COLORS["gray"],
                hover_color=self.COLORS["gray_hover"],
                command=close_dialog
            ).pack(
                side="right",
                padx=(6, 0)
            )

            ctk.CTkButton(
                buttons,
                text="Confirm",
                width=105,
                height=34,
                corner_radius=8,
                fg_color=style["button"],
                hover_color=style["hover"],
                command=confirm_action
            ).pack(side="right")

        else:

            ctk.CTkButton(
                buttons,
                text=style["default"],
                width=120,
                height=34,
                corner_radius=8,
                fg_color=style["button"],
                hover_color=style["hover"],
                command=close_dialog
            ).pack()

        dialog.protocol("WM_DELETE_WINDOW", close_dialog)

        self.wait_window(dialog)

        return result["confirmed"]

    # =====================================================
    # SECTION FACTORY
    # =====================================================

    def _create_section(self, parent, title):

        section = ctk.CTkFrame(
            parent,
            fg_color=self.COLORS["surface"],
            corner_radius=10,
            border_width=1,
            border_color=self.COLORS["border"]
        )

        section.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(0, 8)
        )

        ctk.CTkLabel(
            section,
            text=title,
            font=ctk.CTkFont(
                family="Segoe UI",
                size=11,
                weight="bold"
            ),
            text_color=self.COLORS["muted"]
        ).pack(
            anchor="w",
            padx=10,
            pady=(7, 5)
        )

        return section

    # =====================================================
    # BUTTON FACTORY
    # =====================================================

    def _create_button(
        self,
        parent,
        text,
        command,
        color,
        hover_color,
        width=100
    ):

        return ctk.CTkButton(
            parent,
            text=text,
            command=command,
            width=width,
            height=34,
            corner_radius=8,
            border_width=0,
            fg_color=color,
            hover_color=hover_color,
            text_color="#FFFFFF",
            font=ctk.CTkFont(
                family="Segoe UI",
                size=12,
                weight="bold"
            ),
            cursor="hand2"
        )

    # =====================================================
    # INPUT FACTORY
    # =====================================================

    def _input(self, parent, default, width=90):

        entry = ctk.CTkEntry(
            parent,
            width=width,
            height=34,
            corner_radius=8,
            border_width=1,
            border_color=self.COLORS["border"],
            fg_color=self.COLORS["entry"],
            text_color=self.COLORS["text"],
            placeholder_text_color=self.COLORS["muted"],
            font=ctk.CTkFont(
                family="Segoe UI",
                size=12
            ),
            justify="center"
        )

        entry.insert(0, default)
        return entry

    # =====================================================
    # LOCATION SECTION
    # =====================================================

    def _create_location_section(self, parent):

        section = self._create_section(
            parent,
            "⌖  LOCATION"
        )

        row = ctk.CTkFrame(
            section,
            fg_color="transparent"
        )
        row.pack(
            fill="x",
            padx=8,
            pady=(0, 8)
        )

        self.lat_entry = self._input(
            row,
            "28.1099",
            width=85
        )
        self.lat_entry.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 5)
        )

        self.lng_entry = self._input(
            row,
            "30.7503",
            width=85
        )
        self.lng_entry.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 5)
        )

        self.go_btn = self._create_button(
            row,
            "⌖ Go",
            self._go,
            self.COLORS["blue"],
            self.COLORS["blue_hover"],
            width=65
        )
        self.go_btn.pack(side="left")

    # =====================================================
    # DRAWING SECTION
    # =====================================================

    def _create_drawing_section(self, parent):

        section = self._create_section(
            parent,
            "✎  POLYGON DRAWING"
        )

        row = ctk.CTkFrame(
            section,
            fg_color="transparent"
        )
        row.pack(
            fill="x",
            padx=8,
            pady=(0, 8)
        )

        self.points_label = ctk.CTkLabel(
            row,
            text="4+ points",
            font=ctk.CTkFont(
                family="Segoe UI",
                size=11,
                weight="bold"
            ),
            text_color=self.COLORS["muted"]
        )
        self.points_label.pack(
            side="left",
            padx=(2, 7)
        )

        self.draw_btn = self._create_button(
            row,
            "✎ Draw",
            self._toggle_draw,
            self.COLORS["blue"],
            self.COLORS["blue_hover"],
            width=95
        )
        self.draw_btn.pack(
            side="left",
            padx=(0, 5)
        )

        self.clear_btn = self._create_button(
            row,
            "⌫ Clear",
            self._clear,
            self.COLORS["gray"],
            self.COLORS["gray_hover"],
            width=85
        )
        self.clear_btn.pack(side="left")

    # =====================================================
    # EXPORT SECTION
    # =====================================================

    def _create_export_section(self, parent):

        section = self._create_section(
            parent,
            "⇩  EXPORT"
        )

        row = ctk.CTkFrame(
            section,
            fg_color="transparent"
        )
        row.pack(
            fill="x",
            padx=8,
            pady=(0, 8)
        )

        self.save_btn = self._create_button(
            row,
            "⇩ Export ZIP",
            self._save,
            self.COLORS["green"],
            self.COLORS["green_hover"],
            width=125
        )
        self.save_btn.pack(
            side="left",
            fill="x",
            expand=True
        )

        ctk.CTkLabel(
            row,
            text=".SHP",
            font=ctk.CTkFont(
                family="Segoe UI",
                size=10,
                weight="bold"
            ),
            text_color=self.COLORS["muted"]
        ).pack(
            side="left",
            padx=(8, 2)
        )

    # =====================================================
    # LOCATION
    # =====================================================

    def _go(self):

        lat_text = self.lat_entry.get().strip()
        lng_text = self.lng_entry.get().strip()

        if not lat_text or not lng_text:

            missing = []

            if not lat_text:
                missing.append("Latitude")

            if not lng_text:
                missing.append("Longitude")

            self._show_dialog(
                "Missing Coordinates",
                f"Please enter {' and '.join(missing)} before navigating.",
                "warning"
            )
            return

        try:

            lat = float(lat_text)
            lng = float(lng_text)

            if not -90 <= lat <= 90:

                self._show_dialog(
                    "Invalid Latitude",
                    "Latitude must be between -90 and 90 degrees.",
                    "error"
                )
                self.lat_entry.focus()
                return

            if not -180 <= lng <= 180:

                self._show_dialog(
                    "Invalid Longitude",
                    "Longitude must be between -180 and 180 degrees.",
                    "error"
                )
                self.lng_entry.focus()
                return

            self.map_widget.go_to_location(lat, lng)

        except ValueError:

            self._show_dialog(
                "Invalid Coordinates",
                "Coordinates must contain valid numeric values.",
                "error"
            )

    # =====================================================
    # DRAWING
    # =====================================================

    def _toggle_draw(self):

        if not self.map_widget.is_drawing:

            self.map_widget.toggle_drawing()
            self._update_draw_btn(True)
            return

        if not self.map_widget._has_valid_polygon_points():

            self._show_dialog(
                "Not Enough Points",
                (
                    "A polygon requires at least 4 distinct points.\n"
                    f"Currently added: "
                    f"{len(self.map_widget.polygon_points)} points."
                ),
                "warning"
            )
            return

        self.map_widget.toggle_drawing()

        self._update_draw_btn(
            self.map_widget.is_drawing
        )

    def _update_draw_btn(self, is_drawing):

        if is_drawing:

            self.draw_btn.configure(
                text="■ Stop",
                fg_color=self.COLORS["red"],
                hover_color=self.COLORS["red_hover"]
            )

        else:

            self.draw_btn.configure(
                text="✎ Draw",
                fg_color=self.COLORS["blue"],
                hover_color=self.COLORS["blue_hover"]
            )

    # =====================================================
    # CLEAR MAP
    # =====================================================

    def _clear(self):

        confirm = self._show_dialog(
            "Clear Map",
            "This will remove all drawn points and polygons.",
            "warning",
            confirm=True
        )

        if not confirm:
            return

        self.map_widget.clear_map()
        self._update_draw_btn(False)

        self._show_dialog(
            "Map Cleared",
            "All temporary points and polygons have been removed.",
            "success"
        )

    # =====================================================
    # EXPORT
    # =====================================================

    def _save(self):

        if self.map_widget.is_drawing:

            self._show_dialog(
                "Drawing In Progress",
                "Finish your polygon before exporting it.",
                "warning"
            )
            return

        if not self.map_widget._has_valid_polygon_points():

            self._show_dialog(
                "Invalid Polygon",
                "A valid polygon must contain at least 4 distinct points.",
                "warning"
            )
            return

        if self.map_widget.current_polygon is None:

            self._show_dialog(
                "No Polygon Found",
                "Draw a polygon and finish drawing before exporting.",
                "warning"
            )
            return

        zip_path = filedialog.asksaveasfilename(
            defaultextension=".zip",
            filetypes=[
                ("Zipped Shapefile", "*.zip")
            ],
            title="Export Polygon Shapefile"
        )

        if not zip_path:
            return

        try:

            export_polygon_to_zip(
                self.map_widget.polygon_points,
                zip_path
            )

            self._show_dialog(
                "Export Successful",
                "Your shapefile has been exported successfully.",
                "success",
                details=f"Saved to:\n{zip_path}"
            )

        except Exception as e:

            self._show_dialog(
                "Export Failed",
                "Something went wrong while exporting the shapefile.",
                "error",
                details=str(e)
            )
