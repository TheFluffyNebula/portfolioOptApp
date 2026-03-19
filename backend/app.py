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
import os
import io
from PIL import Image

from OceanPortfolioOptimization.Tools.DownloadNREL_Wind import DonwloadNREL_WindData
from OceanPortfolioOptimization.Tools.GeneralGeoTools import PlotTurbineLocations, ChangeTimeSpaceResolution
from Tools.Port_Opt_MaxGeneration import SolvePortOpt_MaxGen_LCOE_Iterator
from gurobipy import *
from pathlib import Path
import traceback

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

# @app.route('/getWindEnergyCostGeneration', methods=['POST'])
# @cross_origin(origin='*', headers=['Content-Type', 'Authorization'])
# def getWindEnergyCostGeneration():
#     CurrentTimeResolution=1 #in hours
#     NewTimeResolution=3 #3hour time discretization
#     StepsPerDegree=10 #New grid resolution 1/StepsPerDegree (If you want the same resolution as the BOEM data, set this to 100 as it will filter sites with no data)

#     if not request.is_json:
#         return jsonify({"error": "Request must be JSON"}), 400

#     try:
#         requestdata = request.get_json()  # Use Flask's built-in JSON parsing
#         # Remove redundant json.loads if client sends direct JSON
#         start_year = requestdata['start_year']
#         end_year = requestdata['end_year']
#     except Exception as e:
#         return jsonify({"error": f"Invalid request format: {str(e)}"}), 400

#     StartDateTime=datetime(start_year, 1, 1, 0, 0)
#     EndDateTime=datetime(end_year, 12, 31, 23) #Wind goes up to datetime(2013, 12, 31, 23)

#     file_list=["GenCost_ATB_8MW_2020_Vestas","GenCost_ATB_12MW_2030","GenCost_ATB_15MW_2030", "GenCost_ATB_18MW_2030"]
#     for file in file_list:
#         ReferenceDataPath=str(path) + "./OutputData/Wind/"+ file +".npz"
#         NewSavePath=str(path) + f"./OutputData/Wind/Upscale3h_0.1Degree_{start_year}_{end_year}_"+ file +".npz"
#         _, _, _, _, _, _, _, _, _, _,_=ChangeTimeSpaceResolution (ReferenceDataPath, CurrentTimeResolution, NewTimeResolution, StepsPerDegree, StartDateTime, EndDateTime, NewSavePath=NewSavePath)
#         print(NewSavePath)

#     return jsonify({ 'message': 'The server executed this API call.' })

@app.route('/resourceUpload', methods=['POST'])
@cross_origin(origin='*', headers=['Content-Type', 'Authorization'])
def resourceUpload():
    try:
        data = request.get_json()
        print(f"Received data: {data}")
    except Exception as e:
        print(f"JSON parse error: {str(e)}")
        
    try:
        from werkzeug.utils import secure_filename
        files = request.files.getlist('files')
        print(files)
        saved_files = []
        for file in files:
            if file and file.filename:
                filename = secure_filename(file.filename)
                if "PowerTimeSeriesKite" in filename:
                    print(f"Saving to {os.path.join('./OutputData/OceanCurrent', filename)}")
                    print(os.path.exists(os.path.join('./OutputData/OceanCurrent', filename)))
                    file.save(os.path.join('./OutputData/OceanCurrent', filename))
                saved_files.append(filename)

    except Exception as e:
        print(traceback.format_exc())
        return jsonify({"error": f"Invalid request format: {str(e)}"}), 400

    return jsonify({'message': f'{len(saved_files)} file(s) uploaded successfully', 'files': saved_files}), 200

