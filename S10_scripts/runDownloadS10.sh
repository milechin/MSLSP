#!/bin/bash -l
#$ -j y

# -t 10 # creating an array job 

tile=$1
baseDir=$2
imgStartYr=$3
imgEndYr=$4
tileDir=$5

# tile='13RFN'

# tile='18TWN'
# baseDir='/projectnb/modislc/users/sjstone/MSLSP/input/S10/'
# imgStartYr='2021'
# imgEndYr='2021'
# tileDir='/projectnb/modislc/users/sjstone/MSLSP/input/S10/18TWN/tile/'

imgDir="${baseDir}${tile}/images/"
tempDir="${baseDir}${tile}/images/temp/"

module load miniconda
conda activate /projectnb/modislc/users/sjstone/.conda/envs/S10env

mkdir -p $tempDir

#Get Images from web
##########

python /projectnb/modislc/users/aliceni/MSLSP/S10_scripts/getS10_DM.py $tile $imgStartYr $imgEndYr $imgDir $baseDir $tileDir $tempDir

# for y in `seq $imgStartYr $imgEndYr`;
# do
#   #downloadHLS.sh -t $tile -y $y $imgDir 
   
#   # imgSD="${y}-01-01"
#   # imgED="${y}-12-31"
# #   mkdir -p $tempDir
#     # python /projectnb/modislc/users/sjstone/MSLSP/S10_scripts/getS10.py $tile $y $imgDir $baseDir $tileDir $tempDir
#     python /projectnb/modislc/users/sjstone/MSLSP/S10_scripts/getS10_DM.py $tile $y $imgDir $baseDir $tileDir $tempDir
#   # python /projectnb/modislc/users/sjstone/MSLSP/S10_scripts/getS10.py $tile $y $imgDir $baseDir $tileDir $tempDir $SGE_TASK_ID
# #   rm -r $tempDir
# done

# rm -r $tempDir
