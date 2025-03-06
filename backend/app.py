#env Gurobi

from flask import Flask, jsonify, send_file, request
from flask_cors import CORS, cross_origin

import csv
import numpy as np
import xarray as xr
import sys
import json
from datetime import datetime, timedelta
from tqdm import tqdm
import time

from OceanPortfolioOptimization.Tools.DownloadNREL_Wind import DonwloadNREL_WindData
from OceanPortfolioOptimization.Tools.GeneralGeoTools import PlotTurbineLocations, ChangeTimeSpaceResolution
from Tools.Port_Opt_MaxGeneration import SolvePortOpt_MaxGen_LCOE_Iterator
from gurobipy import *
from pathlib import Path

app = Flask(__name__)
CORS(app)

path = Path(__file__).parent

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

@app.route('/getWindEnergyCostGeneration', methods=['POST'])
@cross_origin(origin='*', headers=['Content-Type', 'Authorization'])
def getWindEnergyCostGeneration():
    CurrentTimeResolution=1 #in hours
    NewTimeResolution=3 #3hour time discretization
    StepsPerDegree=10 #New grid resolution 1/StepsPerDegree (If you want the same resolution as the BOEM data, set this to 100 as it will filter sites with no data)

    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    try:
        requestdata = request.get_json()  # Use Flask's built-in JSON parsing
        # Remove redundant json.loads if client sends direct JSON
        start_year = requestdata['start_year']
        end_year = requestdata['end_year']
    except Exception as e:
        return jsonify({"error": f"Invalid request format: {str(e)}"}), 400

    StartDateTime=datetime(start_year, 1, 1, 0, 0)
    EndDateTime=datetime(end_year, 12, 31, 23) #Wind goes up to datetime(2013, 12, 31, 23)

    file_list=["GenCost_ATB_8MW_2020_Vestas","GenCost_ATB_12MW_2030","GenCost_ATB_15MW_2030", "GenCost_ATB_18MW_2030"]
    for file in file_list:
        ReferenceDataPath=str(path) + "./OutputData/Wind/"+ file +".npz"
        NewSavePath=str(path) + f"./OutputData/Wind/Upscale3h_0.1Degree_{start_year}_{end_year}_"+ file +".npz"
        _, _, _, _, _, _, _, _, _, _,_=ChangeTimeSpaceResolution (ReferenceDataPath, CurrentTimeResolution, NewTimeResolution, StepsPerDegree, StartDateTime, EndDateTime, NewSavePath=NewSavePath)
        print(NewSavePath)

    return jsonify({ 'message': 'The server executed this API call.' })

@app.route('/portfolioOptimization', methods=['POST'])
@cross_origin(origin='*', headers=['Content-Type', 'Authorization'])
def portfolioOptimization():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    PathWindDesigns=[]
    PathKiteDesigns=[]
    PathWaveDesigns=[]
    PathTransmissionDesign=[]
    GeneralPathResources="./OutputData/"


    try:
        requestdata = request.get_json()  # Use Flask's built-in JSON parsing
        # Remove redundant json.loads if client sends direct JSON
        winds = requestdata['wind']
        for wind in winds:
            PathWindDesigns.append(GeneralPathResources + wind)
        
        kites = requestdata['kite']
        for kite in kites:
            PathKiteDesigns.append(GeneralPathResources + kite)
        
        waves = requestdata['wave']
        for wave in waves:
            PathWaveDesigns.append(GeneralPathResources + wave)
        
        tranmissions = requestdata['transmission']
        for trasmission in tranmissions:
            PathTransmissionDesign.append(GeneralPathResources + trasmission)
        
        max_wind = requestdata['max_wind']
        min_wind = requestdata['min_wind']

        max_kite = requestdata['max_kite']
        min_kite = requestdata['min_kite']
        
        max_wave = requestdata['max_wave']
        min_wave = requestdata['min_wave']

        lcoe_max = requestdata['lcoe_max']
        lcoe_min = requestdata['lcoe_min']
        lcoe_step = requestdata['lcoe_step']


        LCOE_RANGE=range(lcoe_max,lcoe_min,-1*lcoe_step)
        Max_CollectionRadious=30
        MaxDesignsWind=max_wind
        MaxDesingsKite=max_kite

        MinNumWindTurb=min_wind
        MinNumKiteTrub=min_kite

        MaxDesingsWave=max_wave
        MinNumWaveTurb=min_wave

        print(PathWindDesigns)
        print(PathKiteDesigns)
        print(PathWaveDesigns)
        print(PathTransmissionDesign)
        
        for PathTransmissionDesign_i in (PathTransmissionDesign):
            for wi, PathWindDesigns_i in tqdm(enumerate(PathWindDesigns)):
                TurbineCaseName=PathWindDesigns_i.rsplit(r"/")[-1][:-4]
                TransmissionCaseName=PathTransmissionDesign_i.rsplit(r"/")[-1][:-4]
                
                SavePath=str(path) + "./OutputData/Portfolios/KiteWind_"+TurbineCaseName+"_"+TransmissionCaseName+f"_{datetime.today().strftime('%Y-%m-%d')}_{time.time()}"
                ReadMe=""
            
                #Create and solve the optimization problem
                SolvePortOpt_MaxGen_LCOE_Iterator([PathWindDesigns_i], PathWaveDesigns, PathKiteDesigns, PathTransmissionDesign_i, LCOE_RANGE,
                    Max_CollectionRadious, MaxDesignsWind, MaxDesingsWave, MaxDesingsKite, MinNumWindTurb, MinNumWaveTurb, MinNumKiteTrub,
                    ReadMe,SavePath=SavePath)
                print("Done with "+SavePath)

    except Exception as e:
        return jsonify({"error": f"Invalid request format: {str(e)}"}), 400

    return jsonify({ 'message': 'The server executed this API call.' })


