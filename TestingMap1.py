import folium
import geopandas as gpd
import pandas as pd
import branca.colormap as cm
from folium.plugins import Fullscreen
import os
from branca.element import Figure, Html, MacroElement
import json

# === 1. Load Shapefile ===
# Pastikan path ini sesuai di komputer Anda
shapefile_path = r"C:/Users/User/Downloads/ProjectMap-master/BATAS PROVINSI DESEMBER 2019 DUKCAPIL/BATAS_PROVINSI_DESEMBER_2019_DUKCAPIL.shp"
gdf = gpd.read_file(shapefile_path)
gdf['geometry'] = gdf['geometry'].simplify(tolerance=0.01, preserve_topology=True)

# === 2. Load Excel ===
data_path = "data_pencairan1.xlsx"
nilai_df = pd.read_excel(data_path)

# === 3. Group by PROVINSI ===
nilai_df_grouped = nilai_df.groupby("PROVINSI").agg({
    "total_loan_created": "sum",
    "total_os_loan_created": "sum",
    "total_ktp_reject": "sum",
    "total_usr_reject": "sum",
    "total_lepas_ktp_reject": "sum",
    "total_lepas_usr_reject": "sum",
    "total_reject_slik": "sum",
    "total_reject_sicd_raya": "sum",
    "total_reject_sicd_bri": "sum",
    "total_reject_blacklist_company": "sum",
    "total_reject_score_500": "sum",
    "total_reject_failed_to_approve": "sum"
}).reset_index()

# === 4. Merge Data ===
gdf = gdf.merge(nilai_df_grouped, how="left", on="PROVINSI")
numeric_cols = gdf.select_dtypes(include=['number']).columns
gdf[numeric_cols] = gdf[numeric_cols].fillna(0)

# === 5. Hitung Metrics ===
gdf["total_reject"] = (
    gdf["total_reject_slik"] + gdf["total_reject_sicd_raya"] + 
    gdf["total_reject_sicd_bri"] + gdf["total_reject_blacklist_company"] + 
    gdf["total_reject_score_500"] + gdf["total_reject_failed_to_approve"]
)
gdf["os_potensi_ktp"] = gdf["total_lepas_ktp_reject"]
gdf["os_potensi_usr"] = gdf["total_lepas_usr_reject"]
gdf["os_loan_created"] = gdf["total_os_loan_created"]

# === 6. Siapkan Data Chart Top 10 ===
loan_sorted = gdf.sort_values("total_os_loan_created", ascending=False).head(10)
loan_labels = [f"{p} (NOA: {int(n)})" for p, n in zip(loan_sorted["PROVINSI"], loan_sorted["total_loan_created"])]
loan_values = loan_sorted["total_os_loan_created"].tolist()

reject_sorted = gdf.sort_values("total_reject", ascending=False).head(10)
reject_labels = reject_sorted["PROVINSI"].tolist()
reject_values = reject_sorted["total_reject"].tolist()

usr_sorted = gdf.sort_values("os_potensi_usr", ascending=False).head(10)
usr_labels = [f"{p} (NOA: {int(n)})" for p, n in zip(usr_sorted["PROVINSI"], usr_sorted["total_usr_reject"])]
usr_values = usr_sorted["os_potensi_usr"].tolist()

ktp_sorted = gdf.sort_values("os_potensi_ktp", ascending=False).head(10)
ktp_labels = [f"{p} (NOA: {int(n)})" for p, n in zip(ktp_sorted["PROVINSI"], ktp_sorted["total_ktp_reject"])]
ktp_values = ktp_sorted["os_potensi_ktp"].tolist()

# === 7. Build Map ===
m = folium.Map(location=[-2.5, 118], zoom_start=5, tiles="CartoDB positron")
Fullscreen(position='topleft').add_to(m)

colormap = cm.linear.YlGnBu_09.scale(float(gdf["total_loan_created"].min()), float(gdf["total_loan_created"].max()))
colormap.caption = "Intensitas Pencairan (Loan Created)"

# === 8. Konfigurasi Tooltip (MUNCUL SAAT HOVER) ===
hover_tooltip = folium.GeoJsonTooltip(
    fields=["PROVINSI", "total_loan_created", "total_reject", "os_potensi_usr"],
    aliases=["Provinsi", "Pencairan (NOA)", "Total Reject (NOA)", "Potensi USR (OS)"],
    localize=True,
    sticky=True,
    style="""
        background-color: rgba(255, 255, 255, 0.95);
        border: 1px solid #ddd;
        border-radius: 6px;
        font-family: 'Segoe UI', sans-serif;
        font-size: 11px;
        font-weight: 400;
        padding: 8px;
        color: #444;
        white-space: nowrap;
   """
)

