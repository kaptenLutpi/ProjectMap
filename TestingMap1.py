import folium
import geopandas as gpd
import pandas as pd
import branca.colormap as cm
from folium.plugins import Fullscreen
import os

# --- 1. Load data & Sederhanakan Geometri ---
shapefile_path = r"C:\Users\luthfi\Downloads\MapProject\BATAS PROVINSI DESEMBER 2019 DUKCAPIL\BATAS_PROVINSI_DESEMBER_2019_DUKCAPIL.shp"
gdf = gpd.read_file(shapefile_path)

# PENTING: Sederhanakan data untuk mengurangi ukuran file
gdf['geometry'] = gdf['geometry'].simplify(tolerance=0.01, preserve_topology=True)

nilai_df1 = pd.read_excel("data_pencairan1.xlsx")
nilai_df2 = pd.read_excel("data_pencairan2.xlsx")

gdf1 = gdf.merge(nilai_df1, how="left", on="PROVINSI")
gdf2 = gdf.merge(nilai_df2, how="left", on="PROVINSI")

# --- 2. Simpan GeoDataFrame menjadi file GeoJSON terpisah ---
gdf1.to_file("data1.geojson", driver="GeoJSON")
gdf2.to_file("data2.geojson", driver="GeoJSON")

# --- 3. Inisialisasi peta ---
m = folium.Map(location=[-2.5, 118], zoom_start=5, tiles="CartoDB positron")

# --- 4. Buat colormap & Tambahkan layer DARI FILE GEOJSON ---
all_vals = pd.concat([gdf1["nilai"], gdf2["nilai"]])
colormap = cm.linear.YlGnBu_09.scale(all_vals.min(), all_vals.max())
colormap.caption = "Jumlah Pencairan"

folium.GeoJson(
    "data1.geojson", # Mengacu pada file GeoJSON, BUKAN variabel gdf1
    name="Jumlah Pencairan Tanggal 2025-07-01 s/d 2025-07-14",
    # ... (lanjutan kode)
).add_to(m)

folium.GeoJson(
    "data2.geojson", # Mengacu pada file GeoJSON, BUKAN variabel gdf2
    name="Jumlah Pencairan Tanggal 2025-07-15 s/d 2025-07-28",
    # ... (lanjutan kode)
).add_to(m)

# --- 5. Tambahkan kontrol layer & colormap ---
colormap.add_to(m)
folium.LayerControl(collapsed=False).add_to(m)

# --- 6. Simpan HTML ---
m.save("peta_pencairan.html")