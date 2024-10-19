from flask import Flask, jsonify, send_file
from flask_cors import CORS, cross_origin

import csv
import numpy as np
import xarray as xr
import sys
from datetime import datetime, timedelta

from OceanPortfolioOptimization.Tools.DownloadNREL_Wind import DonwloadNREL_WindData

app = Flask(__name__)
CORS(app)

@app.route('/test', methods=['GET'])
def test():
    return jsonify({ 'message': 'The server is running' })

@app.route('/download-wind-data', methods=['GET', 'POST'])
@cross_origin(origin='*', headers=['Content-Type', 'Authorization'])
def download_wind_data():
    ListOfAvailableData=["winddirection_100m","winddirection_10m","winddirection_120m","winddirection_140m","winddirection_160m",
                    "winddirection_200m","winddirection_40m","winddirection_60m","winddirection_80m",
                    "windspeed_100m","windspeed_10m","windspeed_120m","windspeed_140m","windspeed_160m","windspeed_200m",
                    "windspeed_40m","windspeed_60m","windspeed_80m"]

    InputDataPath="./InputData"
    Data2Download="windspeed_100m" #100, 140, 160
    SavePath="./InputData/Wind/"+Data2Download+".npz"


    LatMinMax=(34, 34.5)   #(33, 37)
    LongMinMax=(-76.5,-76) #(-81,-73)
    DepthMinMax=(0,5000)   #(0,1000)
    
    DonwloadNREL_WindData(InputDataPath, SavePath, Data2Download=Data2Download, LatMinMax=LatMinMax, LongMinMax=LongMinMax, DepthMinMax=DepthMinMax)

    return send_file(SavePath, as_attachment=True)

@app.route('/get-wind-energy-optimization', methods=['GET', 'POST'])
@cross_origin(origin='*', headers=['Content-Type', 'Authorization'])
def get_wind_energy_optimization():
    from OceanPortfolioOptimization.Tools.WindTurbineTools import WindToEnergy, GetTurbineData, FilterOnDepthShoreDistance, GetCostAndGenerationWindTurbine, FilterForWTKDataset, FilterForBOEM
    from OceanPortfolioOptimization.Tools.GeneralGeoTools import PlotGeneralGeoData, PlotGeneralGeoData_Class, GetTimeList, ChangeTimeSpaceResolution, PlotsWithBOEM

    InputDataPath="./OceanPortfolioOptimization/InputData"
    GeoDataPath=InputDataPath+"/CoastLine/"
    WindTurbine="ATB_15MW_2030" #Name of the wind turbine file

    WindCostPath=InputDataPath+"/Wind/CostWindTurbines.xlsx"

    WindSpeedHeightsAvailable={"100":"windspeed_100m.npz", "140":"windspeed_140m.npz", "160":"windspeed_160m.npz"}

    WindEnergy_pu, RatedPower, LatLong, WS_Hub, Depth, DistanceShore, TimeList, ResolutionKm=WindToEnergy(InputDataPath, WindTurbine, WindSpeedHeightsAvailable, SavePath=None) 
    PlotGeneralGeoData(LatLong, np.mean(WindEnergy_pu,axis=0), GeoDataPath, ColorBarTitle="[pu]", Title="Generation for ATB 15MW Device", SavePath=None, s=6, LatMaxMin=(32.9, 37.1), LongMaxMin=(-80, -74.3))

if __name__ == '__main__':
    app.run('0.0.0.0', 4000, debug=True)