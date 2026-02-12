function cost = getComponentCosts(mass,ratedPower,lthr)
%Mary Maceda
%Updated 5/20/24
%using numbers from Aull et. al 2020
%function of system mass and rated Power
for i = 1:length(mass)
%% Factors
%order = [Structure,Generator/Inverter(PTO),Tether/Interconnects,Floating Platform,Mooring System,Anchor System]
ct = [8;2;3;2;2;0.6]; %[material factors, $/kg, structure, 8$/kg for material may be high for Al6061, tether assumed copper
cm = [30.96;18.98;20;4;0.28;4.02];%[Manufacturing factors, $/kg]
ci = [0.8;0.2;0.2;0.26;1.04;2.088];%[Installation factors, $/kg]
FCR = 0.082; %fixed charge rate, discount applied to capex [Based on ARPA-E Method]
Diathr = 0.012;

%% Solve for masses [Based on percentages of the structural mass]%kg %kite 90% of structural mass, motor and powerElectronics each 5% of structural mass
%"mass" is the mass of the kite structure
SFGProp = mass(i)*0;
motor = mass(i)*0.0556;
powerElectronics = mass(i)*0.0556;
tether = pi*(Diathr/2)^2*lthr*8850;%volume of tether times density of copper, assuming a cylindrical tether
interconnects = 0;

%% Power Based Masses [Based on FP 20kg/kW, Mooring 1.5 kg/kW, Anchor 1.5 kg/kW]%kg
floatingPlatform = 20*ratedPower(i);
mooring = 1.5*ratedPower(i);
anchor = 1.5*ratedPower(i);

%% Solve for OpEx [Based on $86/kW]%$
opex = 86*ratedPower(i);

%% Solve for CapEx and Total Costs
massVect = [(mass(i)+SFGProp);(motor+powerElectronics);(tether+interconnects);floatingPlatform;mooring;anchor];
massVect_adj = massVect.*(ct+cm+ci); 
capex = sum(massVect_adj);
cost(i) = opex + capex*FCR;
end

end