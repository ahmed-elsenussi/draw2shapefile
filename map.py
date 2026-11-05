import tkinter as tk
import math

from tkintermapview import TkinterMapView
from PIL import Image, ImageTk


class MapWidget(TkinterMapView):

    # 3 is the minimum to close a shape (Triangle)
    MIN_POLYGON_POINTS = 3

    def __init__(
        self,
        master,
        initial_lat=28.1099,
        initial_lng=30.7503,
        **kwargs
    ):

        # Progressive zoom fallback state
        self._zoom_fallback_item = None
        self._zoom_fallback_photo = None
        self._zoom_fallback_visual_zoom = None

        super().__init__(
            master,
            database_path="map_tiles.db",
            **kwargs
        )

        # Polygon drawing state
        self.is_drawing = False
        self.polygon_points = []
        self.temp_markers = []
        self.temp_paths = []
        self.current_polygon = None
        self._dragged_idx = None  # Tracks which point is being dragged
        self.active_idx = None    # Tracks which point is currently clicked/selected

        self.canvas.configure(bg="#1a1a1a")

        # Google satellite imagery
        self.set_tile_server(
            "https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
            max_zoom=22
        )

        self.set_position(initial_lat, initial_lng)
        self.set_zoom(12)

        self.add_left_click_map_command(
            self._on_map_click
        )
        
        # Bind right-click for point deletion (Button-3 for Win/Linux, Button-2 for Mac)
        self.canvas.bind("<Button-3>", self._on_right_click)
        self.canvas.bind("<Button-2>", self._on_right_click)

    # =====================================================
    # PROGRESSIVE ZOOM
    # =====================================================

    def set_zoom(
        self,
        zoom,
        relative_pointer_x=0.5,
        relative_pointer_y=0.5
    ):

        old_zoom = getattr(self, "zoom", None)

        if (
            old_zoom is not None
            and getattr(self, "canvas_tile_array", None)
        ):

            target_zoom = zoom

            if hasattr(self, "max_zoom"):
                target_zoom = min(
                    target_zoom,
                    self.max_zoom
                )

            if hasattr(self, "min_zoom"):
                target_zoom = max(
                    target_zoom,
                    self.min_zoom
                )

            if target_zoom != old_zoom:

                try:
                    self._show_zoom_fallback(
                        target_zoom,
                        relative_pointer_x,
                        relative_pointer_y
                    )

                except Exception as exc:
                    print(f"[Zoom fallback] {exc}")

        result = super().set_zoom(
            zoom,
            relative_pointer_x,
            relative_pointer_y
        )

        self._maybe_clear_zoom_fallback()

        return result

    def _get_zoom_source_layers(self):

        layers = []

        if (
            self._zoom_fallback_item is not None
            and self._zoom_fallback_photo is not None
        ):

            coords = self.canvas.coords(
                self._zoom_fallback_item
            )

            if coords:

                layers.append((
                    coords[0],
                    coords[1],
                    self._zoom_fallback_photo
                ))

            return layers

        for column in self.canvas_tile_array:
            for tile in column:
                if tile.canvas_object is None:
                    continue
                if tile.image is self.not_loaded_tile_image:
                    continue
                if tile.image is self.empty_tile_image:
                    continue

                coords = self.canvas.coords(
                    tile.canvas_object
                )

                if len(coords) < 2:
                    continue

                layers.append((
                    coords[0],
                    coords[1],
                    tile.image
                ))

        return layers

    def _show_zoom_fallback(
        self,
        target_zoom,
        relative_pointer_x=0.5,
        relative_pointer_y=0.5
    ):

        layers = self._get_zoom_source_layers()
        if not layers:
            return

        visual_zoom = (
            self._zoom_fallback_visual_zoom
            if self._zoom_fallback_visual_zoom is not None
            else self.zoom
        )

        scale = max(
            1.0,
            2 ** (target_zoom - visual_zoom)
        )

        anchor_x = relative_pointer_x * self.width
        anchor_y = relative_pointer_y * self.height

        converted = []

        for x, y, photo in layers:
            try:
                image = ImageTk.getimage(photo).convert("RGB")
                converted.append((x, y, image))
            except Exception:
                continue

        if not converted:
            return

        left = math.floor(min(x for x, y, image in converted))
        top = math.floor(min(y for x, y, image in converted))
        right = math.ceil(max(x + image.width for x, y, image in converted))
        bottom = math.ceil(max(y + image.height for x, y, image in converted))

        source = Image.new(
            "RGB",
            (max(1, right - left), max(1, bottom - top)),
            "#1a1a1a"
        )

        for x, y, image in converted:
            source.paste(
                image,
                (round(x) - left, round(y) - top)
            )

        inverse_scale = 1.0 / scale
        transform = (
            inverse_scale,
            0,
            anchor_x * (1 - inverse_scale) - left,

            0,
            inverse_scale,
            anchor_y * (1 - inverse_scale) - top
        )

        nearest = getattr(getattr(Image, "Resampling", Image), "NEAREST")
        affine = getattr(getattr(Image, "Transform", Image), "AFFINE")

        snapshot = source.transform(
            (int(self.width), int(self.height)),
            affine,
            transform,
            resample=nearest,
            fillcolor="#1a1a1a"
        )

        new_photo = ImageTk.PhotoImage(snapshot, master=self.canvas)

        new_item = self.canvas.create_image(
            0,
            0,
            image=new_photo,
            anchor=tk.NW,
            tags=("zoom_fallback",)
        )

        old_item = self._zoom_fallback_item

        self._zoom_fallback_item = new_item
        self._zoom_fallback_photo = new_photo
        self._zoom_fallback_visual_zoom = max(visual_zoom, target_zoom)

        if old_item is not None:
            self.canvas.delete(old_item)

        self.manage_z_order()

    def _maybe_clear_zoom_fallback(self):

        if self._zoom_fallback_item is None:
            return

        tiles = [
            tile
            for column in getattr(self, "canvas_tile_array", [])
            for tile in column
        ]

        if not tiles:
            return

        all_loaded = all(
            tile.image is not self.not_loaded_tile_image
            for tile in tiles
        )

        if all_loaded:
            self._clear_zoom_fallback()

    def _clear_zoom_fallback(self):

        if self._zoom_fallback_item is not None:
            self.canvas.delete(self._zoom_fallback_item)

        self._zoom_fallback_item = None
        self._zoom_fallback_photo = None
        self._zoom_fallback_visual_zoom = None

    def update_canvas_tile_images(self):
        super().update_canvas_tile_images()
        self._maybe_clear_zoom_fallback()

    # =====================================================
    # LOCATION NAVIGATION
    # =====================================================

    def go_to_location(self, lat, lng):

        self._clear_zoom_fallback()
        self.set_position(lat, lng)
        self.set_zoom(15)
        self.set_marker(lat, lng, text=f"{lat:.4f}, {lng:.4f}")

    # =====================================================
    # POLYGON VALIDATION
    # =====================================================

    def _has_valid_polygon_points(self):
        """
        Require at least 3 distinct geographic coordinates (Triangle).
        """
        unique_points = []
        for lat, lng in self.polygon_points:
            duplicate = any(
                abs(lat - existing_lat) < 0.000001
                and abs(lng - existing_lng) < 0.000001
                for existing_lat, existing_lng in unique_points
            )
            if not duplicate:
                unique_points.append((lat, lng))

        return len(unique_points) >= self.MIN_POLYGON_POINTS
        
    def _get_vertex_at(self, event_x, event_y):
        """
        Detects if a map coordinate (click) is near an existing vertex.
        """
        click_lat, click_lng = self.convert_canvas_coords_to_decimal_coords(event_x, event_y)
        
        degrees_per_pixel = 360.0 / (256.0 * (2.0 ** self.zoom))
        threshold = 15.0 * degrees_per_pixel
        
        for i, (lat, lng) in enumerate(self.polygon_points):
            lat_rad = math.radians(lat)
            dx = (click_lng - lng) * math.cos(lat_rad)
            dy = (click_lat - lat)
            dist = math.hypot(dx, dy)
            
            if dist <= threshold:
                return i
        return None

    # =====================================================
    # INTERACTIVE DRAG & DROP & ACTIVATION
    # =====================================================
    
    def _update_marker_labels(self):
        """Updates text of markers to show which one is currently active."""
        for i, marker in enumerate(self.temp_markers):
            if i == self.active_idx:
                marker.set_text(f"📍 P{i+1}")
            else:
                marker.set_text(f"P{i+1}")

    def mouse_click(self, event):
        if not self.is_drawing and self.current_polygon:
            idx = self._get_vertex_at(event.x, event.y)
            if idx is not None:
                self._dragged_idx = idx
                self.active_idx = idx
                self._update_marker_labels()
                return # Skip super() call to freeze map panning
            else:
                # Clicked empty space, clear active point
                self.active_idx = None
                self._update_marker_labels()
                
        super().mouse_click(event)

    def mouse_move(self, event):
        if getattr(self, '_dragged_idx', None) is not None:
            lat, lng = self.convert_canvas_coords_to_decimal_coords(event.x, event.y)
            self.polygon_points[self._dragged_idx] = (lat, lng)
            
            if self.current_polygon:
                try:
                    self.current_polygon.position_list = self.polygon_points
                    self.current_polygon.draw()
                except AttributeError:
                    self._redraw_polygon()
                    
            if len(self.temp_markers) > self._dragged_idx:
                self.temp_markers[self._dragged_idx].set_position(lat, lng)
            return
            
        super().mouse_move(event)

    def mouse_release(self, event):
        if getattr(self, '_dragged_idx', None) is not None:
            self._dragged_idx = None
            return
            
        super().mouse_release(event)
        
    def _on_right_click(self, event):
        if not self.is_drawing and self.current_polygon:
            idx = self._get_vertex_at(event.x, event.y)
            if idx is not None:
                # Select the point
                self.active_idx = idx
                self._update_marker_labels()
                
                # Show custom simple menu instead of messagebox
                menu = tk.Menu(
                    self, 
                    tearoff=0, 
                    bg="#1F2937", 
                    fg="#F9FAFB", 
                    activebackground="#DC2626", 
                    font=("Segoe UI", 10)
                )
                menu.add_command(label="🗑 Delete Point", command=lambda: self._delete_point(idx))
                
                try:
                    menu.tk_popup(event.x_root, event.y_root)
                finally:
                    menu.grab_release()
        
        # 'break' stops the event from triggering default OS/Tkinter copy/paste menus
        return "break"
        
    def _delete_point(self, idx):
        self.polygon_points.pop(idx)
        self.active_idx = None
        
        if len(self.polygon_points) >= self.MIN_POLYGON_POINTS:
            # Continue functioning as a closed polygon
            self._redraw_polygon()
        else:
            # Reverts safely to an open drawing path if points fall below 3
            if self.current_polygon:
                self.current_polygon.delete()
                self.current_polygon = None
            self._clear_temp_markers()
            
            self.is_drawing = True
            
            for i, (lat, lng) in enumerate(self.polygon_points):
                marker = self.set_marker(lat, lng, text=f"P{i+1}")
                self.temp_markers.append(marker)
                
            if len(self.polygon_points) == 2:
                path = self.set_path(
                    [self.polygon_points[0], self.polygon_points[1]],
                    color="#00FF00",
                    width=2
                )
                self.temp_paths.append(path)
                
            print("[MAP] Downgraded to line. Back in drawing mode.")

    # =====================================================
    # POLYGON DRAWING & REDRAWING
    # =====================================================

    def toggle_drawing(self):
        if not self.is_drawing:
            self.is_drawing = True
            print("[MAP] Drawing started.")
            return True

        if not self._has_valid_polygon_points():
            print(f"[WARNING] At least {self.MIN_POLYGON_POINTS} distinct points are required.")
            return True

        if self.finalize_polygon():
            self.is_drawing = False

        return self.is_drawing
        
    def _redraw_polygon(self):
        if self.current_polygon:
            self.current_polygon.delete()
            self.current_polygon = None
            
        self.current_polygon = self.set_polygon(
            self.polygon_points,
            fill_color="#3182CE",
            outline_color="#63B3ED",
            border_width=2
        )
        
        self._clear_temp_markers()
        for i, (lat, lng) in enumerate(self.polygon_points):
            marker = self.set_marker(lat, lng, text="")
            self.temp_markers.append(marker)
            
        self._update_marker_labels()

    def finalize_polygon(self):
        if not self._has_valid_polygon_points():
            print(f"[ERROR] Cannot create polygon: at least {self.MIN_POLYGON_POINTS} distinct points required.")
            return False

        self._redraw_polygon()
        self._clear_temp_paths()

        print(f"[SUCCESS] Polygon created with {len(self.polygon_points)} points.")
        return True


    def _on_map_click(self, coords):
        if not self.is_drawing:
            return

        lat, lng = coords

        if self.polygon_points:
            last_lat, last_lng = self.polygon_points[-1]
            if (
                abs(lat - last_lat) < 0.000001
                and abs(lng - last_lng) < 0.000001
            ):
                return

        if len(self.polygon_points) >= self.MIN_POLYGON_POINTS:
            first_lat, first_lng = self.polygon_points[0]
            
            degrees_per_pixel = 360.0 / (256.0 * (2.0 ** self.zoom))
            threshold = 15.0 * degrees_per_pixel
            
            lat_rad = math.radians(first_lat)
            dx = (lng - first_lng) * math.cos(lat_rad)
            dy = (lat - first_lat)
            dist = math.hypot(dx, dy)
            
            if dist <= threshold:
                self.toggle_drawing()
                return

        self.polygon_points.append((lat, lng))

        marker = self.set_marker(
            lat,
            lng,
            text=f"P{len(self.polygon_points)}"
        )
        self.temp_markers.append(marker)

        if len(self.polygon_points) > 1:
            path = self.set_path(
                [
                    self.polygon_points[-2],
                    self.polygon_points[-1]
                ],
                color="#00FF00",
                width=2
            )
            self.temp_paths.append(path)

        print(f"[MAP] Points: {len(self.polygon_points)}")


    # =====================================================
    # CLEAR MAP
    # =====================================================

    def clear_map(self):
        self._clear_temp_markers()
        self._clear_temp_paths()

        if self.current_polygon:
            self.current_polygon.delete()
            self.current_polygon = None

        self.polygon_points.clear()
        self.is_drawing = False
        self.active_idx = None

        print("[MAP] All drawing elements cleared.")

    def _clear_temp_markers(self):
        for marker in self.temp_markers[:]:
            try:
                marker.delete()
            except Exception as exc:
                print(f"[Marker cleanup] {exc}")
        self.temp_markers.clear()

    def _clear_temp_paths(self):
        for path in self.temp_paths[:]:
            try:
                path.delete()
            except Exception as exc:
                print(f"[Path cleanup] {exc}")
        self.temp_paths.clear()