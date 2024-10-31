This directory contains new runs of 30m MSLSP along with test runs of 10m MSLSP for Buenos Aires National Wildlife Refuge in Tucson, AZ using only Sentinel-2 data.

This directory contains all of the scripts to run the 30m product and the 10m product

Currently there is a 'dev' version of the rScript and rFunctions script that are located in the directory with the rest of the MSLSP scripts.
This 'dev' version contains the updated adjustments to the functionality to allow to run using S10 data

S10 download script which is under: '/projectnb/modislc/users/sjstone/MSLSP/S10_scripts/getS10_DM.py' or
				    '/projectnb/modislc/users/aliceni/MSLSP/S10_scripts/getS10_DM.py'
The only thing that needs to be adjusted in that script is including your copernicus username and password where it is indidated as variables 'copernicus_user' and 'copernicus_password': dataspace.copernicus.eu

These are the steps that need to be taken to run MSLSP at 10m:
    1. go to the 'MSLSP_Parameters.json' file and set the following parameters:
        a. imgStartYr & imgEndYr, to the desired range *
        b. phenStartYr * phenEndYr to the desired range
        c. downloadImagery -- if the Sentinel-2 imagery needs to be downloaded set to true, if not set to false
        d. preprocessImagery -- if there is a pre-processed version of the Sentinel - 2 data already generated in the directory set to false, if not set to true
        e. runPhenology -- if you want to run the phenology metrics, set to true
        under the 'SCC' section need to adjust:
            f. workDir, logDir, and dataDir to be the locations where you want to have these directories
            g. rScript & rFunctions - path to these two scripts
            h. runS10 -- set to true if you want to run using only Sentinel-2 / generate 10m product 
    2. go to the 'MSLSP_submitTiles_SCC.sh' script and adjust the following things:
        a. set the 'parameters' variable to the path where you have the adjusted 'MSLSP_Parameters.json' file
        b. set the 'tileList' variable to the path where you have a text file that containst the desired tiles to run
	c. change the file paths in the rest of the script to your respective directories: there should be 4 paths to change
    3. once the above two files are adjusted select the entire 'MSLSP_submitTiles_SCC.sh' script and run it to submit jobs to the SCC, the numbers of jobs that are submitted will depend on the the number of tiles and if you are downloading imagery or not
        
        

CAVEATS:
    * For the image data range ensure that there is one additional year (either before or after) if running the phenology metrics for only one year (I usually would set the imgStartYr to 2018 and the imgEndYr to 2020 if running phenology for only 2019)

    
