import os
import io
import sys  
import json
import requests 
import logging
import traceback
import xlsxwriter
from constant_host_unit import *
sys.path.append("")

class host_details:
  def __init__(self):
   self.host_name = ""
   self.host_units = 0
   self.client_name = "Not found!!" 

class tenantInfo:
   def __init__(self):
     self.tenant_url = ""
     self.tenant_token = ""
     self.name = ""

#------------------------------------------------------------------------------
# Author: Nikhil Goenka
# Function to make API call using the token defined in constant.py
# Returns the json object returned using the API call 
#------------------------------------------------------------------------------
def dtApiQuery(logger, endpoint, tenant_info, URL=""):
  try: 
    logger.info("In dtApiQuery")

    if URL == "":
      URL = tenant_info.tenant_url

    query = str(URL) + str(endpoint)
    logger.debug(query)
    get_param = {'Accept':'application/json', 'Authorization':'Api-Token {}'.format(tenant_info.tenant_token)}
    populate_data = requests.get(query, headers = get_param)
    data = populate_data.json()
    logger.info("Execution sucessfull: dtApiQuery")

  except Exception as e:
    logger.error("Received exception while running dtApiQuery", exc_info = e) 

  finally:
    return data

#---------------------------------------------------------------------------------------------
# Author: Nikhil Goenka
# Function to print the entire structure of app_mgmt_zone (will be used for debugging) 
#---------------------------------------------------------------------------------------------
def pretty_print(logger, app_mgmt_zone):
  try:
    logger.info("In pretty_print")
    for mgmt_zone_name in app_mgmt_zone.keys():
        for i in range(len(app_mgmt_zone[mgmt_zone_name])):
          print (mgmt_zone_name + " " + str(len(app_mgmt_zone[mgmt_zone_name])) + "." + app_mgmt_zone[mgmt_zone_name][i].name + "\t" + str(app_mgmt_zone[mgmt_zone_name][i].consumption) + "\t" + str(app_mgmt_zone[mgmt_zone_name][i].dem) + "\n")
  except Exception as e:
    logger.fatal("Received exception while running pretty_print", str(e), exc_info=True)

#---------------------------------------------------------------------------------------------
# Author: Nikhil Goenka
# Function to generate the xlsx file 
#---------------------------------------------------------------------------------------------

def write_data(logger, worksheet, tenant_info, host_info):
    try:
      logger.info("In write_data: ")
      j = 1 

      for entityId in host_info.keys():
        try:
           worksheet.write(j,0,host_info[entityId].host_name)
           worksheet.write(j,1,host_info[entityId].client_name)
           worksheet.write(j,2,float(host_info[entityId].host_units))
        except Exception: 
           logger.error ("Received error while read host_info ", exc_info=e)
        finally:
           j = j + 1 

    except Exception:
      logger.error ("Received error while executing write_data ", exc_info=e)
     
    finally:
      return worksheet

#------------------------------------------------------------------------
# Author: Nikhil Goenka
# Function to call API and populate the excel file
#------------------------------------------------------------------------
def func(logger, totalHostUnits, tenant_info, workbook, host_info):
  try:
    logger.info("In func")
    logger.debug("func: totalHostUnits = %s", totalHostUnits)  

    hosts = dtApiQuery(logger, INFRA_API, tenant_info)

    for host in hosts:
      entityId = host['entityId'] 
      
      current_host_info = host_details()
      try:
        tags = host['tags']
        for tag in tags:
           if (tag['key'] == "ClientName"):
             current_host_info.client_name = tag['value']
      except KeyError:
        current_host_info.client_name = "Not found!!"

      try:
         current_host_info.host_name = host['displayName']
         current_host_info.host_units = float(host['consumedHostUnits'])
         host_info[entityId] = current_host_info
      except Exception: 
         logger.error ("Received error while populating host_info ", exc_info=e)

    worksheet = workbook.add_worksheet(tenant_info.name) 

    worksheet.write(0,0,"Host Name")
    worksheet.write(0,1,"Client Name")
    worksheet.write(0,2,"Host Units Consumption")
    worksheet = write_data(logger, worksheet, tenant_info, host_info)
    logger.info("Successful execution: func")
    
  except Exception as e:
    logger.fatal("Received exception while running func", str(e), exc_info = True)

  finally:
    return workbook

#------------------------------------------------------------------------
# Author: Nikhil Goenka
# Function to call API and populate the excel file
#------------------------------------------------------------------------
def parse_config(filename):
  try:
    stream = open(filename)
    data = json.load(stream)
  except Exception:
    logger.error("Exception encountered in parse_config function : %s ", exc_info=e)
  finally:
    return data

#------------------------------------------------------------------------
# Author: Nikhil Goenka
# Function to call API and populate the excel file
#------------------------------------------------------------------------
def populate_tenant_details(logger, tenant, tenant_info):
  try:
    logger.info("In populate_tenant_details")
    logger.info("In populate_tenant_details %s ", tenant)

    tenant_info.tenant_url = tenant['tenant-URL'] 
    tenant_info.tenant_token = tenant['API-token']
    tenant_info.name = tenant['tenant-name']
  except Exception as e:
    logger.error("Exception encountered while executing populate_tenant_details %s ", str(e))
  finally:
    return tenant_info 
  
#------------------------------------------------------------------------
# Author: Nikhil Goenka
# Function to call API and populate the excel file
#------------------------------------------------------------------------

if __name__ == "__main__":
  try:
    totalHostUnits = 0
    filename = "config.json"
    data = parse_config(filename)


    logging.basicConfig(filename=data['log_file'],
                            filemode='a',
                            format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                            datefmt='%H:%M:%S',
                            level=logging.DEBUG)
    logger = logging.getLogger()
    tenants = data['tenant-details']

    workbook = xlsxwriter.Workbook("Consumption_details.xlsx") 
    for tenant in tenants:
      host_info = {}

      tenant_info = tenantInfo()
      tenant_info = populate_tenant_details(logger, tenant, tenant_info)
      workbook = func(logger, totalHostUnits, tenant_info, workbook, host_info)
   
  except Exception as e:
    logger.error("Received exception while running main", exc_info=e)
  
  finally:
    logger.info("Succesfull completion of running the program")
    workbook.close()