@app.route('/windInputGeneration', methods=['POST'])
@cross_origin(origin='*', headers=['Content-Type', 'Authorization'])
def windInputGeneration():
    try:
        data = request.get_json()
        print(f"Received data: {data}")
    except Exception as e:
        print(f"JSON parse error: {str(e)}")
        
    required_fields = ['wind', 'min_year', 'max_year']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    CurrentTimeResolution=1 #in hours
    NewTimeResolution=3 #3hour time discretization
    StepsPerDegree=10 #New grid resolution 1/StepsPerDegree (If you want the same resolution as the BOEM data, set this to 100 as it will filter sites with no data)

    try:
        requestdata = request.get_json()
        min_year = requestdata['min_year']
        max_year = requestdata['max_year']
        winds = requestdata['wind']
        StartDateTime=datetime(min_year, 1, 1, 0, 0)
        EndDateTime=datetime(max_year, 12, 31, 23) #Wind goes up to datetime(2013, 12, 31, 23)

        winds = ["GenCost" + wind.split("GenCost")[-1].split(".")[0] for wind in winds]

        import os
        from pathlib import Path

        file_list=winds
        for file in file_list:
            ReferenceDataPath="./OutputData/Wind/"+ file +".npz"
            NewSavePath=f"./OutputData/Wind/Upscale3h_0.1Degree_{min_year}_{max_year}_"+ file +".npz"
            if not os.path.exists(NewSavePath):
                _, _, _, _, _, _, _, _, _, _,_=ChangeTimeSpaceResolution (ReferenceDataPath, CurrentTimeResolution, NewTimeResolution, StepsPerDegree, StartDateTime, EndDateTime, NewSavePath=NewSavePath)
            else:
                print(f"{NewSavePath} already exists")

    except Exception as e:
        print(traceback.format_exc())
        return jsonify({"error": f"Invalid request format: {str(e)}"}), 400

    return jsonify({ 'message': 'The server executed this API call.' })