# === 9. Konfigurasi Popup (MUNCUL SAAT KLIK) ===
click_popup = folium.features.GeoJsonPopup(
    fields=[
        "total_reject_slik", "total_reject_sicd_raya", "total_reject_sicd_bri",
        "total_reject_blacklist_company", "total_reject_score_500", "total_reject_failed_to_approve"
    ],
    aliases=[
        "• SLIK", "• SICD Raya", "• SICD BRI",
        "• Blacklist Company", "• Score < 500", "• RPC"
    ],
    localize=True,
    labels=True,
    style="""
        font-family: 'Segoe UI', sans-serif;
        font-size: 11px;
        font-weight: 400;
        width: auto;
        min-width: 180px;
        padding: 5px;
        white-space: nowrap;
    """
)

# === 10. Gabungkan ke dalam Map ===
geojson = folium.GeoJson(
    gdf,
    style_function=lambda x: {
        "fillColor": colormap(x["properties"]["total_loan_created"]),
        "color": "black",
        "weight": 0.5,
        "fillOpacity": 0.7,
    },
    tooltip=hover_tooltip,
    popup=click_popup
).add_to(m)

colormap.add_to(m)

# === CSS & JS FIX (Final Styling) ===
m.get_root().header.add_child(folium.Element("""
    <style>
        .leaflet-container { font-family: 'Segoe UI', sans-serif !important; }
        
        /* Merapikan Popup agar ramping */
        .leaflet-popup-content-wrapper { 
            border-radius: 8px !important; 
            padding: 2px !important;
        }
        .leaflet-popup-content {
            margin: 10px !important;
            line-height: 1.4 !important;
        }

        /* Hilangkan Hover saat Klik */
        .leaflet-popup-open ~ .leaflet-tooltip-pane {
            display: none !important;
        }
    </style>
    
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            var observer = new MutationObserver(function(mutations) {
                var pane = document.querySelector('.leaflet-tooltip-pane');
                if (!pane) return;
                if (document.querySelector('.leaflet-popup')) {
                    pane.style.visibility = 'hidden';
                } else {
                    pane.style.visibility = 'visible';
                }
            });
            observer.observe(document.body, { childList: true, subtree: true });
        });
    </script>
"""))

# # === CSS & JS FIX (HIDE HOVER SAAT KLIK) ===
m.get_root().header.add_child(folium.Element("""
    <style>
        /* Font styling agar lebih rapi */
        .leaflet-container { font-family: 'Segoe UI', Tahoma, sans-serif !important; }
        
        /* Merapikan kotak Popup */
        .leaflet-popup-content-wrapper { 
            border-radius: 12px !important; 
            box-shadow: 0 5px 15px rgba(0,0,0,0.2) !important; 
        }

        /* Logic: Sembunyikan SEMUA tooltip jika ada popup yang sedang terbuka */
        .leaflet-popup-open ~ .leaflet-tooltip-pane,
        .leaflet-has-popup.leaflet-popup-open .leaflet-tooltip {
            display: none !important;
        }
        
        /* Tambahan: Jika popup sedang aktif di map, paksa tooltip jadi transparan */
        body.popup-open .leaflet-tooltip-pane {
            display: none !important;
        }
    </style>
    
    <script>
        // Script tambahan untuk mendeteksi kapan popup dibuka/tutup
        document.addEventListener('DOMContentLoaded', function() {
            var mapElement = document.querySelector('.leaflet-container');
            if (mapElement) {
                // Monitor perubahan pada map untuk menyembunyikan tooltip secara paksa
                var observer = new MutationObserver(function(mutations) {
                    if (document.querySelector('.leaflet-popup')) {
                        document.querySelector('.leaflet-tooltip-pane').style.display = 'none';
                    } else {
                        document.querySelector('.leaflet-tooltip-pane').style.display = 'block';
                    }
                });
                observer.observe(document.body, { childList: true, subtree: true });
            }
        });
    </script>
"""))


# === 8. HEADER UTAMA (Maret 2026) ===
header_html = """
<div style="
    position: fixed; 
    top: 20px; 
    left: 50%; 
    transform: translateX(-50%); 
    z-index: 10000; 
    background: white; 
    padding: 10px 30px; 
    border-radius: 50px; 
    box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    border: 2px solid #0275d8;
    text-align: center;
">
    <h1 style="margin: 0; font-family: 'Segoe UI', Arial; font-size: 24px; color: #333; font-weight: bold;">
        MAP PENCAIRAN 01 - 15 Juni 2026
    </h1>
</div>
"""
m.get_root().html.add_child(folium.Element(header_html))

