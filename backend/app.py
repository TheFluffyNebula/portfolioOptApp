from flask import Flask, jsonify, send_file, request
from flask_cors import CORS, cross_origin

import csv
import numpy as np
import xarray as xr
import sys
import json
from datetime import datetime, timedelta
from tqdm import tqdm

from OceanPortfolioOptimization.Tools.DownloadNREL_Wind import DonwloadNREL_WindData

app = Flask(__name__)
CORS(app)

@app.route('/test', methods=['GET', 'POST'])
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
    PlotGeneralGeoData(LatLong, np.mean(WindEnergy_pu,axis=0), GeoDataPath, ColorBarTitle="[pu]", Title="Generation for ATB 15MW Device", SavePath='C://Users/snisar/Desktop/OceanPortfolioOptimization/portfolio-optimization/backend', s=6, LatMaxMin=(32.9, 37.1), LongMaxMin=(-80, -74.3))

    # return send_file('/', as_attachment=True)

@app.route('/generate', methods=['GET', 'POST'])
@cross_origin(origin='*', headers=['Content-Type', 'Authorization'])
def generate():
    requestdata = json.loads(request.data)
    requestdata = json.loads(requestdata['body'])
    print(requestdata)

    from Tools.Port_Opt_MaxGeneration import SolvePortOpt_MaxGen_LCOE_Iterator

    GeneralPathResources="./OutputData/"
    PathWindDesigns=[]
    PathKiteDesigns=[]
    PathTransmissionDesign=[]
    PathWaveDesigns = []

    for resourceType in requestdata['resourceType']:
        PathWindDesigns.append(GeneralPathResources+resourceType)

    for transmission in requestdata['transmission']:
        PathTransmissionDesign.append(GeneralPathResources+transmission)

    print(PathWindDesigns)
    print(PathTransmissionDesign)

    LCOE_RANGE=range(requestdata['lcoe_max'], requestdata['lcoe_min'], -1*requestdata['lcoe_step'])
    Max_CollectionRadious=30
    MaxDesingsKite=1
    MaxDesignsWind=1
    MaxDesingsWave=0
    MinNumWindTurb=0
    MinNumWaveTurb=0
    MinNumKiteTrub=0

    for PathTransmissionDesign_i in tqdm(PathTransmissionDesign):
        for PathWindDesigns_i in tqdm(PathWindDesigns):
            TurbineCaseName=PathWindDesigns_i.rsplit(r"/")[-1][:-4]
            TransmissionCaseName=PathTransmissionDesign_i.rsplit(r"/")[-1][:-4]
            
            SavePath="/OutputData/Portfolios/Wind_"+TurbineCaseName+"_"+TransmissionCaseName+".npz"
            ReadMe="Case with wind, considering a 1.2GW, 1.0, 0.6, 0.3 or 0.1GW transmission system, 30km radious and 1 design for each tech\
                \n Wind designs: 8MW Vestas 2020, 12MW 2030, 15MW 2030, 18MW 2030"
                
            #Create and solve the optimization problem
            SolvePortOpt_MaxGen_LCOE_Iterator([PathWindDesigns_i], PathWaveDesigns, PathKiteDesigns, PathTransmissionDesign_i, LCOE_RANGE\
                ,Max_CollectionRadious,MaxDesignsWind, MaxDesingsWave, MaxDesingsKite,MinNumWindTurb,MinNumWaveTurb,MinNumKiteTrub\
                ,ReadMe,SavePath=SavePath)

    return jsonify({
        'result': requestdata
    })

if __name__ == '__main__':
    app.run('0.0.0.0', 4000, debug=True)