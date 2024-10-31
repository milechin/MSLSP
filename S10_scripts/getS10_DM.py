from datetime import date, timedelta
import requests
import pandas as pd
import geopandas as gpd
from shapely.geometry import shape
from sentinelsat import read_geojson, geojson_to_wkt
import zipfile
import os
import sys
import rasterio as rio
import glob
import shutil



systemArguments = sys.argv
print(systemArguments)
tileID = systemArguments[1]
year = systemArguments[2]
endDate = systemArguments[3]
savePath = systemArguments[4]
baseDir = systemArguments[5]
tilePath = systemArguments[6]
tempPath = systemArguments[7]
# taskID = int(systemArguments[7])

print(tileID)
print(year)
print(savePath)
print(os.path.exists(tempPath))

tileShapefile = gpd.read_file('/projectnb/modislc/users/aliceni/MSLSP/tileShapefile/sentinel_2_index_shp.shp')

copernicus_user = 'username'
copernicus_password = 'password'

# startList = [year+'-01-01', year+'-02-01', year+'-03-01', year+'-04-01', year+'-05-01', year+'-06-01', year+'-07-01', year+'-08-01',
#                 year+'-09-01', year+'-10-01', year+'-11-01', year+'-12-01']
# endList = [year+'-01-31', year+'-02-28', year+'-03-31', year+'-04-30', year+'-05-31', year+'-06-30', year+'-07-31', year+'-08-31',
#             year+'-09-30', year+'-10-31', year+'-11-30', year+'-12-31']
bands = ['B08', 'B11', 'B12', 'B05', 'B06', 'B07', 'B02', 'B03', 'B04', 'SCL']

# if it is a leap year need to adjust the end day of the month for Feb to the 29th
# if ((year == '2016') or (year == '2020') or (year == '2024')):
#     endList[1] = year + '-02-29'

# need to generate json of the tile extent
selectedTile = tileShapefile[tileShapefile['Name'] == tileID]
geojsonSaveName = tilePath + tileID + '.geojson'
selectedTile.to_file(geojsonSaveName, driver='GeoJSON')
footprint = geojson_to_wkt(read_geojson(geojsonSaveName))
ft = footprint.split('(', 1)[1][:-1]

# defining the data collection that should be downloaded, in this case it is Sentinel-2
data_collection = "SENTINEL-2"

def get_keycloak(username: str, password: str):
    data = {
        "client_id": "cdse-public",
        "username": username,
        "password": password,
        "grant_type": "password",
    }
    try:
        r = requests.post(
            "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token",
            data=data,
        )
        r.raise_for_status()
    except Exception as e:
        raise Exception(
            f"Keycloak token creation failed. Reponse from the server was: {r.json()}"
        )
    
    return r.json()

# DENNIS: Created new function to reresh the token.
# source: https://documentation.dataspace.copernicus.eu/APIs/OData.html#product-download
def refesh_keycloak(refresh_token: str):
    data = {
        "grant_type": "refresh_token",
        "client_id": "cdse-public",
        "refresh_token": refresh_token,
    }
    try:
        r = requests.post(
            "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token",
            data=data,
        )
        r.raise_for_status()
    except Exception as e:
        raise Exception(
            f"Keycloak refresh token failed. Reponse from the server was: {r.json()}"
        )
    
    return r.json()



# get access token based on username and password
token_data = get_keycloak(copernicus_user, copernicus_password)


# download images for each month, limit to how many images can be read in at once 
# for loc in list(range(0, len(startList)))[taskID-1:taskID]:

for yr in list(range(int(year), int(endDate) + 1)):
    yr = str(yr)
    startList = [yr+'-01-01', yr+'-02-01', yr+'-03-01', yr+'-04-01', yr+'-05-01', yr+'-06-01', yr+'-07-01', yr+'-08-01',
                yr+'-09-01', yr+'-10-01', yr+'-11-01', yr+'-12-01']
    endList = [yr+'-01-31', yr+'-02-28', yr+'-03-31', yr+'-04-30', yr+'-05-31', yr+'-06-30', yr+'-07-31', yr+'-08-31',
             yr+'-09-30', yr+'-10-31', yr+'-11-30', yr+'-12-31']
    
    if ((yr == '2016') or (yr == '2020') or (yr == '2024')):
        endList[1] = yr + '-02-29'
        
    for loc in list(range(0, len(startList))):
        startDate = startList[loc]
        endDate = endList[loc]
        
        requesting = requests.get(
                f"https://catalogue.dataspace.copernicus.eu/odata/v1/Products?$filter=Collection/Name eq '{data_collection}' and  OData.CSC.Intersects(area=geography'SRID=4326;{ft}') and ContentDate/Start gt {startDate}T00:00:00.000Z and ContentDate/Start lt {endDate}T00:00:00.000Z&$count=True&$top=1000"
                )
        statusCode = requesting.status_code
    
        if statusCode != 200:
            requesting = requests.get(
                f"https://catalogue.dataspace.copernicus.eu/odata/v1/Products?$filter=Collection/Name eq '{data_collection}' and  OData.CSC.Intersects(area=geography'SRID=4326;{ft}') and ContentDate/Start gt {startDate}T00:00:00.000Z and ContentDate/Start lt {endDate}T00:00:00.000Z&$count=True&$top=1000"
                )
            if tryRequestAgain.status_code != 200:
                print(f'unable to pull data for tile {tileID} from {startDate} to {endDate} due to status code: {tryRequestAgain.status_code}')
                continue
    
        json_ = requesting.json()
        p = pd.DataFrame.from_dict(json_['value']) # Fetch available dataset 
    
        if p.shape[0] > 0:
            p['geometry'] = p['GeoFootprint'].apply(shape)
    
            # Convert pandas dataframe to Geopandas dataframe by setting up geometry
            productDF = gpd.GeoDataFrame(p).set_geometry('geometry')
            # in this next chunk removing the L1C data, selecting only the specified tile, the data that is available online, and removing duplicates
            productDF = productDF[~productDF['Name'].str.contains('L1C')]
            productDF["identifier"] = productDF["Name"].str.split(".").str[0]
            productDF = productDF[productDF['Name'].str.contains(tileID)].reset_index(drop = True)
            productDF = productDF[productDF['Online'] == True].reset_index(drop = True)
            productDF = productDF.sort_values('ModificationDate', ascending = False).reset_index(drop = True) # sorting by the modification date
            dupLoc = productDF.duplicated('ContentDate', keep = 'first')
            productDF = productDF[~dupLoc].reset_index(drop = True)
    
            print(f"total L2A tiles found {len(productDF)} for tile {tileID} from {startDate} to {endDate}")
            allfeat = len(productDF)
        
                # if no data is found print that no data is found
            if allfeat == 0:
                print('No tiles found for date range and location')
    
            else:
                # download tiles from server
                for index, feat in enumerate(productDF.iterfeatures()):
                    imgName = feat['properties']['Name'].split('.')[0]
                    imgPath = savePath + imgName + '/'
                    # print(imgPath)
                    if os.path.exists(imgPath) == True:
                        print('path exists')
                        # need to check if there are files in the folder
                        tifFiles = glob.glob(imgPath + '*.tif')
                        if len(tifFiles) >= len(bands):
                            print(f'files have already been downloaded for {imgName}')
                            continue
                    else:
                        print('path does not exist, making folder for images')
                        # make the directory
                        os.mkdir(imgPath)
    
                    
                # create requests session
                    # DENNIS: using 'with' when creating a session will ensure 
                    #          the connection is closed proplerly
                    with requests.Session() as s:
                        
                        # DENNIS: refresh the token. The access token expires after 10 minutes:
                        #       source: https://documentation.dataspace.copernicus.eu/Quotas.html
                        token_data = refesh_keycloak(token_data['refresh_token'])
                        headers = {'Authorization': f"Bearer {token_data['access_token']}"}
    
                        url = f"https://zipper.dataspace.copernicus.eu/odata/v1/Products({feat['properties']['Id']})/$value"
    
                        s.headers.update(headers)
                        response = s.get(url, headers=headers, stream=True)
    
                        # DENNIS: This will check if the response was good.
                        #         If not, it will raise an exception and terminate the script.
                        response.raise_for_status()
    
                        with open(tempPath + feat['properties']['Name'] + '.zip', "wb") as file:
                            for chunk in response.iter_content(chunk_size=8192):
                                if chunk:
                                    file.write(chunk)
    
                    # DENNIS: Moved try further down, so we can catch post processing errors
                    try:        
                        # unzip the downloaded file
                        zf = zipfile.ZipFile(tempPath + feat['properties']['Name'] + '.zip', 'r')
                        zf.extractall(tempPath)
                        zf.close()
                        print(f'files unzipped for {imgName}')
                        # move the desired bands to the final folder
                        for selBand in bands:
                            path = glob.glob(tempPath + '/' + feat['properties']['Name'] + '/GRANULE/**/IMG_DATA/**/*' + selBand + '*.jp2', recursive = True)
                            if len(path) > 1:
                                resList = []
                                for i in path:
                                    # print(i.split('/')[-2][1:3])
                                    resList.append(int(i.split('/')[-2][1:3]))
                                minRes = str(min(resList))
                                # print(minRes)
                                # print(min(resList))
                                path = next(x for x in path if '/R'+minRes+'m/' in x)
                            #     path = path[0]
                            else:
                                path = path[0]
    
                            
                            imgName = path.split('/')[-1]
                            updatedImgName = imgName.replace('jp2', 'tif')
                            # copying the selected band files to the specified save path
                            openFile = rio.open(path)
                            readFile = openFile.read()
                            # save the file to the new folder as a tif instead of jp2
                            rio.open(
                                imgPath + updatedImgName,
                                'w',
                                height=readFile.shape[1],
                                width=readFile.shape[2],
                                count=readFile.shape[0],
                                dtype=readFile.dtype.name,
                                crs=openFile.crs,
                                transform=openFile.transform,
                                compress='lzw'
                            ).write(readFile)
                        # copying the file with information on the mean solar azimuth and zenith angle
                        metaDatPath = glob.glob(tempPath + '/' + feat['properties']['Name'] + '/GRANULE/**/MTD_TL.xml')
                        shutil.copy(metaDatPath[0], imgPath)
                    except:
                        print('Problem encountered with processing the downloaded tile.')
    #                     print('respond:', response)
                            # shutil.copy(path, imgPath)
                            # print(path)
                        
    
        else : # If no tiles found for given date range and AOI
            print('no data found') 