@app.route('/generate-wind-binaries', methods=['GET', 'POST'])
@cross_origin(origin='*', headers=['Content-Type', 'Authorization'])
def generate_wind_binaries():
    #env Gurobi
    import numpy as np
    from datetime import datetime, timedelta
    import sys
    from tqdm import tqdm
    from multiprocessing import Pool

    from OceanPortfolioOptimization.Tools.Port_Opt_MaxGeneration import SolvePortOpt_MaxGen_LCOE_Iterator
    from OceanPortfolioOptimization.Tools.Multiprocessing.OnlyWindBOEM import Iterator_WindBOEM

    GeneralPathResources="OceanPortfolioOptimization/OutputData/"
    PathWindDesigns=[]

    PathWindDesigns.append(GeneralPathResources+"Wind/Upscale3h_0.1Degree_2007_2013_GenCost_ATB_18MW_2030.npz")
    PathWindDesigns.append(GeneralPathResources+"Wind/Upscale3h_0.1Degree_2007_2013_GenCost_ATB_15MW_2030.npz")
    PathWindDesigns.append(GeneralPathResources+"Wind/Upscale3h_0.1Degree_2007_2013_GenCost_ATB_12MW_2030.npz")
    PathWindDesigns.append(GeneralPathResources+"Wind/Upscale3h_0.1Degree_2007_2013_GenCost_ATB_8MW_2020_Vestas.npz")
    PathWindDesigns.append(GeneralPathResources+"Wind/BOEM_2007_Upscale3h_0.02Degree_GenCost_ATB_15MW_2030.npz")

    PathKiteDesigns=[]
    PathWaveDesigns=[]


    PathTransmissionDesign=[]
    #PathTransmissionDesign.append(GeneralPathResources+"Transmission/Transmission_1200MW.npz")
    #PathTransmissionDesign.append(GeneralPathResources+"Transmission/Transmission_1000MW.npz")
    #PathTransmissionDesign.append(GeneralPathResources+"Transmission/Transmission_600MW.npz")
    PathTransmissionDesign.append(GeneralPathResources+"Transmission/Transmission_300MW.npz")


    LCOE_RANGE=range(120,30,-2)
    Max_CollectionRadious=30
    MaxDesingsKite=1
    MaxDesignsWind=1
    MaxDesingsWave=0
    MinNumWindTurb=0
    MinNumWaveTurb=0
    MinNumKiteTrub=0


    LCOE_RANGE=list(range(120,30,-2))
    Max_CollectionRadious=30
    MaxDesingsKite=1
    MaxDesignsWind=1
    MaxDesingsWave=0
    MinNumWindTurb=0
    MinNumWaveTurb=0
    MinNumKiteTrub=0

    for PathTransmissionDesign_i in tqdm(PathTransmissionDesign):
        for wi, PathWindDesigns_i in enumerate(PathWindDesigns):
            TurbineCaseName=PathWindDesigns_i.rsplit(r"/")[-1][:-4]
            TransmissionCaseName=PathTransmissionDesign_i.rsplit(r"/")[-1][:-4]
            
            SavePath="OceanPortfolioOptimization/OutputData/Portfolios/Wind_"+TurbineCaseName+"_"+TransmissionCaseName+".npz"
            ReadMe="Case with wind on BOEM regions, considering a 1.2GW, 1.0, 0.6, 0.3 or 0.1GW transmission system, 30km radious and 1 design for each tech\
                    \n Wind designs: 8MW Vestas 2020, 12MW 2030, 15MW 2030, 18MW 2030"
            

            #Create and solve the optimization problem
            SolvePortOpt_MaxGen_LCOE_Iterator([PathWindDesigns_i], PathWaveDesigns, PathKiteDesigns, PathTransmissionDesign_i, LCOE_RANGE,
                Max_CollectionRadious,MaxDesignsWind, MaxDesingsWave, MaxDesingsKite,MinNumWindTurb,MinNumWaveTurb,MinNumKiteTrub,
                ReadMe,SavePath=SavePath)
    
    return jsonify({ 'message': 'The server executed this API call.' })

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

    wind()

    # return send_file('/', as_attachment=True)

