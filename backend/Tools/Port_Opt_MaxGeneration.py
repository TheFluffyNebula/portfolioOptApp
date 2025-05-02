#This code compute the optimal portfolio for wave wind and ocean current resources
#Considering transmission system costs, CAPEX and OPEX of each technology and its generation availability in a given region

#The objective function is the maximization of the total generation of the portfolio, costraint to limits in the portfolio LCOE, maximum
#Capacity of the transmission system, maximum number of turbines per site location, and maxmimum radious of the energy collection system.

#The model also takes into considering curtailment, and the possibility of chosing from a limited number of turbine desings.

#env Gurobi
import numpy as np
from pyomo.environ import *
import pandas as pd
from datetime import datetime, timedelta
from tqdm import tqdm
import sys

from Tools.GetIdxInOutRadious import GetIdxOutRadious, GetIdxInRadious_Simple
from Tools.Port_Opt_Tools import GetOverlaps_Idx_Area


def PreparePotOptInputs(PathWindDesigns, PathWaveDesigns, PathKiteDesigns, PathCoaxialDesigns, PathTransmissionDesign, LCOE_RANGE=range(200,30,-2)\
    ,Max_CollectionRadious=30, MaxDesignsWind=1, MaxDesignsWave=1, MaxDesignsKite=1, MinNumWindTurb=0, MinNumWaveTurb=0, MinNumKiteTrub=0, MaxDesingsCoaxial=1, MinNumCoaxialTurb=0,
    WindTurbinesPerSite=4, KiteTurbinesPerSite=390, WaveTurbinesPerSite=300, CoaxialTurbinesPerSite=390):
    
    
    # WindTurbinesPerSite= 4 [MW/Km2]
    # KiteTurbinesPerSite= 25 per 2x2km cells, but the simulation is running on 0.08x0.08 degrees cells (as base resolution)
    # KiteTurbinesPerSite= 390 per 9x7km cells
    # WaveTurbinesPerSite=  1/15degees , from pelamis 12.5 devices per km2. This would be +500 devices, using 300 for now

    #WindTurbinesPerSite: Number of turbines per site location based on the initial wind resolution from NREL
    #KiteTurbinesPerSite: Number of turbines per site location based on the initial kite resolution from where the data was obtained (HYCOM, MABSAB)
    #WaveTurbinesPerSite: Number of turbines per site location based on the initial wave resolution from where the data was obtained (WWIII)  
    
    #Function to prepare the inputs for the optimization
    #All portfolio data needs to be at the same time resolution and range, unless the portfolio path is empty eg. PathWaveDesigns=[]
    # LCOE_RANGE=range(200,30,-2) #Max LCOE limits investigated
    # Max_CollectionRadious=30 #Radious for the energy collection system

    WindEnergy, WindLatLong, AnnualizedCostWind, MaxNumWindPerSite, WindDesign, TimeWindData,\
    RatedPowerWindTurbine, WindResolutionDegrees, WindResolutionKm = list(), list(), list(), list(), list(), list(), list(), list(), list()
    
    KiteEnergy, KiteLatLong, AnnualizedCostKite, MaxNumKitePerSite, KiteDesign, TimeKiteData,\
    RatedPowerKiteTurbine, KiteResolutionDegrees, KiteResolutionKm = list(), list(), list(), list(), list(), list(), list(), list(), list()
    
    WaveEnergy, WaveLatLong, AnnualizedCostWave, MaxNumWavePerSite, WaveDesign, TimeWaveData,\
    RatedPowerWaveTurbine, WaveResolutionDegrees, WaveResolutionKm = list(), list(), list(), list(), list(), list(), list(), list(), list()

    CoaxialEnergy, CoaxialLatLong, AnnualizedCostCoaxial, MaxNumCoaxialPerSite, CoaxialDesign, TimeCoaxialData,\
    RatedPowerCoaxialTurbine, CoaxialResolutionDegrees, CoaxialResolutionKm = list(), list(), list(), list(), list(), list(), list(), list(), list()
    
    for i in range(len(PathWindDesigns)):
        Data=np.load(PathWindDesigns[i],allow_pickle=True)
        if i==0:
            
            WindEnergy=Data['Energy_pu']
            WindLatLong=Data['LatLong']
            AnnualizedCostWind=Data['AnnualizedCost']
            WindDesign=np.array([i]*len(Data["NumberOfCellsPerSite"]))
            TimeWindData=Data["TimeList"]
            RatedPowerWindTurbine=np.array([float(Data["RatedPower"])]*len(Data["NumberOfCellsPerSite"]))
            WindResolutionDegrees=np.array([float(Data["ResolutionDegrees"])]*len(Data["NumberOfCellsPerSite"]))
            WindResolutionKm=np.array([float(Data["ResolutionKm"])]*len(Data["NumberOfCellsPerSite"]))
            
            #work with wind using MW/Km2
            TubPerSite=np.max([WindTurbinesPerSite*4/float(Data["RatedPower"]),1])
            MaxNumWindPerSite=Data["NumberOfCellsPerSite"]*TubPerSite
            
            TimeList=TimeWindData
            
            
        else:
            WindEnergy=np.concatenate((WindEnergy,Data['Energy_pu']),axis=1)
            WindLatLong=np.concatenate((WindLatLong,Data['LatLong']))
            AnnualizedCostWind=np.concatenate((AnnualizedCostWind,Data['AnnualizedCost']))
            
            WindDesign=np.concatenate((WindDesign,[i]*len(Data["NumberOfCellsPerSite"])))
            RatedPowerWindTurbine=np.concatenate((RatedPowerWindTurbine,np.array([float(Data["RatedPower"])]*len(Data["NumberOfCellsPerSite"]))))
            WindResolutionDegrees=np.concatenate((WindResolutionDegrees, np.array([float(Data["ResolutionDegrees"])]*len(Data["NumberOfCellsPerSite"]))))
            WindResolutionKm=np.concatenate((WindResolutionKm, np.array([float(Data["ResolutionKm"])]*len(Data["NumberOfCellsPerSite"]))))

            TubPerSite=np.max([(WindTurbinesPerSite*4/float(Data["RatedPower"])),1])     
            MaxNumWindPerSite=np.concatenate((MaxNumWindPerSite,Data["NumberOfCellsPerSite"]*TubPerSite))
            
        Data.close()
        
    #Kite Data
    for i in range(len(PathKiteDesigns)):
        Data=np.load(PathKiteDesigns[i],allow_pickle=True)
        if i==0:
            KiteEnergy=Data['Energy_pu'][:-8,:] #Change it in the future
            KiteLatLong=Data['LatLong']
            AnnualizedCostKite=Data['AnnualizedCost']
            MaxNumKitePerSite=Data["NumberOfCellsPerSite"]*KiteTurbinesPerSite
            KiteDesign=np.array([i]*len(Data["NumberOfCellsPerSite"]))
            TimeKiteData=Data["TimeList"][:-8]
            RatedPowerKiteTurbine=np.array([float(Data["RatedPower"])]*len(Data["NumberOfCellsPerSite"]))
            KiteResolutionDegrees=np.array([float(Data["ResolutionDegrees"])]*len(Data["NumberOfCellsPerSite"]))
            KiteResolutionKm=np.array([float(Data["ResolutionKm"])]*len(Data["NumberOfCellsPerSite"]))
            
            TimeList=TimeKiteData
            
            
        else:
            KiteEnergy=np.concatenate((KiteEnergy,Data['Energy_pu'][:-8,:]),axis=1) #Change it in the future
            KiteLatLong=np.concatenate((KiteLatLong,Data['LatLong']))
            AnnualizedCostKite=np.concatenate((AnnualizedCostKite,Data['AnnualizedCost']))
            MaxNumKitePerSite=np.concatenate((MaxNumKitePerSite,KiteTurbinesPerSite*Data["NumberOfCellsPerSite"]))
            KiteDesign=np.concatenate((KiteDesign,[i]*len(Data["NumberOfCellsPerSite"])))
            RatedPowerKiteTurbine=np.concatenate((RatedPowerKiteTurbine,np.array([float(Data["RatedPower"])]*len(Data["NumberOfCellsPerSite"]))))
            KiteResolutionDegrees=np.concatenate((KiteResolutionDegrees, np.array([float(Data["ResolutionDegrees"])]*len(Data["NumberOfCellsPerSite"]))))
            KiteResolutionKm=np.concatenate((KiteResolutionKm, np.array([float(Data["ResolutionKm"])]*len(Data["NumberOfCellsPerSite"]))))
            
        Data.close()
        
    #Wave Data
    for i in range(len(PathWaveDesigns)):
        Data=np.load(PathWaveDesigns[i],allow_pickle=True)
        if i==0:
            WaveEnergy=Data['Energy_pu']
            WaveLatLong=Data['LatLong']
            AnnualizedCostWave=Data['AnnualizedCost']
            MaxNumWavePerSite=Data["NumberOfCellsPerSite"]*WaveTurbinesPerSite
            WaveDesign=np.array([i]*len(Data["NumberOfCellsPerSite"]))
            TimeWaveData=Data["TimeList"]
            RatedPowerWaveTurbine=np.array([float(Data["RatedPower"])]*len(Data["NumberOfCellsPerSite"]))  
            WaveResolutionDegrees=np.array([float(Data["ResolutionDegrees"])]*len(Data["NumberOfCellsPerSite"]))
            WaveResolutionKm=np.array([float(Data["ResolutionKm"])]*len(Data["NumberOfCellsPerSite"]))
            
            TimeList=TimeWaveData
            
        else:
            WaveEnergy=np.concatenate((WaveEnergy,Data['Energy_pu']),axis=1)
            WaveLatLong=np.concatenate((WaveLatLong,Data['LatLong']))
            AnnualizedCostWave=np.concatenate((AnnualizedCostWave,Data['AnnualizedCost']))
            MaxNumWavePerSite=np.concatenate((MaxNumWavePerSite,WaveTurbinesPerSite*Data["NumberOfCellsPerSite"]))
            WaveDesign=np.concatenate((WaveDesign,[i]*len(Data["NumberOfCellsPerSite"])))
            RatedPowerWaveTurbine=np.concatenate((RatedPowerWaveTurbine,np.array([float(Data["RatedPower"])]*len(Data["NumberOfCellsPerSite"]))))
            WaveResolutionDegrees=np.concatenate((WaveResolutionDegrees, np.array([float(Data["ResolutionDegrees"])]*len(Data["NumberOfCellsPerSite"]))))
            WaveResolutionKm=np.concatenate((WaveResolutionKm, np.array([float(Data["ResolutionKm"])]*len(Data["NumberOfCellsPerSite"]))))
    
    for i in range(len(PathCoaxialDesigns)):
        Data=np.load(PathCoaxialDesigns[i],allow_pickle=True)
        if i==0:
            CoaxialEnergy=Data['Energy_pu']
            CoaxialLatLong=Data['LatLong']
            AnnualizedCostCoaxial=Data['AnnualizedCost']
            MaxNumCoaxialPerSite=Data["NumberOfCellsPerSite"]*CoaxialTurbinesPerSite
            CoaxialDesign=np.array([i]*len(Data["NumberOfCellsPerSite"]))
            TimeCoaxialData=Data["TimeList"]
            RatedPowerCoaxialTurbine=np.array([float(Data["RatedPower"])]*len(Data["NumberOfCellsPerSite"]))  
            CoaxialResolutionDegrees=np.array([float(Data["ResolutionDegrees"])]*len(Data["NumberOfCellsPerSite"]))
            CoaxialResolutionKm=np.array([float(Data["ResolutionKm"])]*len(Data["NumberOfCellsPerSite"]))
            
            TimeList=TimeCoaxialData
            
        else:
            CoaxialEnergy=np.concatenate((CoaxialEnergy,Data['Energy_pu']),axis=1)
            CoaxialLatLong=np.concatenate((CoaxialLatLong,Data['LatLong']))
            AnnualizedCostCoaxial=np.concatenate((AnnualizedCostCoaxial,Data['AnnualizedCost']))
            MaxNumCoaxialPerSite=np.concatenate((MaxNumCoaxialPerSite,CoaxialTurbinesPerSite*Data["NumberOfCellsPerSite"]))
            CoaxialDesign=np.concatenate((CoaxialDesign,[i]*len(Data["NumberOfCellsPerSite"])))
            RatedPowerCoaxialTurbine=np.concatenate((RatedPowerCoaxialTurbine,np.array([float(Data["RatedPower"])]*len(Data["NumberOfCellsPerSite"]))))
            CoaxialResolutionDegrees=np.concatenate((CoaxialResolutionDegrees, np.array([float(Data["ResolutionDegrees"])]*len(Data["NumberOfCellsPerSite"]))))
            CoaxialResolutionKm=np.concatenate((CoaxialResolutionKm, np.array([float(Data["ResolutionKm"])]*len(Data["NumberOfCellsPerSite"]))))

    # #Verify if all the data is at the same time resolution and range
    # if len(PathWindDesigns)!=0 and len(PathKiteDesigns)!=0:
        
    #     if np.all(TimeWindData==TimeKiteData)==False:
    #         return print("Time resolution of the wind, and wave data is not the same")
        
    # if len(PathWindDesigns)!=0 and len(PathWaveDesigns)!=0:
    #     if  np.all(TimeWindData==TimeWaveData)==False:
    #         return print("Time resolution of the wind, and wave data is not the same")

    # if len(PathKiteDesigns)!=0 and len(PathWaveDesigns)!=0:
    #     if  np.all(TimeKiteData==TimeWaveData)==False:
    #         return print("Time resolution of the kite, and wave data is not the same")

    

    #Transmission
    Data=np.load(PathTransmissionDesign,allow_pickle=True)["TransmissionLineParameters"].item()

    AnnualizedCostTransmission=Data['S_BestACost']
    TransLatLong=Data['TL_LatLong']
    EfficiencyTransmission=Data['S_Efficiency']
    RatedPowerMWTransmissionMW=Data['RatedPowerMW']

    # if len(PathKiteDesigns)!=0:
    #     # LCOE_Kite=AnnualizedCostKite*10**6/((KiteEnergy.mean(axis=0)*RatedPowerKiteTurbine).mean(axis=0)*365*24)#$/MWh
    #     LCOE_Kite = LCOE_Kite
    #     IdxInKites=np.where(LCOE_Kite<200)[0]
        
    #     NumKiteSites=len(KiteLatLong[IdxInKites,:])
    #     KiteEnergy=KiteEnergy[:,IdxInKites]
    #     KiteLatLong=KiteLatLong[IdxInKites,:]
    #     AnnualizedCostKite=AnnualizedCostKite[IdxInKites]
    #     MaxNumKitePerSite=MaxNumKitePerSite[IdxInKites]
    #     KiteDesign=KiteDesign[IdxInKites]
    #     RatedPowerKiteTurbine=RatedPowerKiteTurbine[IdxInKites]
    #     KiteResolutionDegrees=KiteResolutionDegrees[IdxInKites]
    #     KiteResolutionKm=KiteResolutionKm[IdxInKites]

    # if len(PathWindDesigns)!=0:
    #     IdxInWind=np.where(WindLatLong[:,0]<200)[0]
        
    #     NumWindSites=len(WindLatLong[IdxInWind,:])
    #     WindEnergy=WindEnergy[:,IdxInWind]
    #     WindLatLong=WindLatLong[IdxInWind,:]
    #     AnnualizedCostWind=AnnualizedCostWind[IdxInWind]
    #     MaxNumWindPerSite=MaxNumWindPerSite[IdxInWind]
    #     WindDesign=WindDesign[IdxInWind]
    #     RatedPowerWindTurbine=RatedPowerWindTurbine[IdxInWind]
    #     WindResolutionDegrees=WindResolutionDegrees[IdxInWind]
    #     WindResolutionKm=WindResolutionKm[IdxInWind]
    
    # if len(PathCoaxialDesigns)!=0:
    #     IdxInCoaxial=np.where(CoaxialLatLong[:,0]<200)[0]
        
    #     NumCoaxialSites=len(CoaxialLatLong[IdxInCoaxial,:])
    #     CoaxialEnergy=CoaxialEnergy[:,IdxInCoaxial]
    #     CoaxialLatLong=CoaxialLatLong[IdxInCoaxial,:]
    #     AnnualizedCostCoaxial=AnnualizedCostCoaxial[IdxInCoaxial]
    #     MaxNumCoaxialPerSite=MaxNumCoaxialPerSite[IdxInCoaxial]
    #     CoaxialDesign=CoaxialDesign[IdxInCoaxial]
    #     RatedPowerCoaxialTurbine=RatedPowerCoaxialTurbine[IdxInCoaxial]
    #     CoaxialResolutionDegrees=CoaxialResolutionDegrees[IdxInCoaxial]
    #     CoaxialResolutionKm=CoaxialResolutionKm[IdxInCoaxial]
    
    # if len(TimeList) == 0:
    #     print("Warning: NumTimeSteps is zero. Check your input data.")
    #     TimeList = [0]  # Set a minimal default value

    KiteEnergy_filtered, KiteLatLong_filtered, AnnualizedCostKite_filtered, MaxNumKitePerSite_filtered = np.array([]), np.array([]), np.array([]), np.array([])
    KiteDesign_filtered = np.array([])
    RatedPowerKiteTurbine_filtered = np.array([])
    KiteResolutionDegrees_filtered = np.array([])
    KiteResolutionKm_filtered = np.array([])
    
    if len(PathKiteDesigns) != 0:
        LCOE_Kite=AnnualizedCostKite*10**6/((KiteEnergy.mean(axis=0)*RatedPowerKiteTurbine).mean(axis=0)*365*24)#$/MWh
        IdxInKites=np.where(LCOE_Kite<300)[0]
        print(f"======== IdxInKites: {IdxInKites} ========")

        if len(IdxInKites) == 0:
        # Either use all kite sites or set empty arrays with proper dimensions
            KiteEnergy_filtered = np.zeros((KiteEnergy.shape[0], 0))  # Empty but with correct first dimension
            KiteLatLong_filtered = np.zeros((0, KiteLatLong.shape[1]))  # Empty but with correct second dimension
        else:
            KiteEnergy_filtered = KiteEnergy[:,IdxInKites]
            KiteLatLong_filtered = KiteLatLong[IdxInKites,:]
            AnnualizedCostKite_filtered = AnnualizedCostKite[IdxInKites]
            MaxNumKitePerSite_filtered = MaxNumKitePerSite[IdxInKites]
            KiteDesign_filtered = KiteDesign[IdxInKites]
            RatedPowerKiteTurbine_filtered = RatedPowerKiteTurbine[IdxInKites]
            KiteResolutionDegrees_filtered = KiteResolutionDegrees[IdxInKites]
            KiteResolutionKm_filtered = KiteResolutionKm[IdxInKites]



    PortImputDir={  #Wind data
                    "WindEnergy":WindEnergy,
                    "WindLatLong":WindLatLong,
                    "AnnualizedCostWind":AnnualizedCostWind, #Costs should be in M$/year
                    "MaxNumWindPerSite":MaxNumWindPerSite,
                    "WindDesign":WindDesign,
                    "RatedPowerWindTurbine":RatedPowerWindTurbine, #shoud be in MW
                    "NumWindSites": len(WindLatLong),
                    "WindResolutionDegrees":WindResolutionDegrees,
                    "WindResolutionKm":WindResolutionKm,
                    
                    
                    #Kite data
                    "KiteEnergy":KiteEnergy_filtered,
                    "KiteLatLong":KiteLatLong_filtered,
                    "AnnualizedCostKite":AnnualizedCostKite_filtered,
                    "MaxNumKitePerSite":MaxNumKitePerSite_filtered,
                    "KiteDesign":KiteDesign_filtered,
                    "RatedPowerKiteTurbine":RatedPowerKiteTurbine_filtered,
                    "NumKiteSites": len(KiteLatLong),
                    "KiteResolutionDegrees":KiteResolutionDegrees_filtered,
                    "KiteResolutionKm":KiteResolutionKm_filtered,

                                                     
                    #Wavedata
                    "WaveEnergy":WaveEnergy,
                    "WaveLatLong":WaveLatLong,
                    "AnnualizedCostWave":AnnualizedCostWave,
                    "MaxNumWavePerSite":MaxNumWavePerSite,
                    "WaveDesign":WaveDesign,
                    "RatedPowerWaveTurbine":RatedPowerWaveTurbine,
                    "NumWaveSites": len(WaveLatLong),
                    "WaveResolutionDegrees":WaveResolutionDegrees,
                    "WaveResolutionKm":WaveResolutionKm,

                    "CoaxialEnergy":CoaxialEnergy,
                    "CoaxialLatLong":CoaxialLatLong,
                    "AnnualizedCostCoaxial":AnnualizedCostCoaxial, #Costs should be in M$/year
                    "MaxNumCoaxialPerSite":MaxNumCoaxialPerSite,
                    "CoaxialDesign":CoaxialDesign,
                    "RatedPowerCoaxialTurbine":RatedPowerCoaxialTurbine, #shoud be in MW
                    "NumCoaxialSites": len(CoaxialLatLong),
                    "CoaxialResolutionDegrees":CoaxialResolutionDegrees,
                    "CoaxialResolutionKm":CoaxialResolutionKm,
                    
                    
                    "TimeList":TimeList,
                    "NumTimeSteps":len(TimeList),
                    
                    #Transmission
                    "RatedPowerMWTransmissionMW":RatedPowerMWTransmissionMW,
                    "AnnualizedCostTransmission":AnnualizedCostTransmission,
                    "TransLatLong":TransLatLong,
                    "EfficiencyTransmission":EfficiencyTransmission,
                    "NumTransSites": len(TransLatLong),
                    
                    #Optimization Params
                    "LCOE_RANGE":LCOE_RANGE,
                    "Max_CollectionRadious":Max_CollectionRadious,
                    "MaxDesignsWind":MaxDesignsWind,
                    "MaxDesignsWave":MaxDesignsWave,
                    "MaxDesignsKite":MaxDesignsKite,
                    "MinNumWindTurb":MinNumWindTurb,
                    "MinNumWaveTurb":MinNumWaveTurb,
                    "MinNumKiteTrub":MinNumKiteTrub,
                    "MaxDesingsCoaxial": MaxDesingsCoaxial,
                    "MinNumCoaxialTurb": MinNumCoaxialTurb,
            
                }
    return PortImputDir

