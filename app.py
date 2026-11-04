import customtkinter as ctk
from map import MapWidget
from control import ControlPanel

def main():
    ctk.set_appearance_mode("Dark")
    app = ctk.CTk()
    app.geometry("1100x800")
    app.title("Minya Governorate - Polygon GIS Exporter")

    # Initialize Map Display
    map_widget = MapWidget(app, width=1100, height=720, corner_radius=0)

    # Initialize Top Control Panel Header
    control_panel = ControlPanel(app, map_widget=map_widget, height=50)
    control_panel.pack(fill="x", padx=10, pady=10)

    # Pack Map Display underneath
    map_widget.pack(fill="both", expand=True)

    app.mainloop()

if __name__ == "__main__":
    main()