def wind():
    MainPortResultsPath="./OceanPortfolioOptimization/OutputData/Portfolios/"
    SolutionPath=[]
    SolutionPath.append(MainPortResultsPath+"Wind_BOEM_2007_Upscale3h_0.02Degree_GenCost_ATB_15MW_2030_Transmission_1200MW.npz")
    SolutionPath.append(MainPortResultsPath+"Wind_BOEM_2007_Upscale3h_0.02Degree_GenCost_ATB_15MW_2030_Transmission_1000MW.npz")
    SolutionPath.append(MainPortResultsPath+"Wind_BOEM_2007_Upscale3h_0.02Degree_GenCost_ATB_15MW_2030_Transmission_600MW.npz")


    Legend=[] #one list per solution, each list contains the legend for each design of each technology 3d list
    Legend.append( [["Wind 18MW- TL 1.2GW"],
                    [],
                    []])

    Legend.append( [["Wind 18MW- TL 1.0GW"],
                    [],
                    []])

    Legend.append( [["Wind 18MW- TL 0.6GW"],
                    [],
                    []])

    LCOE_Target=-1 #Lowest LCOE
    StateCountours="./OceanPortfolioOptimization/InputData/CoastLine/"
    LatMaxMin=(33.3, 37.2)
    LongMaxMin=(-78.7, -74.3)

    PathDataUnderLayer=[]
    PathDataUnderLayer.append("./OceanPortfolioOptimization/OutputData/Wind/BOEM_Upscale24h_0.02Degree_GenCost_ATB_18MW_2030.npz")
    LegendUnderLayerColorbar=["Wind [pu]"]

    SavePath="/"
    PlotTurbineLocations(SolutionPath, Legend, PathDataUnderLayer, LegendUnderLayerColorbar, StateCountours,LCOE_Target=-1, LatMaxMin=(33.3, 37.2), LongMaxMin=(-78.7, -74.3), SavePath=SavePath)

@app.route('/get-wind-kites-energy-optimization', methods=['GET', 'POST'])
@cross_origin(origin='*', headers=['Content-Type', 'Authorization'])
def get_wind_kites__energy_optimization():
    GeneralPathResources="./OceanPortfolioOptimization/OutputData/"
    PathWindDesigns=[]

    PathWindDesigns.append(GeneralPathResources+"Wind/Upscale3h_0.1Degree_2007_2007_GenCost_ATB_18MW_2030.npz")

    PathKiteDesigns=[]
    PathKiteDesigns.append(GeneralPathResources+"OceanCurrent/PowerTimeSeriesKite_VD50_BCS2.5.npz")
    PathKiteDesigns.append(GeneralPathResources+"OceanCurrent/PowerTimeSeriesKite_VD50_BCS2.0.npz")
    PathKiteDesigns.append(GeneralPathResources+"OceanCurrent/PowerTimeSeriesKite_VD50_BCS1.5.npz")
    PathKiteDesigns.append(GeneralPathResources+"OceanCurrent/PowerTimeSeriesKite_VD50_BCS1.0.npz")
    PathWaveDesigns=[]


    PathTransmissionDesign=[]
    PathTransmissionDesign.append(GeneralPathResources+"Transmission/Transmission_1200MW.npz")


    LCOE_RANGE=[130,120,110,100,90,80,75,70,65,60,55,50,40,30,20,10]

    Max_CollectionRadious=30
    MaxDesingsKite=2
    MaxDesignsWind=1
    MaxDesingsWave=0
    MinNumWindTurb=0
    MinNumWaveTurb=0
    MinNumKiteTrub=0


    SavePath="./OutputData/Portfolios/Wind18MW_4KiteDesings_1200MW.npz"
    ReadMe="Test"

    # #Create and solve the optimization problem
    SolvePortOpt_MaxGen_LCOE_Iterator(PathWindDesigns, PathWaveDesigns, PathKiteDesigns, PathTransmissionDesign[0], LCOE_RANGE\
        ,Max_CollectionRadious,MaxDesignsWind, MaxDesingsWave, MaxDesingsKite,MinNumWindTurb,MinNumWaveTurb,MinNumKiteTrub\
        ,ReadMe,SavePath=SavePath)
    