def merge_kite_years(min_year, max_year, BCS):
    # Merge range of years for each kite design
    import datetime as dt
    years = range(min_year, max_year)
    VerticalDepth=[50, 100, 150, 200]
    i_vd=0

    # Skip merge if the output file already exists (e.g. uploaded by user)
    output_path = './OutputData/OceanCurrent/' + 'PowerTimeSeriesKite_VD' + str(VerticalDepth[i_vd]) + '_BCS' + str(BCS) + f'_{min_year}_{max_year}.npz'
    if os.path.exists(output_path):
        print(f"{output_path} already exists, skipping merge.")
        return

    for year in tqdm(years):
        SavePowerTimeSeriesPath='./OutputData/OceanCurrent/'+str(year)+"_"
        PathKiteParams=SavePowerTimeSeriesPath+'PowerTimeSeriesKite_VD'+str(VerticalDepth[i_vd])+'_BCS'+str(BCS)+'.npz'
        Data=np.load(PathKiteParams,allow_pickle=True)

        Energy_pu=Data['Energy_pu']
        RawResource=Data['RawResource']
        TimeList=Data['TimeList']
        LatLong=Data['LatLong']
        Depth=Data['Depth']
        DistanceShore=Data['DistanceShore']
        CAPEX_site=Data['CAPEX_site']
        OPEX_site=Data['OPEX_site']
        AnnualizedCost=Data['AnnualizedCost']
        NumberOfCellsPerSite=Data['NumberOfCellsPerSite']
        RatedPower=Data['RatedPower']
        ResolutionDegrees=Data['ResolutionDegrees']
        ResolutionKm=Data['ResolutionKm']
        MatlabSiteIdx=Data['MatlabSiteIdx']
        StructuralMass=Data['StructuralMass']
        Span=Data['Span']
        AspectRatio=Data['AspectRatio']
        Length=Data['Length']
        Diameter=Data['Diameter']

        if year==np.min(years):
            Energy_pu_all=Energy_pu
            RawResource_all=RawResource
            TimeList_all=TimeList
            LatLong_all=LatLong
            Depth_all=Depth
            DistanceShore_all=DistanceShore
            CAPEX_site_all=CAPEX_site
            OPEX_site_all=OPEX_site
            AnnualizedCost_all=AnnualizedCost
            NumberOfCellsPerSite_all=NumberOfCellsPerSite
            RatedPower_all=RatedPower
            ResolutionDegrees_all=ResolutionDegrees
            ResolutionKm_all=ResolutionKm
            MatlabSiteIdx_all=MatlabSiteIdx
            StructuralMass_all=StructuralMass
            Span_all=Span
            AspectRatio_all=AspectRatio
            Length_all=Length
            Diameter_all=Diameter

        else:
            IdxSpecific=[]
            for i in range(len(LatLong_all)):
                # Find matching indices in LatLong where both latitude and longitude match
                matches = np.where((LatLong[:, 0] == LatLong_all[i, 0]) & (LatLong[:, 1] == LatLong_all[i, 1]))[0]
                if matches.size > 0:
                    # Add the first matching index to the list
                    IdxSpecific.append(matches[0])
            
            LatLong=LatLong[IdxSpecific,:]
            Energy_pu=Energy_pu[:,IdxSpecific]
            RawResource=RawResource[IdxSpecific]



            IdxAll=[]
            for i in range(len(LatLong)):
                # Find matching indices in LatLong_all where both latitude and longitude match
                matches = np.where((LatLong_all[:, 0] == LatLong[i, 0]) & (LatLong_all[:, 1] == LatLong[i, 1]))[0]
                if matches.size > 0:
                    # Add the first matching index to the list
                    IdxAll.append(matches[0])
            
            LatLong_all=LatLong_all[IdxAll,:]
            Depth_all=Depth_all[IdxAll]
            DistanceShore_all=DistanceShore_all[IdxAll]
            AnnualizedCost_all=AnnualizedCost_all[IdxAll]
            NumberOfCellsPerSite_all=NumberOfCellsPerSite_all[IdxAll]
            MatlabSiteIdx_all=MatlabSiteIdx_all[IdxAll]
            Energy_pu_all=Energy_pu_all[:,IdxAll]
            RawResource_all=RawResource_all[IdxAll]

            Energy_pu_all=np.concatenate((Energy_pu_all,Energy_pu),axis=0)

            RawResource_all=(RawResource+RawResource_all)/2            

        SavePowerTimeSeriesPath='./OutputData/OceanCurrent/'
        PathKiteParams=SavePowerTimeSeriesPath+'PowerTimeSeriesKite_VD'+str(VerticalDepth[i_vd])+'_BCS'+str(BCS)+f'_{min_year}_{max_year}.npz'
        
        #Hard code correction for time from 2007 to 2013 in 3hour steps
        TimeList_all=[dt.datetime(2007, 1, 1, 0, 0) + dt.timedelta(hours=3*i) for i in range(Energy_pu_all.shape[0])]
        np.savez(PathKiteParams,Energy_pu=Energy_pu_all,RawResource=RawResource_all,
                    TimeList=TimeList_all,LatLong=LatLong_all,Depth=Depth_all,DistanceShore=DistanceShore_all,
                    CAPEX_site=CAPEX_site_all,OPEX_site=OPEX_site_all,AnnualizedCost=AnnualizedCost_all,
                    NumberOfCellsPerSite=NumberOfCellsPerSite_all,RatedPower=RatedPower_all,ResolutionDegrees=ResolutionDegrees_all,
                    ResolutionKm=ResolutionKm_all,MatlabSiteIdx=MatlabSiteIdx_all,StructuralMass=StructuralMass_all,
                    Span=Span_all,AspectRatio=AspectRatio_all,Length=Length_all,Diameter=Diameter_all)


