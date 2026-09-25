import os
import json
from flask import Flask, render_template, send_from_directory, jsonify

app = Flask(__name__, template_folder='templates', static_folder='static')
# The textured house model (final.obj/.mtl) ships at the repository root,
# one level above this web_viewer/ package.
BASE_3D_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/model/<path:filename>')
def serve_model(filename):
    return send_from_directory(BASE_3D_DIR, filename)

@app.route('/api/cadastre')
def get_cadastre():
    data = {
        "ulpin": "33-012-0087-0348-2026",
        "location": {
            "name": "BK Pudur, Sugunapuram / Kuniyamuthur",
            "city": "Coimbatore",
            "district": "Coimbatore South",
            "state": "Tamil Nadu",
            "pincode": "641008",
            "latitude": 10.953500,
            "longitude": 76.963400,
            "elevation_amsl_m": 421.5
        },
        "parcel": {
            "survey_number": "SF No. 142/3B",
            "patta_number": "TR-9821/2024",
            "ward_number": "Ward 87, West Zone",
            "local_body": "Coimbatore City Municipal Corporation (CCMC)",
            "area_sqm": 227.6,
            "area_sqft": 2450.0,
            "classification": "Nanjai / Residential Plot (R-2)",
            "vertical_envelope": {
                "air_rights_limit_m": 12.0,
                "building_height_m": 8.5,
                "ground_elevation_m": 0.0,
                "subsurface_limit_m": -4.0
            }
        },
        "utilities": [
            {
                "id": "PIPE-WAT-01",
                "name": "Potable Water Supply Main",
                "type": "water",
                "color": "#00b4d8",
                "diameter_mm": 150,
                "depth_m": 1.2,
                "material": "Ductile Iron (DI) Class K9",
                "operator": "CCMC Water Supply Department / Siruvani Water Supply",
                "pressure_bar": 3.2,
                "status": "Operational / Active"
            },
            {
                "id": "PIPE-WAT-02",
                "name": "Domestic Water Service Inflow",
                "type": "water",
                "color": "#48cae4",
                "diameter_mm": 50,
                "depth_m": 1.0,
                "material": "HDPE PN10",
                "operator": "Private Household Connection",
                "pressure_bar": 2.8,
                "status": "Connected to Sump"
            },
            {
                "id": "PIPE-SEW-01",
                "name": "Municipal Sewer Trunk Line",
                "type": "sewer",
                "color": "#e76f51",
                "diameter_mm": 250,
                "depth_m": 2.5,
                "material": "Reinforced Concrete Pipe (NP3)",
                "operator": "Underground Drainage (UGD) Project - CCMC",
                "gradient": "1 in 120",
                "status": "Operational / Gravity Flow"
            },
            {
                "id": "PIPE-SEW-02",
                "name": "House Lateral Sewer and Inspection Chamber",
                "type": "sewer",
                "color": "#f4a261",
                "diameter_mm": 160,
                "depth_m": 1.8,
                "material": "uPVC SWR Ring-Fit",
                "operator": "Residential Internal Line",
                "gradient": "1 in 80",
                "status": "Active Inspection Chamber"
            },
            {
                "id": "PIPE-STM-01",
                "name": "Roadside Stormwater Conduit",
                "type": "storm",
                "color": "#2a9d8f",
                "diameter_mm": 300,
                "depth_m": 0.8,
                "material": "Precast RCC Box Drain",
                "operator": "CCMC Stormwater Infrastructure",
                "status": "Rainwater Harvesting Linked"
            },
            {
                "id": "COND-ELEC-01",
                "name": "Underground Power and Fiber Optic Cable Duct",
                "type": "power",
                "color": "#e9c46a",
                "diameter_mm": 90,
                "depth_m": 0.7,
                "material": "Double Wall Corrugated (DWC) HDPE",
                "operator": "TANGEDCO (Tamil Nadu Electricity Board)",
                "voltage": "415V 3-Phase + Optical Fiber",
                "status": "Energized"
            }
        ]
    }
    return jsonify(data)

if __name__ == '__main__':
    print('Starting 3D Cadastral and Subsurface Utility Web Viewer on port 8050...')
    app.run(host='0.0.0.0', port=8050, debug=False)