def tmp():
    import numpy as np
    from datetime import datetime, timedelta
    import sys
    from tqdm import tqdm
    from multiprocessing import Pool

    from OceanPortfolioOptimization.Tools.Port_Opt_MaxGeneration import SolvePortOpt_MaxGen_LCOE_Iterator

    # from OceanPortfolioOptimization.Tools.Multiprocessing.OnlyWindBOEM import Iterator_WindBOEM
    # from OceanPortfolioOptimization.Tools.Multiprocessing.OnlyWindAll import Iterator_Wind

    GeneralPathResources="./OceanPortfolioOptimization/OutputData/"
    PathWindDesigns=[]

    PathWindDesigns.append(GeneralPathResources+"Wind/Upscale3h_0.1Degree_2007_2013_GenCost_ATB_18MW_2030.npz")
    PathWindDesigns.append(GeneralPathResources+"Wind/Upscale3h_0.1Degree_2007_2013_GenCost_ATB_15MW_2030.npz")
    PathWindDesigns.append(GeneralPathResources+"Wind/Upscale3h_0.1Degree_2007_2013_GenCost_ATB_12MW_2030.npz")
    PathWindDesigns.append(GeneralPathResources+"Wind/Upscale3h_0.1Degree_2007_2013_GenCost_ATB_8MW_2020_Vestas.npz")

    PathKiteDesigns=[]
    PathWaveDesigns=[]


    PathTransmissionDesign=[]
    #PathTransmissionDesign.append(GeneralPathResources+"Transmission/Transmission_1200MW.npz")
    #PathTransmissionDesign.append(GeneralPathResources+"Transmission/Transmission_1000MW.npz")
    #PathTransmissionDesign.append(GeneralPathResources+"Transmission/Transmission_600MW.npz")
    PathTransmissionDesign.append(GeneralPathResources+"Transmission/Transmission_300MW.npz")


    LCOE_RANGE=range(120,30,-2)
    Max_CollectionRadious=30
    MaxDesingsKite=1
    MaxDesignsWind=1
    MaxDesingsWave=0
    MinNumWindTurb=0
    MinNumWaveTurb=0
    MinNumKiteTrub=0


    LCOE_RANGE=list(range(120,30,-2))

@app.route('/generate', methods=['GET', 'POST'])
@cross_origin(origin='*', headers=['Content-Type', 'Authorization'])
def generate():
    requestdata = json.loads(request.data)
    requestdata = json.loads(requestdata['body'])
    print(requestdata)

    from Tools.Port_Opt_MaxGeneration import SolvePortOpt_MaxGen_LCOE_Iterator

    GeneralPathResources="OutputData/"
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
    MaxDesingsKite=0
    MaxDesignsWind=1
    
    MinNumWindTurb=1
    MinNumKiteTrub=0
    
    MaxDesingsWave=0
    MinNumWaveTurb=0

    for PathTransmissionDesign_i in tqdm(PathTransmissionDesign):
        for wi, PathWindDesigns_i in enumerate(PathWindDesigns):
            TurbineCaseName=PathWindDesigns_i.rsplit(r"/")[-1][:-4]
            TransmissionCaseName=PathTransmissionDesign_i.rsplit(r"/")[-1][:-4]
            
            SavePath="OutputData/Portfolios/KiteWind_"+TurbineCaseName+"_"+TransmissionCaseName+"_18MW-12MWT-LCOE_3.npz"
            print(SavePath)
            ReadMe="Case with wind on BOEM regions, considering a 1.2GW, 1.0, 0.6, 0.3 or 0.1GW transmission system, 30km radious and 1 design for each tech\
                    \n Wind designs: 8MW Vestas 2020, 12MW 2030, 15MW 2030, 18MW 2030"
            

            #Create and solve the optimization problem
            SolvePortOpt_MaxGen_LCOE_Iterator([PathWindDesigns_i], PathWaveDesigns, PathKiteDesigns, PathTransmissionDesign_i, LCOE_RANGE, Max_CollectionRadious,MaxDesignsWind, MaxDesingsWave, MaxDesingsKite,MinNumWindTurb,MinNumWaveTurb,MinNumKiteTrub, ReadMe,SavePath=SavePath)
            print(f"Done with {SavePath}")

    return jsonify({ 'result': 'Executed API' }) 
    

if __name__ == '__main__':
    # tmp()
    app.run('0.0.0.0', 4000, debug=True)