@app.route('/kiteInputGeneration', methods=['POST'])
@cross_origin(origin='*', headers=['Content-Type', 'Authorization'])
def kiteInputGeneration():
    try:
        data = request.get_json()
        print(f"Received data: {data}")
    except Exception as e:
        print(f"JSON parse error: {str(e)}")
        
    required_fields = ['kite', 'min_year', 'max_year']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    # from Tools.KitePortfolioTools import WriteMatlabInputs2Kites, TimeSeriesGeneration_Kite
    try:
        requestdata = request.get_json()
        min_year = requestdata['min_year']
        max_year = requestdata['max_year']
        kites = requestdata['kite']
        PathKiteParams="./Tools/KitesMatlab/KiteParameters/power_objective.xlsx"
        NumEnvs=30
        i_vd=0 #50m depth

        for kite in kites:
            st = kite
            VD = 0
            BCS = 0
            for it in st.split('_'):
                if 'VD' in it:
                    VD = int(it.split('VD')[-1])
                if 'BCS' in it:
                    BCS = float(it.split('BCS')[-1])
            
            if max_year == min_year:
                import shutil
                source_file = './OutputData/OceanCurrent/' + f'{min_year}_' + 'PowerTimeSeriesKite_VD'+str(VD)+'_BCS'+str(BCS)+'.npz'
                base, ext = os.path.splitext(source_file)
        
                # Construct the path for the new file
                new_file = './OutputData/OceanCurrent/' + 'PowerTimeSeriesKite_VD'+str(VD)+'_BCS'+str(BCS) + f"_{min_year}_{max_year}.npz"
                
                # Copy the file with the new name
                shutil.copy2(source_file, new_file)
                print(f"File '{source_file}' copied to '{new_file}'")
            else:
                for year in tqdm(range(min_year,max_year)):
                    StartDTime=datetime(year, 1, 1, 0, 0, 0) #datetime(2007, 1, 1, 0, 0, 0) 
                    EndDTime  =datetime(year, 12, 31, 23, 0, 0) #datetime(2013, 12, 31, 23, 0, 0)

                    SaveMatPath="./InputData/OceanCurrent/"
                    FullMatlabHycomDataPath=SaveMatPath+"OCSpeedHycom_"+StartDTime.strftime("%Y%m%d")+"_"+EndDTime.strftime("%Y%m%d")+".mat"
                    SavePowerTimeSeriesPath='./OutputData/OceanCurrent/'+str(year)+"_"

                    if not os.path.isfile(SavePowerTimeSeriesPath+'PowerTimeSeriesKite_VD'+str(VD)+'_BCS'+str(BCS)+'.npz'):
                        Test=1
                        while Test==1:
                            try:
                                print("Running year "+str(year)+" VD "+str(VD)+" BCS "+str(BCS))
                                # TimeSeriesGeneration_Kite(PathKiteParams, i_vd, i_cs, SavePowerTimeSeriesPath, FullMatlabHycomDataPath, NumEnvs=NumEnvs)
                                Test=0

                                try:

                                    os.system("taskkill /f /im  MATLAB.exe")
                                    os.system("taskkill /f /im  MathWorksServiceHost.exe")
                                    os.system("taskkill /f /im  MathWorksServiceHost-Monitor.exe")

                                except:
                                    pass


                            except:
                                print("Error in year "+str(year)+" VD "+str(VD)+" BCS "+str(BCS))
                                print("\nWe will kill the matlab process and try again\n")
                    else:
                        print(SavePowerTimeSeriesPath+'PowerTimeSeriesKite_VD'+str(VD)+'_BCS'+str(BCS)+'.npz already exists')
            merge_kite_years(min_year, max_year, BCS)
        
    except Exception as e:
        print(traceback.format_exc())
        return jsonify({"error": f"Invalid request format: {str(e)}"}), 400

    return jsonify({ 'message': 'The server executed this API call.' })

