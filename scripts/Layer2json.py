#-------------------------------------------------------------------------------
# Name:        Layer2Json.py
# Purpose:     Export layer to json file
# Parameters:   Feature class to export
#               json File name
#
# Author:      mody
# updates:  Mody 6/2020 - add field alias, length only for string, empty extent
#           Mody 7/2020 - geometry type can be annotation or dimension
#                       - arena and name for oracle/sql server
#                       - do not put subtype if it does not exists
#
# Created:     08/03/2020
#-------------------------------------------------------------------------------

import arcpy
import traceback, sys, json , codecs, os

db = arcpy.GetParameterAsText(0) # workspace
jsonDir = arcpy.GetParameterAsText(1)

# for debug only
#if(db == ""): db = r"D:\Projects\x2470\domainTest.gdb"
if(db == ""): db = r"D:\Projects\x2470\local@data2.sde"
#if(db == ""): db = r"D:\Projects\rastot\rastot.sde"
#if(db == ""): db = r"D:\Projects\x2470\tools2470\modybu-pc.sde"
if(jsonDir == ""): jsonDir = r"D:\Projects\x2470\layerFiles"

primeField = "" # promaery field is calculated in getFields and used in main

#===========================
def main():
    try:
        arcpy.env.workspace = db
        allLayers = arcpy.ListFeatureClasses ()
        for ly in allLayers:
            doLayer(ly)

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
def doLayer(n):
    try:
        p1("Processing layer " + n,"")
        layerDict = {}

        desc = arcpy.Describe(db + "\\" + n)
        # name can have no point (fgdb), one point (oracle), two points (sql server)
        a1 = desc.name.find('.')
        a2 = desc.name.rfind('.')
        if(a1 == -1):
            layerDict["name"] = desc.name
        elif (a1 == a2):
            layerDict["name"] = desc.name[a1 + 1:] # oracle
        else:
            layerDict["name"] = desc.name[a2 + 1:] # sql server

        layerDict["alias"] = desc.aliasName
        layerDict["arena"] = getArena(desc.path)
        sr = desc.spatialReference
        layerDict["csWKID"] = sr.factoryCode # zero for unknown
        layerDict["hasZ"] = desc.hasZ
        layerDict["hasM"] = desc.hasM
        layerDict["featureType"] = desc.featureType
        if(desc.featureType == "Dimension" or desc.featureType == "Annotation"):
            layerDict["geometryType"] = desc.featureType
        else:
            layerDict["geometryType"] = desc.shapeType
        layerDict["featureExtent"] = getExtent(desc,desc.hasZ,desc.hasM)
        layerDict["tolerance"] = getTolerance(sr,desc.hasZ,desc.hasM)
        layerDict["resolution"] = getResolution(sr,desc.hasZ,desc.hasM)
        layerDict["fields"] = getFields(desc.fields,n)
        layerDict["primaryField"] = primeField
        layerDict["indecies"] = getIndecies(desc)
        layerDict["relations"] = getRel(desc)
        subList = arcpy.da.ListSubtypes(db + "\\" + n)
        #p1("[%s]" % (subList[0]['SubtypeField']),"msg")
        if(subList[0]['SubtypeField'] != ""): # if we have subtype
            layerDict["subtypes"] = getSubType(subList,desc.fields)
        # wrire results
        writeJsonFile(layerDict,desc.name)

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
# arena is "local" for local databases, database for SqlServer, alias connection for Oracle
def getArena(path):
    d = arcpy.Describe(path)
    if( d.workspaceType == "FileSystem" or d.workspaceType == "LocalDatabase" ): return "Local"
    if(d.connectionProperties.instance.find("sde:sqlserver") > -1):
        return d.connectionProperties.database # for sql server - database name
    if(d.connectionProperties.instance.find("sde:oracle") > -1):
        #parts = d.connectionProperties.instance.split(':')
        name = os.path.basename(path)
        return name[0:name.index('.')] # parts[2] # for oracle scema name

    return d.connectionProperties.instance

#===========================
# return extent without z or M return a Dict
def getExtent(desc,isZ,isM):
    valDict = {}
    # must do str(xmin) so it get quotes in case of NaN
    valDict["minX"] = str(desc.extent.XMin)
    valDict["maxX"] = str(desc.extent.XMax)
    valDict["minY"] = str(desc.extent.YMin)
    valDict["maxY"] = str(desc.extent.YMax)
    if(isZ == True):
        valDict["minZ"] = desc.extent.XMin
        valDict["maxZ"] = desc.extent.XMax
    if(isM == True):
        valDict["minM"] = desc.extent.YMin
        valDict["maxM"] = desc.extent.YMax
    return valDict

#===========================
# return tolerance as a Dict
def getTolerance(sr,isZ,isM):
    valDict = {}
    valDict["xy"] = sr.XYTolerance
    if(isZ == True): valDict["z"] = sr.ZTolerance
    if(isM == True): valDict["m"] = sr.MTolerance
    return valDict

#===========================
# return Resolution as a Dict
def getResolution(sr,isZ,isM):
    valDict = {}
    valDict["xy"] = sr.XYResolution
    if(isZ == True): valDict["z"] = sr.ZResolution
    if(isM == True): valDict["m"] = sr.MResolution
    return valDict

