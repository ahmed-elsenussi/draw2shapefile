import os
import tempfile
import zipfile
from pathlib import Path
import geopandas as gpd
import numpy as np
from shapely.geometry import Polygon
import pyogrio  # Ensures PyInstaller bundles GDAL binaries

def export_polygon_to_zip(polygon_points, zip_path):
    """
    Exports a list of (lat, lng) tuples to a zipped ESRI Shapefile matching the target schema.
    """
    if len(polygon_points) < 3:
        raise ValueError("A valid polygon requires at least 3 points.")

    # Swap (lat, lng) to (lng, lat) for standard GIS spatial data (X = Lng, Y = Lat)
    coords_xy = [(lng, lat) for lat, lng in polygon_points]
    
    # Ensure closed geometry ring
    if coords_xy[0] != coords_xy[-1]:
        coords_xy.append(coords_xy[0])

    poly_geom = Polygon(coords_xy)

    # Build GeoDataFrame with target schema (FID as int32)
    gdf = gpd.GeoDataFrame(
        [{'FID': np.int32(1)}],
        geometry=[poly_geom],
        crs="EPSG:4326"
    )

    base_name = Path(zip_path).stem

    # Save sidecars to temporary folder and compress into zip (excluding .cpg)
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_shp_path = os.path.join(temp_dir, f"{base_name}.shp")
        gdf.to_file(temp_shp_path, driver="ESRI Shapefile")

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_out:
            for fname in os.listdir(temp_dir):
                if fname.lower().endswith('.cpg'):
                    continue
                fpath = os.path.join(temp_dir, fname)
                zip_out.write(fpath, arcname=fname)