@app.route('/waveInputGeneration', methods=['POST'])
@cross_origin(origin='*', headers=['Content-Type', 'Authorization'])
def waveInputGeneration():
    try:
        data = request.get_json()
        print(f"Received data: {data}")
    except Exception as e:
        print(f"JSON parse error: {str(e)}")
        
    required_fields = ['wave', 'min_year', 'max_year']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
        
    import numpy as np
    import datetime
    import os

    try:
        requestdata = request.get_json()
        min_year = requestdata['min_year']
        max_year = requestdata['max_year']
        waves = requestdata['wave']

        for wave in waves:
            if not os.path.exists(f'./OutputData/{wave}'):
                wave_type = 'Pelamis' if 'Pelamis' in wave else 'RM3'
                source_wave_file = f'./OutputData/Wave/2005_2019_{wave_type}.npz'
                with np.load(source_wave_file, allow_pickle=True) as data:
                    time_list = data['TimeList']  # assuming shape (39700,)
                    
                    # Create mask by comparing the year attribute (2009 <= year <= 2013)
                    mask = np.array([min_year <= dt.year <= max_year for dt in time_list])
                    
                    # Use the same mask for arrays with shape (39700, 122)
                    energy_pu = data['Energy_pu']       # shape (39700, 122)
                    raw_resource = data['RawResource']    # shape (39700, 122)
                    
                    filtered_energy = energy_pu[mask, :]
                    filtered_resource = raw_resource[mask, :]
                    filtered_time = time_list[mask]
                    
                    print("Filtered TimeList:", filtered_time)
                    print("Filtered TimeList Shape:", filtered_time.shape)
                    print("Filtered Energy_pu shape:", filtered_energy.shape)

                    np.savez(f'./OutputData/{wave}', 
                            Energy_pu=filtered_energy, RawResource=filtered_resource, TimeList=filtered_time, LatLong=data["LatLong"], Depth=data['Depth'], DistanceShore=data['DistanceShore'],
                            CAPEX_site=data['CAPEX_site'], OPEX_site=data['OPEX_site'], AnnualizedCost=data['AnnualizedCost'], NumberOfCellsPerSite=data['NumberOfCellsPerSite'],
                            RatedPower=data['RatedPower'], ResolutionDegrees=data['ResolutionDegrees'], ResolutionKm=data['ResolutionKm'], LCOE=data['LCOE'])
            else:
                print(f"{f'./OutputData/{wave}'} already exists")
            
    except Exception as e:
        print(traceback.format_exc())
        return jsonify({"error": f"Invalid request format: {str(e)}"}), 400

    return jsonify({ 'message': 'The server executed this API call.' })