# for loc in list(range(0, len(startList))):
#     startDate = startList[loc]
#     endDate = endList[loc]
    
#     requesting = requests.get(
#             f"https://catalogue.dataspace.copernicus.eu/odata/v1/Products?$filter=Collection/Name eq '{data_collection}' and  OData.CSC.Intersects(area=geography'SRID=4326;{ft}') and ContentDate/Start gt {startDate}T00:00:00.000Z and ContentDate/Start lt {endDate}T00:00:00.000Z&$count=True&$top=1000"
#             )
#     statusCode = requesting.status_code

#     if statusCode != 200:
#         requesting = requests.get(
#             f"https://catalogue.dataspace.copernicus.eu/odata/v1/Products?$filter=Collection/Name eq '{data_collection}' and  OData.CSC.Intersects(area=geography'SRID=4326;{ft}') and ContentDate/Start gt {startDate}T00:00:00.000Z and ContentDate/Start lt {endDate}T00:00:00.000Z&$count=True&$top=1000"
#             )
#         if tryRequestAgain.status_code != 200:
#             print(f'unable to pull data for tile {tileID} from {startDate} to {endDate} due to status code: {tryRequestAgain.status_code}')
#             continue

#     json_ = requesting.json()
#     p = pd.DataFrame.from_dict(json_['value']) # Fetch available dataset 

#     if p.shape[0] > 0:
#         p['geometry'] = p['GeoFootprint'].apply(shape)

#         # Convert pandas dataframe to Geopandas dataframe by setting up geometry
#         productDF = gpd.GeoDataFrame(p).set_geometry('geometry')
#         # in this next chunk removing the L1C data, selecting only the specified tile, the data that is available online, and removing duplicates
#         productDF = productDF[~productDF['Name'].str.contains('L1C')]
#         productDF["identifier"] = productDF["Name"].str.split(".").str[0]
#         productDF = productDF[productDF['Name'].str.contains(tileID)].reset_index(drop = True)
#         productDF = productDF[productDF['Online'] == True].reset_index(drop = True)
#         productDF = productDF.sort_values('ModificationDate', ascending = False).reset_index(drop = True) # sorting by the modification date
#         dupLoc = productDF.duplicated('ContentDate', keep = 'first')
#         productDF = productDF[~dupLoc].reset_index(drop = True)