def SolvePortOpt_MaxGen_Model(PathWindDesigns, PathWaveDesigns, PathKiteDesigns, PathCoaxialDesigns, PathTransmissionDesign, LCOE_RANGE\
    ,Max_CollectionRadious,MaxDesignsWind, MaxDesingsWave, MaxDesingsKite,MinNumWindTurb,MinNumWaveTurb,MinNumKiteTrub, MaxDesingsCoaxial, MinNumCoaxialTurb, WindTurbinesPerSite=4, KiteTurbinesPerSite=390, WaveTurbinesPerSite=300, CoaxialTurbinesPerSite=390):


    #Create and solve the optimization problem
    InputDir=PreparePotOptInputs(PathWindDesigns, PathWaveDesigns,PathKiteDesigns, PathCoaxialDesigns, PathTransmissionDesign, LCOE_RANGE\
        ,Max_CollectionRadious,MaxDesignsWind, MaxDesingsWave, MaxDesingsKite,MinNumWindTurb,MinNumWaveTurb,MinNumKiteTrub, MaxDesingsCoaxial, MinNumCoaxialTurb, WindTurbinesPerSite=WindTurbinesPerSite, KiteTurbinesPerSite=KiteTurbinesPerSite, WaveTurbinesPerSite=WaveTurbinesPerSite, CoaxialTurbinesPerSite=CoaxialTurbinesPerSite)

    NumWindDesigns=len(PathWindDesigns)
    NumWaveDesigns=len(PathWaveDesigns)
    NumKiteDesigns=len(PathKiteDesigns)
    NumCoaxialDesigns=len(PathCoaxialDesigns)

    Model = ConcreteModel()
    BigM=1000 #Big M for the maximum total number of turbines allowed to be installed (This is used to limits deployments in the radious of the energy collection system)


    # Create Variables
    Model.Y_Wind = Var(range(InputDir["NumWindSites"]), domain=NonNegativeIntegers)# Integer variable to track the number of wind turbines used per site location
    Model.Y_Wave = Var(range(InputDir["NumWaveSites"]) , domain=NonNegativeIntegers)# Integer variable to track the number of wave turbines used per site location
    Model.Y_Kite = Var(range(InputDir["NumKiteSites"]), domain=NonNegativeIntegers)# Integer variable to track the number of kite turbines used per site location
    Model.Y_Coaxial = Var(range(InputDir["NumCoaxialSites"]), domain=NonNegativeIntegers)# Integer variable to track the number of coaxial turbines used per site location

    #Variable used to determined the turbine designs used
    Model.W_Wind = Var(range(NumWindDesigns), domain=Binary)# Binary variable to track the wind turbine design used
    Model.W_Wave = Var(range(NumWaveDesigns), domain=Binary)# Binary variable to track the wave turbine design used
    Model.W_Kite = Var(range(NumKiteDesigns), domain=Binary) # Binary variable to track the kite turbine design used
    Model.W_Coaxial = Var(range(NumCoaxialDesigns), domain=Binary) # Binary variable to track the coaxial turbine design used

    Model.s     = Var(range(InputDir["NumTransSites"]), domain=Binary)# Binary variable to track the center of the energy collection system
    Model.Delta = Var(range(InputDir["NumTimeSteps"]),  domain=NonNegativeReals) #Curtailment amount


    # #Objective Function
    def objective_rule(Model):   
        EGWind=sum(Model.Y_Wind[i]*InputDir["WindEnergy"][:,i].mean()*InputDir["RatedPowerWindTurbine"][i]  for i in range(InputDir["NumWindSites"])) #Energy generation from wind turbines [MW Avg]
        EGWave=sum(Model.Y_Wave[i]*InputDir["WaveEnergy"][:,i].mean()*InputDir["RatedPowerWaveTurbine"][i]  for i in range(InputDir["NumWaveSites"])) #Energy generation from wave turbines [MW Avg]
        EGKite=sum(Model.Y_Kite[i]*InputDir["KiteEnergy"][:,i].mean()*InputDir["RatedPowerKiteTurbine"][i]  for i in range(InputDir["NumKiteSites"])) #Energy generation from kite turbines [MW Avg]
        EGCoaxial=sum(Model.Y_Coaxial[i]*InputDir["CoaxialEnergy"][:,i].mean()*InputDir["RatedPowerCoaxialTurbine"][i]  for i in range(InputDir["NumCoaxialSites"])) #Energy generation from coaxial turbines [MW Avg]

        TotalCurtailment=sum(Model.Delta[t] for t in range(InputDir["NumTimeSteps"]))/InputDir["NumTimeSteps"] #Average curtailment MW

        Obj=(EGWind+EGWave+EGKite+EGCoaxial-TotalCurtailment)*24*365.25 # MWh Avg per year
        return Obj

    Model.OBJ = Objective(rule = objective_rule, sense=maximize)

    #Constraints

    #Maximum number of turbines per site location wind
    def MaxTurbinesCell_Wind_rule(Model,i):
        return Model.Y_Wind[i]<=InputDir["MaxNumWindPerSite"][i]
    Model.Turbines_Cell_Wind = Constraint(range(InputDir["NumWindSites"]), rule=MaxTurbinesCell_Wind_rule)

    def MaxTurbinesCell_Coaxial_rule(Model,i):
        return Model.Y_Coaxial[i]<=InputDir["MaxNumCoaxialPerSite"][i]
    Model.Turbines_Cell_Coaxial = Constraint(range(InputDir["NumCoaxialSites"]), rule=MaxTurbinesCell_Coaxial_rule)

    #Maximum number of turbines per site location kite
    def MaxTurbinesCell_Wave_rule(Model,i):
        return Model.Y_Wave[i]<=InputDir["MaxNumWavePerSite"][i]
    Model.Turbines_Cell_Wave = Constraint(range(InputDir["NumWaveSites"]), rule=MaxTurbinesCell_Wave_rule)

    #Maximum number of turbines per site location kite
    def MaxTurbinesCell_Kite_rule(Model,i):
        return Model.Y_Kite[i]<=InputDir["MaxNumKitePerSite"][i]
    Model.Turbines_Cell_Kite = Constraint(range(InputDir["NumKiteSites"]), rule=MaxTurbinesCell_Kite_rule)

    #Add new constraints to account for multiple technologiges and designs sharing the same region
    #Here pending task


    #Curtailment constraint
    # def Curtailment_rule(Model,t):
    #     EGWind=sum(Model.Y_Wind[i]*InputDir["WindEnergy"][t,i]*InputDir["RatedPowerWindTurbine"][i]  for i in range(InputDir["NumWindSites"])) #Energy generation from wind turbines
    #     EGWave=sum(Model.Y_Wave[i]*InputDir["WaveEnergy"][t,i]*InputDir["RatedPowerWaveTurbine"][i]  for i in range(InputDir["NumWaveSites"])) #Energy generation from wave turbines
    #     EGKite=sum(Model.Y_Kite[i]*InputDir["KiteEnergy"][t,i]*InputDir["RatedPowerKiteTurbine"][i]  for i in range(InputDir["NumKiteSites"])) #Energy generation from kite turbines
        
    #     return -Model.Delta[t]+ EGWind+ EGWave+ EGKite <= InputDir["RatedPowerMWTransmissionMW"]
    
    # def Curtailment_rule(Model,t):
    #     EGWind=sum(Model.Y_Wind[i]*InputDir["WindEnergy"][t,i]*InputDir["RatedPowerWindTurbine"][i]  for i in range(InputDir["NumWindSites"])) #Energy generation from wind turbines
    #     EGWave=sum(Model.Y_Wave[i]*InputDir["WaveEnergy"][t,i]*InputDir["RatedPowerWaveTurbine"][i]  for i in range(InputDir["NumWaveSites"])) #Energy generation from wave turbines
    #     EGKite=sum(Model.Y_Kite[i]*InputDir["KiteEnergy"][t,i]*InputDir["RatedPowerKiteTurbine"][i]  for i in range(InputDir["NumKiteSites"])) #Energy generation from kite turbines
    #     EGCoaxial=sum(Model.Y_Coaxial[i]*InputDir["CoaxialEnergy"][t,i]*InputDir["RatedPowerCoaxialTurbine"][i]  for i in range(InputDir["NumCoaxialSites"])) #Energy generation from coaxial turbines
        
    #     return -Model.Delta[t]+ EGWind+ EGWave+ EGKite + EGCoaxial <= InputDir["RatedPowerMWTransmissionMW"]
    def Curtailment_rule(Model, t):
        EGWind = sum(Model.Y_Wind[i]*InputDir["WindEnergy"][min(t, InputDir["WindEnergy"].shape[0]-1), i]*InputDir["RatedPowerWindTurbine"][i] 
                    for i in range(InputDir["NumWindSites"]))
        
        EGWave = sum(Model.Y_Wave[i]*InputDir["WaveEnergy"][min(t, InputDir["WaveEnergy"].shape[0]-1), i]*InputDir["RatedPowerWaveTurbine"][i] 
                    for i in range(InputDir["NumWaveSites"]))
        
        EGKite = sum(Model.Y_Kite[i]*InputDir["KiteEnergy"][min(t, InputDir["KiteEnergy"].shape[0]-1), i]*InputDir["RatedPowerKiteTurbine"][i] 
                    for i in range(InputDir["NumKiteSites"]))
        
        EGCoaxial = sum(Model.Y_Coaxial[i]*InputDir["CoaxialEnergy"][min(t, InputDir["CoaxialEnergy"].shape[0]-1), i]*InputDir["RatedPowerCoaxialTurbine"][i] 
                    for i in range(InputDir["NumCoaxialSites"]))
        
        return -Model.Delta[t] + EGWind + EGWave + EGKite + EGCoaxial <= InputDir["RatedPowerMWTransmissionMW"]

    Model.Curtailment = Constraint(range(InputDir["NumTimeSteps"]), rule=Curtailment_rule)

    #---Choose center collection system - Start
    #Slect one location for the energy collection system (One location for all technologies)
    #In the future you may be interested in having different locations for each technology or a combination of both

    Model.ChooseOneCircle= Constraint(expr=sum(Model.s[i] for i in range(InputDir["NumTransSites"]))==1)

    #Get the sites that are out of the radious of the center of the collection system
    IdxOutWind=GetIdxOutRadious(InputDir["TransLatLong"], InputDir["WindLatLong"], InputDir["Max_CollectionRadious"])
    IdxOutWave=GetIdxOutRadious(InputDir["TransLatLong"], InputDir["WaveLatLong"], InputDir["Max_CollectionRadious"])
    IdxOutKite=GetIdxOutRadious(InputDir["TransLatLong"], InputDir["KiteLatLong"], InputDir["Max_CollectionRadious"])
    IdxOutCoaxial=GetIdxOutRadious(InputDir["TransLatLong"], InputDir["CoaxialLatLong"], InputDir["Max_CollectionRadious"])

    def MaximumRadious(Model,i):  
        SumWind_s=sum(Model.Y_Wind[j] for j in IdxOutWind[i])
        SumWave_s=sum(Model.Y_Wave[j] for j in IdxOutWave[i])
        SumKite_s=sum(Model.Y_Kite[j] for j in IdxOutKite[i])
        SumCoaxial_s=sum(Model.Y_Coaxial[j] for j in IdxOutCoaxial[i])

        return SumWind_s+SumKite_s+SumWave_s+SumCoaxial_s<=(1-Model.s[i])*BigM # 1000 is a big M for the maximum total number of turbines installed       

    Model.Maximum_Radious = Constraint(range(InputDir["NumTransSites"]), rule=MaximumRadious)
    #---Choose center collection system - End

    #Track the turbine designs used and limit the number of designs used (Start)
    def TrackDesignsWind_rule(Model,d):  
        IdxVarPartOfDesign=np.where(InputDir["WindDesign"]==d)[0] #Index of Variables associated with the design
        
        #The idea of this constraint is that if the design is not selected, then the sum of the variables associated with the design should be zero
        return sum(Model.Y_Wind[i] for i in IdxVarPartOfDesign)<=Model.W_Wind[d]*BigM

    def TrackDesignsCoaxial_rule(Model,d):  
        IdxVarPartOfDesign=np.where(InputDir["CoaxialDesign"]==d)[0] #Index of Variables associated with the design
        
        #The idea of this constraint is that if the design is not selected, then the sum of the variables associated with the design should be zero
        return sum(Model.Y_Coaxial[i] for i in IdxVarPartOfDesign)<=Model.W_Coaxial[d]*BigM 

    def TrackDesignsWave_rule(Model,d):  
        IdxVarPartOfDesign=np.where(InputDir["WaveDesign"]==d)[0] #Index of Variables associated with the design
        
        #The idea of this constraint is that if the design is not selected, then the sum of the variables associated with the design should be zero
        return sum(Model.Y_Wave[i] for i in IdxVarPartOfDesign)<=Model.W_Wave[d]*BigM 

    def TrackDesignsKite_rule(Model,d):  
        IdxVarPartOfDesign=np.where(InputDir["KiteDesign"]==d)[0] #Index of Variables associated with the design
        
        #The idea of this constraint is that if the design is not selected, then the sum of the variables associated with the design should be zero
        return sum(Model.Y_Kite[i] for i in IdxVarPartOfDesign)<=Model.W_Kite[d]*BigM


    Model.TrackDesigns_Wind = Constraint(range(NumWindDesigns), rule=TrackDesignsWind_rule)
    Model.TrackDesigns_Wave = Constraint(range(NumWaveDesigns), rule=TrackDesignsWave_rule)
    Model.TrackDesigns_Kite = Constraint(range(NumKiteDesigns), rule=TrackDesignsKite_rule)
    Model.TrackDesigns_Coaxial = Constraint(range(NumCoaxialDesigns), rule=TrackDesignsCoaxial_rule)

    if NumWindDesigns>0:
        Model.LimitWindDesigns= Constraint(expr=sum(Model.W_Wind[d] for d in range(NumWindDesigns))==InputDir["MaxDesignsWind"])
    
    if NumCoaxialDesigns>0:
        Model.LimitCoaxialDesigns= Constraint(expr=sum(Model.W_Coaxial[d] for d in range(NumCoaxialDesigns))==InputDir["MaxDesingsCoaxial"])
    
    if NumWaveDesigns>0:
        Model.LimitWaveDesigns= Constraint(expr=sum(Model.W_Wave[d] for d in range(NumWaveDesigns))==InputDir["MaxDesignsWave"])
        
    if NumKiteDesigns>0:
        Model.LimitKiteDesigns = Constraint(expr=sum(Model.W_Kite[d] for d in range(NumKiteDesigns)) == InputDir["MaxDesignsKite"])

    #Track the turbine designs used and limit the number of designs used (End)

    #Limit the number of turbines
    
    if NumWindDesigns>0:
        Model.SetLB_Wind= Constraint(expr=sum(Model.Y_Wind[i] for i in range(InputDir["NumWindSites"]))>=InputDir["MinNumWindTurb"])
    
    if NumCoaxialDesigns>0:
        Model.SetLB_Coaxial= Constraint(expr=sum(Model.Y_Coaxial[i] for i in range(InputDir["NumCoaxialSites"]))>=InputDir["MinNumCoaxialTurb"])
    
    if NumWaveDesigns>0:
        Model.SetLB_Wave= Constraint(expr=sum(Model.Y_Wave[i] for i in range(InputDir["NumWaveSites"]))>=InputDir["MinNumWaveTurb"])
        
    if NumKiteDesigns>0:
        Model.SetLB_Kite= Constraint(expr=sum(Model.Y_Kite[i] for i in range(InputDir["NumKiteSites"]))>=InputDir["MinNumKiteTrub"])

    ################################### Overlap Constraints ################################### Start
    #Check for overlapping sites and constraint the number of turbines
    #overlaping with wind sites
    if NumWindDesigns>0:
        IdxOverlap_WindWind, AreaOverlap_WindWind, AreaRef1Ref2_WindWind, MaxTurbinesRef1Ref2_WindWind, PercentageOverlap_WindWind=GetOverlaps_Idx_Area(
            InputDir["WindLatLong"], InputDir["WindResolutionKm"], InputDir["WindResolutionDegrees"], InputDir["MaxNumWindPerSite"],
            InputDir["WindLatLong"], InputDir["WindResolutionKm"], InputDir["WindResolutionDegrees"], InputDir["MaxNumWindPerSite"],
            SameTech=1, PrintName="Wind-Wind")
        
        IdxOvelap_WindWave, AreaOverlap_WindWave, AreaRef1Ref2_WindWave, MaxTurbinesRef1Ref2_WindWave, PercentageOverlap_WindWave=GetOverlaps_Idx_Area(
            InputDir["WindLatLong"], InputDir["WindResolutionKm"], InputDir["WindResolutionDegrees"], InputDir["MaxNumWindPerSite"],
            InputDir["WaveLatLong"], InputDir["WaveResolutionKm"], InputDir["WaveResolutionDegrees"], InputDir["MaxNumWavePerSite"],
            SameTech=0,  PrintName="Wind-Wave")
        
        IdxOvelap_WindKite, AreaOverlap_WindKite, AreaRef1Ref2_WindKite, MaxTurbinesRef1Ref2_WindKite, PercentageOverlap_WindKite=GetOverlaps_Idx_Area(
            InputDir["WindLatLong"], InputDir["WindResolutionKm"], InputDir["WindResolutionDegrees"], InputDir["MaxNumWindPerSite"],
            InputDir["KiteLatLong"], InputDir["KiteResolutionKm"], InputDir["KiteResolutionDegrees"], InputDir["MaxNumKitePerSite"],
            SameTech=0, PrintName="Wind-Kite")
        
        IdxOvelap_WindCoaxial, AreaOverlap_WindCoaxial, AreaRef1Ref2_WindCoaxial, MaxTurbinesRef1Ref2_WindCoaxial, PercentageOverlap_WindCoaxial=GetOverlaps_Idx_Area(
            InputDir["WindLatLong"], InputDir["WindResolutionKm"], InputDir["WindResolutionDegrees"], InputDir["MaxNumWindPerSite"],
            InputDir["CoaxialLatLong"], InputDir["CoaxialResolutionKm"], InputDir["CoaxialResolutionDegrees"], InputDir["MaxNumCoaxialPerSite"],
            SameTech=0,  PrintName="Wind-Coaxial")
        
        #Wind sites with some overlap
        IdxOvelap_UniqueWindIdx=np.unique(np.concatenate((IdxOverlap_WindWind,IdxOvelap_WindWave,IdxOvelap_WindKite,IdxOvelap_WindCoaxial))[:,0])

        def TrackOverlaps_Wind_rule(Model,i):
            
            
            IdxWindWind_f=IdxOverlap_WindWind[IdxOverlap_WindWind[:,0]==i, 1]
            IdxWindWave_f=IdxOvelap_WindWave[IdxOvelap_WindWave[:,0]==i,   1]
            IdxWindCoaxial_f=IdxOvelap_WindCoaxial[IdxOvelap_WindCoaxial[:,0]==i,   1]
            IdxWindKite_f=IdxOvelap_WindKite[IdxOvelap_WindKite[:,0]==i,   1]
            
            AreaWindWind_f=AreaRef1Ref2_WindWind[IdxOverlap_WindWind[:,0]==i]
            AreaWindWave_f=AreaRef1Ref2_WindWave[IdxOvelap_WindWave[:,0]==i]
            AreaWindCoaxial_f=AreaRef1Ref2_WindCoaxial[IdxOvelap_WindCoaxial[:,0]==i]
            AreaWindKite_f=AreaRef1Ref2_WindKite[IdxOvelap_WindKite[:,0]==i]
            
            MaxTurbinesWind_f=MaxTurbinesRef1Ref2_WindWind[IdxOverlap_WindWind[:,0]==i]
            MaxTurbinesWave_f=MaxTurbinesRef1Ref2_WindWave[IdxOvelap_WindWave[:,0]==i]
            MaxTurbinesCoaxial_f=MaxTurbinesRef1Ref2_WindCoaxial[IdxOvelap_WindCoaxial[:,0]==i]
            MaxTurbinesKite_f=MaxTurbinesRef1Ref2_WindKite[IdxOvelap_WindKite[:,0]==i]
            
            PercentageOverlap_WindWind_f=PercentageOverlap_WindWind[IdxOverlap_WindWind[:,0]==i]
            PercentageOverlap_WindWave_f=PercentageOverlap_WindWave[IdxOvelap_WindWave[:,0]==i]
            PercentageOverlap_WindCoaxial_f=PercentageOverlap_WindCoaxial[IdxOvelap_WindCoaxial[:,0]==i]
            PercentageOverlap_WindKite_f=PercentageOverlap_WindKite[IdxOvelap_WindKite[:,0]==i]
            
            #Compute the overlaped area and estimate the equivalent number of turbines that cannot be installed on the ith location anymore
            Expression=Model.Y_Wind[i] <= InputDir["MaxNumWindPerSite"][i]\
                    -sum(Model.Y_Wind[IdxWindWind_f[k]] for k in range(len(IdxWindWind_f)))#\
                    # -sum((AreaWindWave_f[k,1]/MaxTurbinesWave_f[k,1]*Model.Y_Wave[IdxWindWave_f[k]])*PercentageOverlap_WindWave_f[k]\
                    #     *MaxTurbinesWave_f[k,0]/AreaWindWave_f[k,0] for k in range(len(IdxWindWave_f)))\
                    # -sum((AreaWindKite_f[k,1]/MaxTurbinesKite_f[k,1]*Model.Y_Kite[IdxWindKite_f[k]])*PercentageOverlap_WindKite_f[k]\
                    #     *MaxTurbinesKite_f[k,0]/AreaWindKite_f[k,0] for k in range(len(IdxWindKite_f)))
                    
            return Expression
            
            
        Model.OvelapWind_ALL= Constraint(list(IdxOvelap_UniqueWindIdx), rule=TrackOverlaps_Wind_rule)
        
    #overlaping with wave sites
    if NumWaveDesigns>0:
        
        IdxOvelap_WaveWind, AreaOverlap_WaveWind, AreaRef1Ref2_WaveWind, MaxTurbinesRef1Ref2_WaveWind, PercentageOverlap_WaveWind=GetOverlaps_Idx_Area(
            InputDir["WaveLatLong"], InputDir["WaveResolutionKm"], InputDir["WaveResolutionDegrees"], InputDir["MaxNumWavePerSite"],
            InputDir["WindLatLong"], InputDir["WindResolutionKm"], InputDir["WindResolutionDegrees"], InputDir["MaxNumWindPerSite"],
            SameTech=0, PrintName="Wave-Wind")
        
        
        IdxOverlap_WaveWave, AreaOverlap_WaveWave, AreaRef1Ref2_WaveWave, MaxTurbinesRef1Ref2_WaveWave, PercentageOverlap_WaveWave=GetOverlaps_Idx_Area(
            InputDir["WaveLatLong"], InputDir["WaveResolutionKm"], InputDir["WaveResolutionDegrees"], InputDir["MaxNumWavePerSite"],
            InputDir["WaveLatLong"], InputDir["WaveResolutionKm"], InputDir["WaveResolutionDegrees"], InputDir["MaxNumWavePerSite"],
            SameTech=1, PrintName="Wave-Wave")
        
        IdxOverlap_WaveCoaxial, AreaOverlap_WaveCoaxial, AreaRef1Ref2_WaveCoaxial, MaxTurbinesRef1Ref2_WaveCoaxial, PercentageOverlap_WaveCoaxial=GetOverlaps_Idx_Area(
            InputDir["WaveLatLong"], InputDir["WaveResolutionKm"], InputDir["WaveResolutionDegrees"], InputDir["MaxNumWavePerSite"],
            InputDir["CoaxialLatLong"], InputDir["CoaxialResolutionKm"], InputDir["CoaxialResolutionDegrees"], InputDir["MaxNumCoaxialPerSite"],
            SameTech=0, PrintName="Wave-Coaxial")
        
        
        IdxOverlap_WaveKite, AreaOverlap_WaveKite, AreaRef1Ref2_WaveKite, MaxTurbinesRef1Ref2_WaveKite, PercentageOverlap_WaveKite=GetOverlaps_Idx_Area(
            InputDir["WaveLatLong"], InputDir["WaveResolutionKm"], InputDir["WaveResolutionDegrees"], InputDir["MaxNumWavePerSite"],
            InputDir["KiteLatLong"], InputDir["KiteResolutionKm"], InputDir["KiteResolutionDegrees"], InputDir["MaxNumKitePerSite"],
            SameTech=0, PrintName="Wave-Kite")
        
        #Wave sites with some overlap
        IdxOvelap_UniqueWaveIdx=np.unique(np.concatenate((IdxOvelap_WaveWind,IdxOverlap_WaveWave,IdxOverlap_WaveKite, IdxOverlap_WaveCoaxial))[:,0])
        
        def TrackOverlaps_Wave_rule(Model,i):
                
                
            IdxWaveWind_f=IdxOvelap_WaveWind[IdxOvelap_WaveWind[:,0]==i,   1]
            IdxWaveWave_f=IdxOverlap_WaveWave[IdxOverlap_WaveWave[:,0]==i, 1]
            IdxWaveKite_f=IdxOverlap_WaveKite[IdxOverlap_WaveKite[:,0]==i, 1]
            IdxWaveCoaxial_f=IdxOverlap_WaveCoaxial[IdxOverlap_WaveCoaxial[:,0]==i,   1]
            
            AreaWaveWind_f=AreaRef1Ref2_WaveWind[IdxOvelap_WaveWind[:,0]==i]
            AreaWaveWave_f=AreaRef1Ref2_WaveWave[IdxOverlap_WaveWave[:,0]==i]
            AreaWaveKite_f=AreaRef1Ref2_WaveKite[IdxOverlap_WaveKite[:,0]==i]
            AreaWaveCoaxial_f=AreaRef1Ref2_WaveCoaxial[IdxOverlap_WaveCoaxial[:,0]==i]
            
            MaxTurbinesWaveWind_f=MaxTurbinesRef1Ref2_WaveWind[IdxOvelap_WaveWind[:,0]==i]
            MaxTurbinesWaveWave_f=MaxTurbinesRef1Ref2_WaveWave[IdxOverlap_WaveWave[:,0]==i]
            MaxTurbinesWaveKite_f=MaxTurbinesRef1Ref2_WaveKite[IdxOverlap_WaveKite[:,0]==i]
            MaxTurbinesWaveCoaxial_f=MaxTurbinesRef1Ref2_WaveCoaxial[IdxOverlap_WaveCoaxial[:,0]==i]
            
            PercentageOverlap_WaveWind_f=PercentageOverlap_WaveWind[IdxOvelap_WaveWind[:,0]==i]
            PercentageOverlap_WaveWave_f=PercentageOverlap_WaveWave[IdxOverlap_WaveWave[:,0]==i]
            PercentageOverlap_WaveKite_f=PercentageOverlap_WaveKite[IdxOverlap_WaveKite[:,0]==i]
            PercentageOverlap_WaveCoaxial_f=PercentageOverlap_WaveCoaxial[IdxOverlap_WaveCoaxial[:,0]==i]
            
            #Compute the overlaped area and estimate the equivalent number of turbines that cannot be installed on the ith location anymore
            Expression=Model.Y_Wave[i] <= InputDir["MaxNumWavePerSite"][i]\
                    -sum((AreaWaveWind_f[k,1]/MaxTurbinesWaveWind_f[k,1]*Model.Y_Wind[IdxWaveWind_f[k]])*PercentageOverlap_WaveWind_f[k]\
                        *MaxTurbinesWaveWind_f[k,0]/AreaWaveWind_f[k,0] for k in range(len(IdxWaveWind_f)))\
                    -sum((AreaWaveWave_f[k,1]/MaxTurbinesWaveWave_f[k,1]*Model.Y_Wave[IdxWaveWave_f[k]])*PercentageOverlap_WaveWave_f[k]\
                        *MaxTurbinesWaveWave_f[k,0]/AreaWaveWave_f[k,0] for k in range(len(IdxWaveWave_f)))\
                    -sum((AreaWaveKite_f[k,1]/MaxTurbinesWaveKite_f[k,1]*Model.Y_Kite[IdxWaveKite_f[k]])*PercentageOverlap_WaveKite_f[k]\
                        *MaxTurbinesWaveKite_f[k,0]/AreaWaveKite_f[k,0] for k in range(len(IdxWaveKite_f)))\
                    -sum((AreaWaveCoaxial_f[k,1]/MaxTurbinesWaveCoaxial_f[k,1]*Model.Y_Coaxial[IdxWaveCoaxial_f[k]])*PercentageOverlap_WaveCoaxial_f[k]\
                                *MaxTurbinesWaveCoaxial_f[k,0]/AreaWaveCoaxial_f[k,0] for k in range(len(IdxWaveCoaxial_f)))
            return Expression

        Model.OverlapWave_ALL= Constraint(list(IdxOvelap_UniqueWaveIdx), rule=TrackOverlaps_Wave_rule)
        
    #overlaping with kite sites
    if NumKiteDesigns>0:
        
        IdxOvelap_KiteWind, AreaOverlap_KiteWind, AreaRef1Ref2_KiteWind, MaxTurbinesRef1Ref2_KiteWind, PercentageOverlap_KiteWind=GetOverlaps_Idx_Area(
            InputDir["KiteLatLong"], InputDir["KiteResolutionKm"], InputDir["KiteResolutionDegrees"], InputDir["MaxNumKitePerSite"],
            InputDir["WindLatLong"], InputDir["WindResolutionKm"], InputDir["WindResolutionDegrees"], InputDir["MaxNumWindPerSite"],
            SameTech=0, PrintName="Kite-Wind")
        
        IdxOvelap_KiteWave, AreaOverlap_KiteWave, AreaRef1Ref2_KiteWave, MaxTurbinesRef1Ref2_KiteWave, PercentageOverlap_KiteWave=GetOverlaps_Idx_Area(
            InputDir["KiteLatLong"], InputDir["KiteResolutionKm"], InputDir["KiteResolutionDegrees"], InputDir["MaxNumKitePerSite"],
            InputDir["WaveLatLong"], InputDir["WaveResolutionKm"], InputDir["WaveResolutionDegrees"], InputDir["MaxNumWavePerSite"],
            SameTech=0, PrintName="Kite-Wave")
        
        IdxOvelap_KiteCoaxial, AreaOverlap_KiteCoaxial, AreaRef1Ref2_KiteCoaxial, MaxTurbinesRef1Ref2_KiteCoaxial, PercentageOverlap_KiteCoaxial=GetOverlaps_Idx_Area(
            InputDir["KiteLatLong"], InputDir["KiteResolutionKm"], InputDir["KiteResolutionDegrees"], InputDir["MaxNumKitePerSite"],
            InputDir["CoaxialLatLong"], InputDir["CoaxialResolutionKm"], InputDir["CoaxialResolutionDegrees"], InputDir["MaxNumCoaxialPerSite"],
            SameTech=0, PrintName="Kite-Coaxial")
        
        IdxOverlap_KiteKite, AreaOverlap_KiteKite, AreaRef1Ref2_KiteKite, MaxTurbinesRef1Ref2_KiteKite, PercentageOverlap_KiteKite=GetOverlaps_Idx_Area(
            InputDir["KiteLatLong"], InputDir["KiteResolutionKm"], InputDir["KiteResolutionDegrees"], InputDir["MaxNumKitePerSite"],
            InputDir["KiteLatLong"], InputDir["KiteResolutionKm"], InputDir["KiteResolutionDegrees"], InputDir["MaxNumKitePerSite"],
            SameTech=1, PrintName="Kite-Kite")
        
        #Kite sites with some overlap
        IdxOvelap_UniqueKiteIdx=np.unique(np.concatenate((IdxOvelap_KiteWind,IdxOvelap_KiteWave,IdxOverlap_KiteKite,IdxOvelap_KiteCoaxial))[:,0])
        
        def TrackOverlaps_Kite_rule(Model,i):
                
                
            IdxKiteWind_f=IdxOvelap_KiteWind[IdxOvelap_KiteWind[:,0]==i,   1]
            IdxKiteWave_f=IdxOvelap_KiteWave[IdxOvelap_KiteWave[:,0]==i,   1]
            IdxKiteCoaxial_f=IdxOvelap_KiteCoaxial[IdxOvelap_KiteCoaxial[:,0]==i,   1]
            IdxKiteKite_f=IdxOverlap_KiteKite[IdxOverlap_KiteKite[:,0]==i, 1]
            
            AreaKiteWind_f=AreaRef1Ref2_KiteWind[IdxOvelap_KiteWind[:,0]==i]
            AreaKiteWave_f=AreaRef1Ref2_KiteWave[IdxOvelap_KiteWave[:,0]==i]
            AreaKiteCoaxial_f=AreaRef1Ref2_KiteCoaxial[IdxOvelap_KiteCoaxial[:,0]==i]
            AreaKiteKite_f=AreaRef1Ref2_KiteKite[IdxOverlap_KiteKite[:,0]==i]
            
            MaxTurbinesKiteWind_f=MaxTurbinesRef1Ref2_KiteWind[IdxOvelap_KiteWind[:,0]==i]
            MaxTurbinesKiteWave_f=MaxTurbinesRef1Ref2_KiteWave[IdxOvelap_KiteWave[:,0]==i]
            MaxTurbinesKiteCoaxial_f=MaxTurbinesRef1Ref2_KiteCoaxial[IdxOvelap_KiteCoaxial[:,0]==i]
            MaxTurbinesKiteKite_f=MaxTurbinesRef1Ref2_KiteKite[IdxOverlap_KiteKite[:,0]==i]
            
            PercentageOverlap_KiteWind_f=PercentageOverlap_KiteWind[IdxOvelap_KiteWind[:,0]==i]
            PercentageOverlap_KiteWave_f=PercentageOverlap_KiteWave[IdxOvelap_KiteWave[:,0]==i]
            PercentageOverlap_KiteCoaxial_f=PercentageOverlap_KiteCoaxial[IdxOvelap_KiteCoaxial[:,0]==i]
            PercentageOverlap_KiteKite_f=PercentageOverlap_KiteKite[IdxOverlap_KiteKite[:,0]==i]
            
            #Compute the overlaped area and estimate the equivalent number of turbines that cannot be installed on the ith location anymore
            Expression=Model.Y_Kite[i] <= InputDir["MaxNumKitePerSite"][i]-sum(Model.Y_Kite[IdxKiteKite_f[k]] for k in range(len(IdxKiteKite_f)))
                    # -sum((AreaKiteWind_f[k,1]/MaxTurbinesKiteWind_f[k,1]*Model.Y_Wind[IdxKiteWind_f[k]])*PercentageOverlap_KiteWind_f[k]\
                    #     *MaxTurbinesKiteWind_f[k,0]/AreaKiteWind_f[k,0] for k in range(len(IdxKiteWind_f)))\
                    # -sum((AreaKiteWave_f[k,1]/MaxTurbinesKiteWave_f[k,1]*Model.Y_Wave[IdxKiteWave_f[k]])*PercentageOverlap_KiteWave_f[k]\
                    #     *MaxTurbinesKiteWave_f[k,0]/AreaKiteWave_f[k,0] for k in range(len(IdxKiteWave_f)))\
                    
            return Expression
        
        Model.OverlapKite_ALL= Constraint(list(IdxOvelap_UniqueKiteIdx), rule=TrackOverlaps_Kite_rule)
    
    if NumCoaxialDesigns>0:
        
        IdxOvelap_CoaxialWind, AreaOverlap_CoaxialWind, AreaRef1Ref2_CoaxialWind, MaxTurbinesRef1Ref2_CoaxialWind, PercentageOverlap_CoaxialWind=GetOverlaps_Idx_Area(
            InputDir["CoaxialLatLong"], InputDir["CoaxialResolutionKm"], InputDir["CoaxialResolutionDegrees"], InputDir["MaxNumCoaxialPerSite"],
            InputDir["WindLatLong"], InputDir["WindResolutionKm"], InputDir["WindResolutionDegrees"], InputDir["MaxNumWindPerSite"],
            SameTech=0, PrintName="Coaxial-Wind")
        
        IdxOvelap_CoaxialWave, AreaOverlap_CoaxialWave, AreaRef1Ref2_CoaxialWave, MaxTurbinesRef1Ref2_CoaxialWave, PercentageOverlap_CoaxialWave=GetOverlaps_Idx_Area(
            InputDir["CoaxialLatLong"], InputDir["CoaxialResolutionKm"], InputDir["CoaxialResolutionDegrees"], InputDir["MaxNumCoaxialPerSite"],
            InputDir["WaveLatLong"], InputDir["WaveResolutionKm"], InputDir["WaveResolutionDegrees"], InputDir["MaxNumWavePerSite"],
            SameTech=0, PrintName="Coaxial-Wave")
        
        IdxOvelap_CoaxialCoaxial, AreaOverlap_CoaxialCoaxial, AreaRef1Ref2_CoaxialCoaxial, MaxTurbinesRef1Ref2_CoaxialCoaxial, PercentageOverlap_CoaxialCoaxial=GetOverlaps_Idx_Area(
            InputDir["CoaxialLatLong"], InputDir["CoaxialResolutionKm"], InputDir["CoaxialResolutionDegrees"], InputDir["MaxNumCoaxialPerSite"],
            InputDir["CoaxialLatLong"], InputDir["CoaxialResolutionKm"], InputDir["CoaxialResolutionDegrees"], InputDir["MaxNumCoaxialPerSite"],
            SameTech=0, PrintName="Coaxial-Coaxial")
        
        IdxOverlap_CoaxialKite, AreaOverlap_CoaxialKite, AreaRef1Ref2_CoaxialKite, MaxTurbinesRef1Ref2_CoaxialKite, PercentageOverlap_CoaxialKite=GetOverlaps_Idx_Area(
            InputDir["CoaxialLatLong"], InputDir["CoaxialResolutionKm"], InputDir["CoaxialResolutionDegrees"], InputDir["MaxNumCoaxialPerSite"],
            InputDir["KiteLatLong"], InputDir["KiteResolutionKm"], InputDir["KiteResolutionDegrees"], InputDir["MaxNumKitePerSite"],
            SameTech=1, PrintName="Coaxial-Kite")
        
        #Kite sites with some overlap
        IdxOvelap_UniqueCoaxialIdx=np.unique(np.concatenate((IdxOvelap_CoaxialWind,IdxOvelap_CoaxialWave,IdxOverlap_CoaxialKite,IdxOvelap_CoaxialCoaxial))[:,0])
        
        def TrackOverlaps_Coaxial_rule(Model,i):
                
                
            IdxCoaxialWind_f=IdxOvelap_CoaxialWind[IdxOvelap_CoaxialWind[:,0]==i,   1]
            IdxCoaxialWave_f=IdxOvelap_CoaxialWave[IdxOvelap_CoaxialWave[:,0]==i,   1]
            IdxCoaxialCoaxial_f=IdxOvelap_CoaxialCoaxial[IdxOvelap_CoaxialCoaxial[:,0]==i,   1]
            IdxCoaxialKite_f=IdxOverlap_CoaxialKite[IdxOverlap_CoaxialKite[:,0]==i, 1]
            
            AreaCoaxialWind_f=AreaRef1Ref2_CoaxialWind[IdxOvelap_CoaxialWind[:,0]==i]
            AreaCoaxialWave_f=AreaRef1Ref2_CoaxialWave[IdxOvelap_CoaxialWave[:,0]==i]
            AreaCoaxialCoaxial_f=AreaRef1Ref2_CoaxialCoaxial[IdxOvelap_CoaxialCoaxial[:,0]==i]
            AreaCoaxialKite_f=AreaRef1Ref2_CoaxialKite[IdxOverlap_CoaxialKite[:,0]==i]
            
            MaxTurbinesCoaxialWind_f=MaxTurbinesRef1Ref2_CoaxialWind[IdxOvelap_CoaxialWind[:,0]==i]
            MaxTurbinesCoaxialWave_f=MaxTurbinesRef1Ref2_CoaxialWave[IdxOvelap_CoaxialWave[:,0]==i]
            MaxTurbinesCoaxialCoaxial_f=MaxTurbinesRef1Ref2_CoaxialCoaxial[IdxOvelap_CoaxialCoaxial[:,0]==i]
            MaxTurbinesCoaxialKite_f=MaxTurbinesRef1Ref2_CoaxialKite[IdxOverlap_CoaxialKite[:,0]==i]
            
            PercentageOverlap_CoaxialWind_f=PercentageOverlap_CoaxialWind[IdxOvelap_CoaxialWind[:,0]==i]
            PercentageOverlap_CoaxialWave_f=PercentageOverlap_CoaxialWave[IdxOvelap_CoaxialWave[:,0]==i]
            PercentageOverlap_CoaxialCoaxial_f=PercentageOverlap_CoaxialCoaxial[IdxOvelap_CoaxialCoaxial[:,0]==i]
            PercentageOverlap_CoaxialKite_f=PercentageOverlap_CoaxialKite[IdxOverlap_CoaxialKite[:,0]==i]
            
            #Compute the overlaped area and estimate the equivalent number of turbines that cannot be installed on the ith location anymore
            Expression=Model.Y_Coaxial[i] <= InputDir["MaxNumCoaxialPerSite"][i]-sum(Model.Y_Coaxial[IdxCoaxialCoaxial_f[k]] for k in range(len(IdxCoaxialCoaxial_f)))
                    # -sum((AreaKiteWind_f[k,1]/MaxTurbinesKiteWind_f[k,1]*Model.Y_Wind[IdxKiteWind_f[k]])*PercentageOverlap_KiteWind_f[k]\
                    #     *MaxTurbinesKiteWind_f[k,0]/AreaKiteWind_f[k,0] for k in range(len(IdxKiteWind_f)))\
                    # -sum((AreaKiteWave_f[k,1]/MaxTurbinesKiteWave_f[k,1]*Model.Y_Wave[IdxKiteWave_f[k]])*PercentageOverlap_KiteWave_f[k]\
                    #     *MaxTurbinesKiteWave_f[k,0]/AreaKiteWave_f[k,0] for k in range(len(IdxKiteWave_f)))\
                    
            return Expression
        
        Model.OverlapCoaxial_ALL= Constraint(list(IdxOvelap_UniqueCoaxialIdx), rule=TrackOverlaps_Coaxial_rule)
    ####
    ################################### Overlap Constraints ################################### End
    
    # #LCOE Target (Attached later on the LCOE iterator)
    # def LCOETarget(Model, LCOE_Max):  
    #     EGWind=sum(Model.Y_Wind[i]*InputDir["WindEnergy"][:,i].mean()*InputDir["RatedPowerWindTurbine"][i]  for i in range(InputDir["NumWindSites"])) #Energy generation from wind turbines [MW Avg]
    #     EGWave=sum(Model.Y_Wave[i]*InputDir["WaveEnergy"][:,i].mean()*InputDir["RatedPowerWaveTurbine"][i]  for i in range(InputDir["NumWaveSites"])) #Energy generation from wave turbines [MW Avg]
    #     EGKite=sum(Model.Y_Kite[i]*InputDir["KiteEnergy"][:,i].mean()*InputDir["RatedPowerKiteTurbine"][i]  for i in range(InputDir["NumKiteSites"])) #Energy generation from kite turbines [MW Avg]

    #     TotalCurtailment=sum(Model.Delta[t] for t in range(InputDir["NumTimeSteps"]))/InputDir["NumTimeSteps"] #Average curtailment MW

    #     MWhYear=(EGWind+EGWave+EGKite-TotalCurtailment)*24*365.25 # MWh Avg per year


    #     Cost_Wind=sum(Model.Y_Wind[i]*InputDir["AnnualizedCostWind"][i]  for i in range(InputDir["NumWindSites"]))
    #     Cost_Wave=sum(Model.Y_Wave[i]*InputDir["AnnualizedCostWave"][i]  for i in range(InputDir["NumWaveSites"]))
    #     Cost_Kite=sum(Model.Y_Kite[i]*InputDir["AnnualizedCostKite"][i]  for i in range(InputDir["NumKiteSites"]))
        
        
    #     Cost_Transmission=sum(Model.s[i]*InputDir["AnnualizedCostTransmission"][i] for i in Model.SiteTrs)
        
    #     TotalCost=Cost_Wind+Cost_Wave+Cost_Kite+Cost_Transmission
        

    #     return TotalCost<=LCOE_Max*MWhYear  

    return Model, InputDir