# === 9. Chart Container (Samping) ===
chart_container = """
<div id="chartBox" style="
    position: fixed; top: 100px; right: 20px; z-index: 9999; width: 420px;
    background: rgba(255,255,255,0.95); padding: 15px; border-radius: 12px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.3); font-family: Arial;
">
    <div style="text-align:center; margin-bottom:15px;">
        <div style="display: flex; justify-content: space-between; gap: 5px;">
            <button id="btnLoan" onclick="showLoan()" style="flex:1; padding:6px; font-size:11px; border-radius:4px; border:1px solid #0275d8; background:#0275d8; color:white; cursor:pointer;">Loan Created</button>
            <button id="btnReject" onclick="showReject()" style="flex:1; padding:6px; font-size:11px; border-radius:4px; border:1px solid #d9534f; background:transparent; color:#d9534f; cursor:pointer;">Reject Total</button>
            <button id="btnUSR" onclick="showUSR()" style="flex:1; padding:6px; font-size:11px; border-radius:4px; border:1px solid #ff8800; background:transparent; color:#ff8800; cursor:pointer;">USR Reject</button>
            <button id="btnKTP" onclick="showKTP()" style="flex:1; padding:6px; font-size:11px; border-radius:4px; border:1px solid #6f42c1; background:transparent; color:#6f42c1; cursor:pointer;">KTP Reject</button>
        </div>
    </div>
    <h4 id="chartTitle" style="margin:0; text-align:center; font-size:13px; color:#555;">Loan Created — Top 10 OS</h4>
    <div style="height:280px; margin-top:10px;">
        <canvas id="chartReject"></canvas>
    </div>
</div>
"""
m.get_root().html.add_child(folium.Element(chart_container))

# === 10. Chart Script (JS) ===
chart_script = f"""
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
let chartObj = null;
const loanLabels = {json.dumps(loan_labels)}; const loanData = {json.dumps(loan_values)};
const rejectLabels = {json.dumps(reject_labels)}; const rejectData = {json.dumps(reject_values)};
const usrLabels = {json.dumps(usr_labels)}; const usrData = {json.dumps(usr_values)};
const ktpLabels = {json.dumps(ktp_labels)}; const ktpData = {json.dumps(ktp_values)};

function renderChart(labels, data, color, labelName) {{
    const ctx = document.getElementById('chartReject').getContext('2d');
    if (chartObj) chartObj.destroy();
    chartObj = new Chart(ctx, {{
        type: 'bar',
        data: {{
            labels: labels,
            datasets: [{{ label: labelName, data: data, backgroundColor: color, borderRadius: 5 }}]
        }},
        options: {{
            indexAxis: 'y', responsive: true, maintainAspectRatio: false,
            plugins: {{ legend: {{ display: true }} }}
        }}
    }});
}}

function activateButton(active, btns) {{
    btns.forEach(btn => {{ 
        const el = document.getElementById(btn);
        if (el) {{ el.style.background = "transparent"; el.style.color = el.style.borderColor; }}
    }});
    const act = document.getElementById(active);
    if (act) {{ act.style.background = act.style.borderColor; act.style.color = "white"; }}
}}

function showLoan() {{
    activateButton("btnLoan", ["btnLoan","btnReject","btnUSR","btnKTP"]);
    document.getElementById("chartTitle").innerText = "Loan Created — Top 10 OS";
    renderChart(loanLabels, loanData, "rgba(2,117,216,0.8)", "OS");
}}
function showReject() {{
    activateButton("btnReject", ["btnLoan","btnReject","btnUSR","btnKTP"]);
    document.getElementById("chartTitle").innerText = "Reject Total — Top 10 NOA";
    renderChart(rejectLabels, rejectData, "rgba(217,83,79,0.8)", "NOA");
}}
function showUSR() {{
    activateButton("btnUSR", ["btnLoan","btnReject","btnUSR","btnKTP"]);
    document.getElementById("chartTitle").innerText = "USR Reject — Top 10 OS";
    renderChart(usrLabels, usrData, "rgba(255,136,0,0.8)", "OS");
}}
function showKTP() {{
    activateButton("btnKTP", ["btnLoan","btnReject","btnUSR","btnKTP"]);
    document.getElementById("chartTitle").innerText = "KTP Reject — Top 10 OS";
    renderChart(ktpLabels, ktpData, "rgba(111,66,193,0.8)", "OS");
}}
setTimeout(() => {{ showLoan(); }}, 300);
</script>
"""
m.get_root().html.add_child(folium.Element(chart_script))

# === 12. Save ===
m.save("index.html")
print("Sukses!")