#         print(f"total L2A tiles found {len(productDF)} for tile {tileID} from {startDate} to {endDate}")
#         allfeat = len(productDF)
    
#             # if no data is found print that no data is found
#         if allfeat == 0:
#             print('No tiles found for date range and location')

#         else:
#             # download tiles from server
#             for index, feat in enumerate(productDF.iterfeatures()):
#                 imgName = feat['properties']['Name'].split('.')[0]
#                 imgPath = savePath + imgName + '/'
#                 # print(imgPath)
#                 if os.path.exists(imgPath) == True:
#                     print('path exists')
#                     # need to check if there are files in the folder
#                     tifFiles = glob.glob(imgPath + '*.tif')
#                     if len(tifFiles) >= len(bands):
#                         print(f'files have already been downloaded for {imgName}')
#                         continue
#                 else:
#                     print('path does not exist, making folder for images')
#                     # make the directory
#                     os.mkdir(imgPath)

                
#             # create requests session
#                 # DENNIS: using 'with' when creating a session will ensure 
#                 #          the connection is closed proplerly
#                 with requests.Session() as s:
                    
#                     # DENNIS: refresh the token. The access token expires after 10 minutes:
#                     #       source: https://documentation.dataspace.copernicus.eu/Quotas.html
#                     token_data = refesh_keycloak(token_data['refresh_token'])
#                     headers = {'Authorization': f"Bearer {token_data['access_token']}"}

#                     url = f"https://zipper.dataspace.copernicus.eu/odata/v1/Products({feat['properties']['Id']})/$value"

#                     s.headers.update(headers)
#                     response = s.get(url, headers=headers, stream=True)

#                     # DENNIS: This will check if the response was good.
#                     #         If not, it will raise an exception and terminate the script.
#                     response.raise_for_status()

#                     with open(tempPath + feat['properties']['Name'] + '.zip', "wb") as file:
#                         for chunk in response.iter_content(chunk_size=8192):
#                             if chunk:
#                                 file.write(chunk)

#                 # DENNIS: Moved try further down, so we can catch post processing errors
#                 try:        
#                     # unzip the downloaded file
#                     zf = zipfile.ZipFile(tempPath + feat['properties']['Name'] + '.zip', 'r')
#                     zf.extractall(tempPath)
#                     zf.close()
#                     print(f'files unzipped for {imgName}')
#                     # move the desired bands to the final folder
#                     for selBand in bands:
#                         path = glob.glob(tempPath + '/' + feat['properties']['Name'] + '/GRANULE/**/IMG_DATA/**/*' + selBand + '*.jp2', recursive = True)
#                         if len(path) > 1:
#                             resList = []
#                             for i in path:
#                                 # print(i.split('/')[-2][1:3])
#                                 resList.append(int(i.split('/')[-2][1:3]))
#                             minRes = str(min(resList))
#                             # print(minRes)
#                             # print(min(resList))
#                             path = next(x for x in path if '/R'+minRes+'m/' in x)
#                         #     path = path[0]
#                         else:
#                             path = path[0]

                        
#                         imgName = path.split('/')[-1]
#                         updatedImgName = imgName.replace('jp2', 'tif')
#                         # copying the selected band files to the specified save path
#                         openFile = rio.open(path)
#                         readFile = openFile.read()
#                         # save the file to the new folder as a tif instead of jp2
#                         rio.open(
#                             imgPath + updatedImgName,
#                             'w',
#                             height=readFile.shape[1],
#                             width=readFile.shape[2],
#                             count=readFile.shape[0],
#                             dtype=readFile.dtype.name,
#                             crs=openFile.crs,
#                             transform=openFile.transform,
#                             compress='lzw'
#                         ).write(readFile)
#                     # copying the file with information on the mean solar azimuth and zenith angle
#                     metaDatPath = glob.glob(tempPath + '/' + feat['properties']['Name'] + '/GRANULE/**/MTD_TL.xml')
#                     shutil.copy(metaDatPath[0], imgPath)
#                 except:
#                     print('Problem encountered with processing the downloaded tile.')
# #                     print('respond:', response)
#                         # shutil.copy(path, imgPath)
#                         # print(path)
                    

#     else : # If no tiles found for given date range and AOI
#         print('no data found')  