@app.route('/portfolioOptimization', methods=['POST'])
@cross_origin(origin='*', headers=['Content-Type', 'Authorization'])
def portfolioOptimization():
    try:
        data = request.get_json()
        print(f"Received data: {data}")
    except Exception as e:
        print(f"JSON parse error: {str(e)}")
        
    required_fields = ['wind', 'wave', 'kite', 'transmission']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    PathWindDesigns=[]
    PathKiteDesigns=[]
    PathWaveDesigns=[]
    PathTransmissionDesign=[]
    PathCoaxialDesigns = []
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

        coaxials = requestdata['coaxial']
        for coaxial in coaxials:
            PathCoaxialDesigns.append(GeneralPathResources + coaxial)
        
        tranmissions = requestdata['transmission']
        for trasmission in tranmissions:
            PathTransmissionDesign.append(GeneralPathResources + trasmission)
        
        max_wind = requestdata['max_wind']
        min_wind = requestdata['min_wind']

        max_kite = requestdata['max_kite']
        min_kite = requestdata['min_kite']
        
        max_wave = requestdata['max_wave']
        min_wave = requestdata['min_wave']

        max_coaxial = requestdata['max_coaxial']
        min_coaxial = requestdata['min_coaxial']

        lcoe_max = requestdata['lcoe_max']
        lcoe_min = requestdata['lcoe_min']
        lcoe_step = requestdata['lcoe_step']
        max_system_radius = requestdata['max_system_radius']
        WindTurbinesPerSite = requestdata['WindTurbinesPerSite']
        KiteTurbinesPerSite = requestdata['KiteTurbinesPerSite']
        WaveTurbinesPerSite = requestdata['WaveTurbinesPerSite']
        CoaxialTurbinesPerSite = requestdata['CoaxialTurbinesPerSite']


        LCOE_RANGE=range(lcoe_max,lcoe_min,-1*lcoe_step)
        Max_CollectionRadious=max_system_radius
        MaxDesignsWind=max_wind
        MaxDesingsKite=max_kite

        MinNumWindTurb=min_wind
        MinNumKiteTrub=min_kite

        MaxDesingsWave=max_wave
        MinNumWaveTurb=min_wave

        MaxDesingsCoaxial=max_coaxial
        MinNumCoaxialTurb=min_coaxial

        print(PathWindDesigns)
        print(PathKiteDesigns)
        print(PathWaveDesigns)
        print(PathTransmissionDesign)
        print(PathCoaxialDesigns)

        def join_after_last_slash(file_list):
            if not file_list:
                return "0"
            
            # Extract the portion after the last '/' for each string in the list
            extracted_parts = [item.split('/')[-1] for item in file_list]
            
            # Join the extracted parts with '#'
            result = '#'.join(extracted_parts)
            
            return result
        
        SavePaths = []
        
        for PathTransmissionDesign_i in (PathTransmissionDesign):
            for wi, PathWindDesigns_i in tqdm(enumerate(PathWindDesigns)):
                TurbineCaseName=PathWindDesigns_i.rsplit(r"/")[-1][:-4]
                TransmissionCaseName=PathTransmissionDesign_i.rsplit(r"/")[-1][:-4]
                
                SavePath="./OutputData/Portfolios/"+TransmissionCaseName+"$"+TurbineCaseName+"$"+join_after_last_slash(PathKiteDesigns)+"$"+join_after_last_slash(PathWaveDesigns)+"$"+join_after_last_slash(PathCoaxialDesigns)+f"$max={lcoe_max}$min={lcoe_min}$step={lcoe_step}"
                ReadMe=""

                SavePaths.append(SavePath + '.npz')
            
                #Create and solve the optimization problem
                if not os.path.exists(SavePath + '.npz'):
                    SolvePortOpt_MaxGen_LCOE_Iterator([PathWindDesigns_i], PathWaveDesigns, PathKiteDesigns, PathCoaxialDesigns, PathTransmissionDesign_i, LCOE_RANGE,
                        Max_CollectionRadious, MaxDesignsWind, MaxDesingsWave, MaxDesingsKite, MinNumWindTurb, MinNumWaveTurb, MinNumKiteTrub, MaxDesingsCoaxial, MinNumCoaxialTurb,
                        ReadMe,SavePath=SavePath, WindTurbinesPerSite=WindTurbinesPerSite, KiteTurbinesPerSite=KiteTurbinesPerSite, WaveTurbinesPerSite=WaveTurbinesPerSite, CoaxialTurbinesPerSite=CoaxialTurbinesPerSite)
                else:
                    print(f"{SavePath} already exists")
                print("Done with "+SavePath)

    except Exception as e:
        print(traceback.format_exc())
        return jsonify({"error": f"Invalid request format: {str(e)}"}), 400

    return jsonify({ 'message': 'The server executed this API call.', 'save_path': SavePaths })

