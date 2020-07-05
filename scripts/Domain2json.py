#-------------------------------------------------------------------------------
# Name:        Domain2Json.py
# Purpose:     Export domains to json files
# Parameters:   Geodatabase (workspace)
#               Folder to write all files to (one file per domain)
#
# Author:      mody
#
# Created:     08/03/2020
# Updates:
#           2/7/2020 mody - Less printing
#                           Do not write code domain that has no values
#-------------------------------------------------------------------------------

import arcpy
import traceback, sys, json , codecs

db = arcpy.GetParameterAsText(0) # geodatabase for domain
jsonDir = arcpy.GetParameterAsText(1) # dir for json files

# for debug only
#if(db == ""): db = r"D:\Projects\x2470\domainTest.gdb"
if(db == ""): db = r"D:\Projects\x2470\local@data1.sde"
if(jsonDir == ""): jsonDir = r"D:\Projects\x2470\domainFiles"

#===========================
def main():
    try:
        allDomains = arcpy.da.ListDomains(db)
        for domain in allDomains:
            #p1("Processing domain " + domain.name,"")
            if domain.domainType == 'CodedValue':
                doCodeDomain(domain)
            else:
                doRangeDomain(domain)

        return
    except arcpy.ExecuteError:
        msgs = arcpy.GetMessages(2)
        p1(msgs,"err")

    except:
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        pymsg = "PYTHON ERRORS:\nTraceback info:\n" + tbinfo + "\nError Info:\n" + str(sys.exc_info()[1])
        msgs = "ArcPy ERRORS:\n" + arcpy.GetMessages(2) + "\n"

        p1(pymsg,"err")
        p1(msgs,"err")

#===========================
# print function
def p1(mess,mode):
    print(mess)
    if(mode == "err"):
       arcpy.AddError(mess)
    else:
        arcpy.AddMessage(mess)
    return

#===========================
def doCodeDomain(domain):
    p1( "code domain = " + domain.name,"")
    domainDict = {} # dictionery that contain domain data
    domainGeneralProps(domainDict,domain)
    # get coded values
    vals = domain.codedValues
    domainDict["values"] = []
    # do not write if code value have no values
    if(len(vals) == 0):
        p1("Domain %s have no values" % (domain.name),"msg")
        return
    for v in vals:
        domainDict["values"].append({"code": v, "description" : vals[v]})
    # write dictionery to file
    writeJsonFile(domainDict,domain.name)
    return

#===========================
def doRangeDomain(domain):
    p1( "Range domain = " + domain.name,"")
    domainDict = {}
    domainGeneralProps(domainDict,domain)
    domainDict["minimumValue"] = domain.range[0]
    domainDict["maximumValue"] = domain.range[1]
    writeJsonFile(domainDict,domain.name)
    return
#===========================
# get properties that are common to codedValue and range
def domainGeneralProps(dict,domain):
    dict["name"] = domain.name
    dict["description"] = domain.description
    dict["fieldType"] = domain.type
    dict["domainType"] = domain.domainType
    dict["splitPolicy"] = domain.splitPolicy
    dict["mergePolicy"] = domain.mergePolicy
    return

def writeJsonFile(dict,name):
    # there are hebrew strings
    goodName = fixName(name)
    #print goodName
    with codecs.open(jsonDir + "\\" + goodName + ".json", 'w',encoding="utf-8") as outfile:
        json.dump(dict, outfile, ensure_ascii=False)
    return

def fixName(name):
    badChar = ['/',':']
    newName = name
    for char in badChar:
        newName = newName.replace(char,"_")

    return newName


if __name__ == '__main__':
    main()
