from flask import Flask, render_template
import pandas as pd
import geopandas as gpd
import folium
import os

app = Flask(__name__)

DATA = os.path.join(os.path.dirname(__file__), "data")

# ── Cargar y procesar datos UNA SOLA VEZ al iniciar el servidor ──────
df_pred = pd.read_csv(os.path.join(DATA, "predicciones.csv"), dtype=str)
gdf = gpd.read_file(os.path.join(DATA, "esmeraldas_parroquias.geojson"))
gdf = gdf.merge(df_pred, on="ADM3_PCODE", how="left")

def color_riesgo(riesgo):
    if riesgo == "Alto":
        return "#d73027"
    elif riesgo == "Medio":
        return "#fee08b"
    else:
        return "#1a9850"

# Pre-construir el mapa una sola vez
mapa = folium.Map(location=[0.8, -79.5], zoom_start=8)

for _, row in gdf.iterrows():
    riesgo = row.get("RIESGO_INUNDACION", "Sin datos")
    score  = row.get("SCORE", "N/A")
    parroquia = row.get("ADM3_ES", "")
    canton    = row.get("ADM2_ES", "")
    provincia = row.get("ADM1_ES", "")

    folium.GeoJson(
        row["geometry"].__geo_interface__,
        style_function=lambda f, r=riesgo: {
            "fillColor": color_riesgo(r),
            "color": "black",
            "weight": 1,
            "fillOpacity": 0.7
        },
        tooltip=folium.Tooltip(f"{parroquia} | {canton} | {provincia}"),
        popup=folium.Popup(
            f"<b>{parroquia}</b><br>Riesgo: {riesgo}<br>Score: {score}",
            max_width=200
        )
    ).add_to(mapa)

leyenda = """
<div style="position:fixed; bottom:30px; left:30px; z-index:1000;
            background:white; padding:10px; border-radius:8px;
            border:1px solid grey; font-size:13px;">
    <b>Riesgo de Inundación</b><br>
    <i style="background:#d73027;width:12px;height:12px;display:inline-block"></i> Alto<br>
    <i style="background:#fee08b;width:12px;height:12px;display:inline-block"></i> Medio<br>
    <i style="background:#1a9850;width:12px;height:12px;display:inline-block"></i> Bajo
</div>
"""
mapa.get_root().html.add_child(folium.Element(leyenda))

# Convertir a HTML una sola vez
MAPA_HTML = mapa._repr_html_()

@app.route("/")
def index():
    return render_template("index.html", mapa=MAPA_HTML)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    from waitress import serve
    print(f"Servidor corriendo en el puerto {port}")
    serve(app, host='0.0.0.0', port=port)