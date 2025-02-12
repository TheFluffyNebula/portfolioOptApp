import numpy as np

# Load the npz file
data = np.load('./OceanPortfolioOptimization/OutputData/Portfolios/Wind_BOEM_2007_Upscale3h_0.02Degree_GenCost_ATB_15MW_2030_Transmission_1200MW.npz')

# Print all array names stored in the file
print("Arrays in the npz file:", data.files)

# Loop through and print details of each array
for array_name in data.files:
    array = data[array_name]
    print(f"\nArray name: {array_name}")
    print(f"Shape: {array.shape}")
    print(f"Data type: {array.dtype}")
    print("Content:")
    print(array)