#===========================
# return fields as a Dict
def getFields(allFields,layer):
    global primeField
    fList = []
    for f in allFields:
        valDict = {}
        valDict["name"]            = f.name
        valDict["alias"]           = f.aliasName
        valDict["fieldType"]       = f.type
        valDict["allowNullValues"] = f.isNullable
        #if((fld.defaultValue is None) == False):
        valDict["defaultValue"]    = f.defaultValue
        valDict["domain"]          = f.domain
        # take care of some field types
        if(f.type == "String"):
            valDict["length"]          = f.length
        #if(f.type != "Geometry" and f.type != "OID"):
        if(f.editable == True and f.type != "Geometry"):
            valDict["populationCount"] = getPopCountSql(f,layer)
        if(f.type == "OID"):
            primeField = f.name
        fList.append(valDict)

    return fList

#===========================
# return indexes as a list
def getIndecies(desc):
    allIndexes = desc.indexes
    idxList = []
    for idx in allIndexes:
        valDict = {}
        valDict["name"] = idx.name
        valDict["unique"] = idx.isUnique
        valDict["ascending"] = idx.isAscending

        flds = idx.fields
        fList = ""
        for f in flds:
            fList = fList + "," + f.name
        valDict["fields"] = fList[1:]
        idxList.append(valDict)

    return idxList

#===========================
# return relashenship as a list
def getRel(desc):
    try:
        # get the workspace
        workspace = desc.path
        # get list of Relationships, list is different if in feature datasets
        relList = []
        # relslasses is a list (for each featuredataset) we add the list into one
        for path, pathnames, rclasses in arcpy.da.Walk(workspace, datatype='RelationshipClass'):
            relList = relList + rclasses
        resultList = []

        for rel in relList:
            d1 = arcpy.Describe(workspace + "\\" + rel)
            # if the origion is the same as layer
            if (hasattr(d1, "originClassNames") == False): continue # no access
            if( d1.originClassNames[0] != desc.name): continue

            relDict = {}
            relDict["relation"] = rel
            relDict["relatedTo"] = d1.destinationClassNames[0]
            relDict["role"] = "origin"
            if(d1.isComposite == True):
                relDict["type"] = "composite"
            else:
                relDict["type"] = "simple"

            relDict["cardinality"] = d1.cardinality
            relDict["notification"] = d1.notification
            relDict["originPrimaryKey"] = d1.originClassKeys[0][0] # list of tuples
            relDict["destinationPrimaryKey"] = d1.originClassKeys[1][0]
            relDict["forwardPathLabel"] = d1.forwardPathLabel
            relDict["backwardPathLabel"] = d1.backwardPathLabel
            resultList.append(relDict)

        return resultList
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
# count how many records with not null and non default value
def getPopCount(fld,fc):
    fields = [fld.name]
    count = 0
    with arcpy.da.SearchCursor(fc, fields) as cursor:
        for row in cursor:
            if(row[0] is None): continue # no value
            if((fld.defaultValue is None) == False):
                if(row[0] == fld.defaultValue): continue # default value
            count = count + 1
    return count

    #===========================
# count how many records with not null and non default value using SQL
def getPopCountSql(fld,fc):
    try:
        if((fld.defaultValue is None) == False):
            if(fld.type == "String"): # if string must have quotes
                sql = "select count(*) from %s where %s <> '%s' and  %s is not null" % (fc,fld.name,fld.defaultValue,fld.name)
            else:
                sql = "select count(*) from %s where %s <> %s and  %s is not null" % (fc,fld.name,fld.defaultValue,fld.name)
        else: # No default
            sql = "select count(*) from %s where %s is not null" % (fc,fld.name)

        #p1(sql,"mess")
        # connect db
        db_conn = arcpy.ArcSDESQLExecute(db)
        # execute command
        res = db_conn.execute(sql)
        return res
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
# return subtype info as dict. sList is dictionery of subtype info
##  "subtypes":{
##      "subtypeField":"sub",
##      "defaultSubtype":"קבוצה שניה",
##      "_subtypes":[      ---subVals array----
##         {      ----oneSubDict-----
##            "code":1,
##            "description":"קבוצה ראשונה",
##            "subtypeFieldMappings":[  ---subFlds  array---
##               {       ---oneFldDict---
##                  "fieldName":"name",
##                  "defaultValue":"xx"
##               },

def getSubType(sList,flds):
    resDict = {}
    subVals = [] # entry for each sub type value

    try:
        # find the default subtype
        for sub in sList:
            if(sList[sub]["Default"] == True):
                resDict["subtypeField"] = sList[sub]['SubtypeField'] # can be taken from any record
                resDict["defaultSubtype"] = sList[sub]["Name"]
                break
        # get all other info per subtype value
        for sub in sList:
            oneSubDict = {}
            oneSubDict["code"] = sub
            oneSubDict["description"] = sList[sub]["Name"]
            # get domain and default values for each field for this subtype
            flsDict = sList[sub]["FieldValues"]

            subFlds = []
            for f in flds:
                oneFldDict = {} # one field info
                if(flsDict[f.name][0] == None and flsDict[f.name][1] == None): continue # no domain or default
                oneFldDict["fieldName"] = f.name
                if(flsDict[f.name][0] != None):
                    oneFldDict["defaultValue"] = flsDict[f.name][0]
                if(flsDict[f.name][1] != None):
                    oneFldDict["domain"] = flsDict[f.name][1].name
                subFlds.append(oneFldDict)
            oneSubDict["subtypeFieldMappings"] = subFlds

            subVals.append(oneSubDict)
        resDict["_subtypes"] = subVals
        return resDict

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
def writeJsonFile(dict,name):
    # there are hebrew strings
    with codecs.open(jsonDir + "\\" + name + ".json", 'w',encoding="utf-8") as outfile:
        json.dump(dict, outfile, ensure_ascii=False)
    return

if __name__ == '__main__':
    main()