def SolvePortOpt_MaxGen_LCOE_Iterator(PathWindDesigns, PathWaveDesigns, PathKiteDesigns, PathCoaxialDesigns, PathTransmissionDesign, LCOE_RANGE\
    ,Max_CollectionRadious,MaxDesignsWind, MaxDesingsWave, MaxDesingsKite,MinNumWindTurb,MinNumWaveTurb,MinNumKiteTrub, MaxDesingsCoaxial, MinNumCoaxialTurb\
    ,ReadMe,SavePath=None, WindTurbinesPerSite=4, KiteTurbinesPerSite=390, WaveTurbinesPerSite=300, CoaxialTurbinesPerSite=390):

    #Create inputs and main model structure
    Model, InputDir=SolvePortOpt_MaxGen_Model(PathWindDesigns, PathWaveDesigns, PathKiteDesigns, PathCoaxialDesigns, PathTransmissionDesign, LCOE_RANGE\
        ,Max_CollectionRadious,MaxDesignsWind, MaxDesingsWave, MaxDesingsKite,MinNumWindTurb,MinNumWaveTurb,MinNumKiteTrub, MaxDesingsCoaxial, MinNumCoaxialTurb, WindTurbinesPerSite=WindTurbinesPerSite, KiteTurbinesPerSite=KiteTurbinesPerSite, WaveTurbinesPerSite=WaveTurbinesPerSite, CoaxialTurbinesPerSite=CoaxialTurbinesPerSite)

    opt = SolverFactory('gurobi', solver_io="python")
    opt.options['mipgap'] = 0.02

    #LCOE Target
    def LCOETarget_rule(Model, LCOE_Max):  
        EGWind = sum(Model.Y_Wind[i]*InputDir["WindEnergy"][:,i].mean()*InputDir["RatedPowerWindTurbine"][i] for i in range(InputDir["NumWindSites"]))
        EGWave = sum(Model.Y_Wave[i]*InputDir["WaveEnergy"][:,i].mean()*InputDir["RatedPowerWaveTurbine"][i] for i in range(InputDir["NumWaveSites"]))
        EGKite = sum(Model.Y_Kite[i]*InputDir["KiteEnergy"][:,i].mean()*InputDir["RatedPowerKiteTurbine"][i] for i in range(InputDir["NumKiteSites"]))
        EGCoaxial = sum(Model.Y_Coaxial[i]*InputDir["CoaxialEnergy"][:,i].mean()*InputDir["RatedPowerCoaxialTurbine"][i] for i in range(InputDir["NumCoaxialSites"]))

        # Check for zero division
        if InputDir["NumTimeSteps"] > 0:
            TotalCurtailment = sum(Model.Delta[t] for t in range(InputDir["NumTimeSteps"]))/InputDir["NumTimeSteps"]
        else:
            TotalCurtailment = 0  # Default value when no time steps

        MWhYear = (EGWind + EGWave + EGKite + EGCoaxial - TotalCurtailment) * 24 * 365.25 # MWh Avg per year


        Cost_Wind=sum(Model.Y_Wind[i]*InputDir["AnnualizedCostWind"][i]  for i in range(InputDir["NumWindSites"]))
        Cost_Wave=sum(Model.Y_Wave[i]*InputDir["AnnualizedCostWave"][i]  for i in range(InputDir["NumWaveSites"]))
        Cost_Kite=sum(Model.Y_Kite[i]*InputDir["AnnualizedCostKite"][i]  for i in range(InputDir["NumKiteSites"]))
        Cost_Coaxial=sum(Model.Y_Coaxial[i]*InputDir["AnnualizedCostCoaxial"][i]  for i in range(InputDir["NumCoaxialSites"]))
        
        
        Cost_Transmission=sum(Model.s[i]*InputDir["AnnualizedCostTransmission"][i] for i in range(InputDir["NumTransSites"]))
        
        TotalCost=Cost_Wind+Cost_Wave+Cost_Kite+Cost_Coaxial+Cost_Transmission #M$
        TotalCost=TotalCost*10**6 #USD (Convert from M$ to USD)


        return TotalCost<=LCOE_Max*MWhYear  

    SaveFeasibility, Save_LCOETarget, Save_LCOE_Achieved, SaveTotalMWAvg = list(), list(), list(), list()
    Save_Y_Wind, Save_Y_Wave, Save_Y_Kite, Save_Y_Coaxial, Save_W_Wind, Save_W_Wave, Save_W_Kite, Save_W_Coaxial, Save_s, Save_Delta = list(), list(), list(), list(), list(), list(), list(), list(), list(), list()
    Save_TotalMWAvgWind, Save_TotalMWAvgWave, Save_TotalMWAvgKite, Save_TotalMWAvgCoaxial, Save_totalMWAvgCurtailment = list(), list(), list(), list(), list()

    LowestLCOE=10**10
    for LCOETarget in tqdm(InputDir["LCOE_RANGE"]):
        
        #Skip based on the algorithm progress, avoid repeating the same LCOE*
        if LCOETarget<LowestLCOE:    
            Bypass=0
            
            #Upperbound For the LCOE Activate Constraint
            LCOETarget_rule_tmp=LCOETarget_rule(Model,LCOETarget)
            Model.LCOE_Target = Constraint(rule=LCOETarget_rule_tmp)
            print("Running Model With LCOE= %.2f" % LCOETarget)
            
            try:
                results=opt.solve(Model, tee=True)
            except:
                Bypass=1
                Model.del_component(Model.LCOE_Target)  
        
            if Bypass==0:
                if (results.solver.status == SolverStatus.ok) and (results.solver.termination_condition == TerminationCondition.optimal):
                    SaveFeasibility.append(1)
                    Save_LCOETarget.append(LCOETarget)
                    
                    Optimal_Y_Wind=np.array([Model.Y_Wind[i].value for i in range(InputDir["NumWindSites"])])
                    Optimal_Y_Wave=np.array([Model.Y_Wave[i].value for i in range(InputDir["NumWaveSites"])])
                    Optimal_Y_Kite=np.array([Model.Y_Kite[i].value for i in range(InputDir["NumKiteSites"])])
                    Optimal_Y_Coaxial=np.array([Model.Y_Coaxial[i].value for i in range(InputDir["NumCoaxialSites"])])

                    Optimal_W_Wind=np.array([Model.W_Wind[i].value for i in range(len(Model.W_Wind))])
                    Optimal_W_Wave=np.array([Model.W_Wave[i].value for i in range(len(Model.W_Wave))])
                    Optimal_W_Kite=np.array([Model.W_Kite[i].value for i in range(len(Model.W_Kite))])
                    Optimal_W_Coaxial=np.array([Model.W_Coaxial[i].value for i in range(len(Model.W_Coaxial))])

                    Optimal_s=np.array([Model.s[i].value for i in range(InputDir["NumTransSites"])])
                    Optimal_Delta=np.array([Model.Delta[i].value for i in range(InputDir["NumTimeSteps"])])
                    
                    Save_Y_Wind.append(Optimal_Y_Wind)
                    Save_Y_Wave.append(Optimal_Y_Wave)
                    Save_Y_Kite.append(Optimal_Y_Kite)
                    Save_Y_Coaxial.append(Optimal_Y_Coaxial)

                    Save_W_Wind.append(Optimal_W_Wind)
                    Save_W_Wave.append(Optimal_W_Wave)
                    Save_W_Kite.append(Optimal_W_Kite)
                    Save_W_Coaxial.append(Optimal_W_Coaxial)

                    Save_s.append(Optimal_s)
                    Save_Delta.append(Optimal_Delta)
                    

                    #Current LCOE
                    EGWind=sum(Optimal_Y_Wind[i]*InputDir["WindEnergy"][:,i].mean()*InputDir["RatedPowerWindTurbine"][i]  for i in range(InputDir["NumWindSites"])) #Energy generation from wind turbines [MW Avg]
                    EGWave=sum(Optimal_Y_Wave[i]*InputDir["WaveEnergy"][:,i].mean()*InputDir["RatedPowerWaveTurbine"][i]  for i in range(InputDir["NumWaveSites"])) #Energy generation from wave turbines [MW Avg]
                    EGKite=sum(Optimal_Y_Kite[i]*InputDir["KiteEnergy"][:,i].mean()*InputDir["RatedPowerKiteTurbine"][i]  for i in range(InputDir["NumKiteSites"])) #Energy generation from kite turbines [MW Avg]
                    EGCoaxial=sum(Optimal_Y_Coaxial[i]*InputDir["CoaxialEnergy"][:,i].mean()*InputDir["RatedPowerCoaxialTurbine"][i]  for i in range(InputDir["NumCoaxialSites"])) #Energy generation from kite turbines [MW Avg]
                    
                    print(f"===== {InputDir["NumTimeSteps"]} =====")
                    TotalCurtailment=sum(Optimal_Delta[t] for t in range(InputDir["NumTimeSteps"]))/InputDir["NumTimeSteps"] #Average curtailment MW

                    MWhYear=(EGWind+EGWave+EGKite+EGCoaxial-TotalCurtailment)*24*365.25 # MWh Avg per year


                    Cost_Wind=sum(Optimal_Y_Wind[i]*InputDir["AnnualizedCostWind"][i]  for i in range(InputDir["NumWindSites"]))
                    Cost_Wave=sum(Optimal_Y_Wave[i]*InputDir["AnnualizedCostWave"][i]  for i in range(InputDir["NumWaveSites"]))
                    Cost_Kite=sum(Optimal_Y_Kite[i]*InputDir["AnnualizedCostKite"][i]  for i in range(InputDir["NumKiteSites"]))
                    Cost_Coaxial=sum(Optimal_Y_Coaxial[i]*InputDir["AnnualizedCostCoaxial"][i]  for i in range(InputDir["NumCoaxialSites"]))
                    
                    
                    Cost_Transmission=sum(Optimal_s[i]*InputDir["AnnualizedCostTransmission"][i] for i in range(InputDir["NumTransSites"]))
                    
                    TotalCost=Cost_Wind+Cost_Wave+Cost_Kite+Cost_Coaxial+Cost_Transmission #M$
                    TotalCost=TotalCost*10**6 #USD
                
                    CurrentLCOE=TotalCost/MWhYear
                    LowestLCOE=CurrentLCOE
                    
                    Save_LCOE_Achieved.append(CurrentLCOE)
                    SaveTotalMWAvg.append(MWhYear/(24*365.25))
                    Save_TotalMWAvgWind.append(EGWind)
                    Save_TotalMWAvgWave.append(EGWave)
                    Save_TotalMWAvgKite.append(EGKite)
                    Save_TotalMWAvgCoaxial.append(EGCoaxial)
                    Save_totalMWAvgCurtailment.append(TotalCurtailment)
                    
                    
                    print("LCOE OPT: %.2f,\n MW Wind: %.2f,\nMW Wave: %.2f,\nMW Kite: %.2f,\nMW Coaxial: %.2f,\nMW Curtailment: %.2f,\nMW Total: %.2f\n" % (CurrentLCOE,EGWind,EGWave,EGKite, EGCoaxial,TotalCurtailment,EGWind+EGWave+EGKite+EGCoaxial-TotalCurtailment))
                    
                    #Delete constraint for its modification in the next step of the for loop
                    Model.del_component(Model.LCOE_Target)

                else:# Something else is wrong
                    Model.del_component(Model.LCOE_Target)
                    shape_wind = (InputDir["NumWindSites"],)
                    shape_kite = (InputDir["NumKiteSites"],)
                    shape_coaxial = (InputDir["NumCoaxialSites"],)
                    shape_trans = (InputDir["NumTransSites"],)
                    shape_time = (InputDir["NumTimeSteps"],)

                    Save_Y_Wind.append(np.zeros(shape_wind))
                    Save_Y_Wave.append(np.zeros(InputDir["NumWaveSites"]))  # Even if empty
                    Save_Y_Kite.append(np.zeros(shape_kite))
                    Save_Y_Coaxial.append(np.zeros(shape_coaxial))
                    
                    Save_W_Wind.append(np.zeros(MaxDesignsWind))
                    Save_W_Wave.append(np.zeros(MaxDesingsWave))
                    Save_W_Kite.append(np.zeros(MaxDesingsKite))
                    Save_W_Coaxial.append(np.zeros(MaxDesingsCoaxial))
                    
                    Save_s.append(np.zeros(shape_trans))
                    Save_Delta.append(np.zeros(shape_time))
                    
                    # For metrics:
                    Save_TotalMWAvgWind.append(0.0)
                    Save_TotalMWAvgKite.append(0.0) 
                    Save_TotalMWAvgCoaxial.append(0.0) 
                    Save_totalMWAvgCurtailment.append(0.0)
                    break

    #Save Results
    if SavePath!=None:
        np.savez(SavePath, 
                ReadMe=ReadMe,
                #Model Inputs
                PathWindDesigns=np.array(PathWindDesigns, dtype=object),
                PathWaveDesigns=PathWaveDesigns,
                PathKiteDesigns=PathKiteDesigns,
                PathCoaxialDesigns=PathCoaxialDesigns,
                PathTransmissionDesign=PathTransmissionDesign,
                LCOE_RANGE=LCOE_RANGE,
                Max_CollectionRadious=Max_CollectionRadious,

                MaxDesignsWind=MaxDesignsWind,
                MaxDesingsWave=MaxDesingsWave,
                MaxDesingsKite=MaxDesingsKite,
                MaxDesingsCoaxial=MaxDesingsCoaxial,

                MinNumWindTurb=MinNumWindTurb,
                MinNumWaveTurb=MinNumWaveTurb,
                MinNumCoaxialTurb=MinNumCoaxialTurb,
                MinNumKiteTrub=MinNumKiteTrub,

                #Model Outputs
                SaveFeasibility=SaveFeasibility,
                Save_LCOETarget=Save_LCOETarget,
                Save_LCOE_Achieved=Save_LCOE_Achieved,
                SaveTotalMWAvg=SaveTotalMWAvg,
                Save_TotalMWAvgWind=Save_TotalMWAvgWind,
                Save_TotalMWAvgWave=Save_TotalMWAvgWave,
                Save_TotalMWAvgKite=Save_TotalMWAvgKite,
                Save_TotalMWAvgCoaxial=Save_TotalMWAvgCoaxial,
                Save_totalMWAvgCurtailment=Save_totalMWAvgCurtailment,
                
                Save_Y_Wind=np.array(Save_Y_Wind, dtype=object),
                Save_Y_Wave=np.array(Save_Y_Wave, dtype=object),
                Save_Y_Kite=np.array(Save_Y_Kite, dtype=object),
                Save_Y_Coaxial=np.array(Save_Y_Coaxial, dtype=object),

                Save_W_Wind=Save_W_Wind,
                Save_W_Wave=Save_W_Wave,
                Save_W_Kite=Save_W_Kite,
                Save_W_Coaxial=Save_W_Coaxial,

                Save_s=Save_s,
                Save_Delta=Save_Delta, #Curtailed Energy
                )