@app.route('/portfolioPlots', methods=['POST'])
@cross_origin(origin='*', headers=['Content-Type', 'Authorization'])
def portfolioPlots():
    try:
        data = request.get_json()
        print(f"Received data: {data}")
    except Exception as e:
        print(f"JSON parse error: {str(e)}")
        
    required_fields = ['portfolio']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    try:
        requestdata = request.get_json()  # Use Flask's built-in JSON parsing
        print(requestdata)
        # Remove redundant json.loads if client sends direct JSON
        portfolio_location = requestdata['portfolio']
        print("PRINTING => ", portfolio_location)
        portfolio_location = portfolio_location[0].split('./OutputData/Portfolios/')[-1]
        print(portfolio_location)
        
        from OceanPortfolioOptimization.Tools.GeneralGeoTools import PlotEfficientFrontier

        SolutionPaths=[]
        MainPortResultsPath="./OutputData/Portfolios/"

        SolutionPaths.append(MainPortResultsPath+portfolio_location)

        resource_type = {
            '8MW_2020_Vestas': '8MW Vestas 2020',
            '12MW_2030': '12MW 2030',
            '15MW_2030': '15MW 2030',
            '18MW_2030': '18MW 2030',
            'PowerTimeSeriesKite_VD50_BCS0.5': '0.05MW (0.5m/s)',
            'PowerTimeSeriesKite_VD50_BCS0.75': '0.14MW (0.75m/s)',
            'PowerTimeSeriesKite_VD50_BCS1.0': '0.31MW (1.0m/s)',
            'PowerTimeSeriesKite_VD50_BCS1.25': '0.57MW (1.25m/s)',
            'PowerTimeSeriesKite_VD50_BCS1.5': '0.93MW (1.5m/s)',
            'PowerTimeSeriesKite_VD50_BCS1.75': '1.43MW (1.75m/s)',
            'PowerTimeSeriesKite_VD50_BCS2.0': '2.04MW (2.0m/s)',
            'PowerTimeSeriesKite_VD50_BCS2.25': '1.987MW (2.25m/s)',
            'PowerTimeSeriesKite_VD50_BCS2.5': '1.87MW (2.5m/s)',
            'PowerTimeSeriesKite_VD50_BCS2.75': '1.81MW (2.75m/s)',
            'Pelamis': 'Pelamis',
            'RM3': 'RM3'
        }

        resource_names = ""
        for key, val in resource_type.items():
            if key in portfolio_location:
                resource_names += val + '\n'

        print(resource_names)
        Legend=[resource_names]
        # Legend = []
                
        linestyle=['-','-','--','-.','-','--','-.','-','--','-.']
        ColorList=['tab:orange','k','k','k',"b","b","b","r","r","r"]
        Marker = [None] * len(SolutionPaths)
                
        SavePath="./OutputData/Plots/Portfolios/UI.png"

        try: 
            os.remove(SavePath)
        except:
            print("NO PLOT DETECTED")

        PlotEfficientFrontier(SolutionPaths, Legend,linestyle=linestyle, ColorList=ColorList, Marker=Marker, Title=None, SavePath=SavePath)

    except Exception as e:
        return jsonify({"error": f"Invalid request format: {str(e)}"}), 400
    
    if os.path.exists(SavePath):
        return send_file(SavePath, mimetype='image/png', as_attachment=False)
        # with Image.open(SavePath) as img:
        #     # Resize the image
        #     img = img.resize((700, 400), Image.LANCZOS)
            
        #     # Save to a bytes buffer
        #     buf = io.BytesIO()
        #     img.save(buf, format='PNG')
        #     buf.seek(0)
            
        # return send_file(buf, mimetype='image/jpeg')
    else:
        return jsonify({"error": f"Plot not found at {SavePath}"}), 404


@app.route('/generateWindBinaries', methods=['GET', 'POST'])
@cross_origin(origin='*', headers=['Content-Type', 'Authorization'])
def generate_wind_binaries():
    try:
        data = request.get_json()
        print(f"Received data: {data}")
    except Exception as e:
        print(f"JSON parse error: {str(e)}")
        
    required_fields = ['WindTurbine', 'ResolutionKm']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    try:
        requestdata = request.get_json() 
        WindTurbine = requestdata['WindTurbine']
        ResolutionKm = requestdata['ResolutionKm']
        from Tools.WindTurbineTools import WindToEnergy, GetTurbineData, FilterOnDepthShoreDistance, GetCostAndGenerationWindTurbine, FilterForWTKDataset, FilterForBOEM
        InputDataPath="./InputData"
        GeoDataPath=InputDataPath+"/CoastLine/"
        # WindTurbine="ATB_15MW_2030" #Name of the wind turbine file

        WindCostPath=InputDataPath+"/Wind/CostWindTurbines.xlsx"

        WindSpeedHeightsAvailable={"100":"windspeed_100m.npz",
                                "140":"windspeed_140m.npz",
                                "160":"windspeed_160m.npz"}
        for tb in WindTurbine:
            WindEnergy_pu, RatedPower, LatLong, WS_Hub, Depth, DistanceShore, TRG_site, CAPEX_site, OPEX_site, AnnualizedCost, TimeList,_=GetCostAndGenerationWindTurbine(InputDataPath, WindCostPath, WindTurbine=tb, WindSpeedHeightsAvailable=WindSpeedHeightsAvailable, SavePath=f"./OutputData/Wind/GenCost_{tb}.npz", ResolutionKm=ResolutionKm) 
    
    except Exception as e:
        return jsonify({"error": f"Invalid request format: {str(e)}"}), 400
    
    return jsonify({ 'message': 'The server executed this API call.' })


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