#!/usr/bin/python
########### Python 2.7 #############
import httplib, urllib, base64
import json
import readline
import os


def getFaceIdFromNewFace(pic):
    headers = {
        # Request headers
        'Content-Type': 'application/octet-stream',
        'Ocp-Apim-Subscription-Key': 'b269028dbbf64564934cd2a1261890f9',
    }

    params = urllib.urlencode({
        'returnFaceLandmarks': 'true',
        'returnFaceAttributes': 'age',
    })

    try:
        conn = httplib.HTTPSConnection('api.projectoxford.ai')
        conn.request("POST", "/face/v1.0/detect?%s" % params, open(pic,"rb").read(), headers)
        response = conn.getresponse()
        data = response.read()
        conn.close()
        decoded = json.loads(data)
        # Use encode() to convert the Unicode strings contained in JSON to ASCII.
        faceId = decoded[0]["faceId"].encode('ascii', 'ignore')
        return faceId
    except Exception,e:
        print str(e)


def createFaceList(faceListId, facelistName):
    headers = {
        # Request headers
        'Content-Type': 'application/json',
        'Ocp-Apim-Subscription-Key': 'b269028dbbf64564934cd2a1261890f9',
    }

    params = urllib.urlencode({
    })
    
    body = '{\
        "name":"' + facelistName + '",\
        "userData":"User-provided data attached to the face list"\
    }'

    try:
        conn = httplib.HTTPSConnection('api.projectoxford.ai')
        conn.request("PUT", "/face/v1.0/facelists/" + faceListId + "?%s" % params, body, headers)
        response = conn.getresponse()
        data = response.read()
        conn.close()
    except Exception,e:
        print str(e)


def deleteFaceList(faceListId):
    headers = {
        # Request headers
        'Ocp-Apim-Subscription-Key': 'b269028dbbf64564934cd2a1261890f9',
    }

    params = urllib.urlencode({
    })

    try:
        conn = httplib.HTTPSConnection('api.projectoxford.ai')
        conn.request("DELETE", "/face/v1.0/facelists/" + faceListId + "?%s" % params, "{body}", headers)
        response = conn.getresponse()
        data = response.read()
        conn.close()
    except Exception,e:
        print str(e)


def addFaceToList(faceListId, pic, userData):
    headers = {
        # Request headers
        'Content-Type': 'application/octet-stream',
        'Ocp-Apim-Subscription-Key': 'b269028dbbf64564934cd2a1261890f9',
    }

    params = urllib.urlencode({
        # Request parameters
        'userData': userData,
    })

    try:
        conn = httplib.HTTPSConnection('api.projectoxford.ai')
        conn.request("POST", "/face/v1.0/facelists/" + faceListId + "/persistedFaces?%s" % params, open(pic,"rb").read(), headers)
        response = conn.getresponse()
        data = response.read()
        conn.close()
    except Exception,e:
        print str(e)


def getRecognizedFaceId(faceListId, newFaceId):
    headers = {
        # Request headers
        'Content-Type': 'application/json',
        'Ocp-Apim-Subscription-Key': 'b269028dbbf64564934cd2a1261890f9',
    }

    params = urllib.urlencode({
    })

    body = '{"faceId":"' + newFaceId + '",\
        "faceListId":"' + faceListId + '",\
        "maxNumOfCandidatesReturned":10\
    }'
    
    try:
        conn = httplib.HTTPSConnection('api.projectoxford.ai')
        conn.request("POST", "/face/v1.0/findsimilars?%s" % params, body, headers)
        response = conn.getresponse()
        data = response.read()
        conn.close()
        decoded = json.loads(data)
        # Use encode() to convert the Unicode strings contained in JSON to ASCII.
        faceId = decoded[0]["persistedFaceId"].encode('ascii', 'ignore')
        return faceId
    except Exception,e:
        print str(e)


def getFaceList(faceListId):
    headers = {
        # Request headers
        'Ocp-Apim-Subscription-Key': 'b269028dbbf64564934cd2a1261890f9',
    }

    params = urllib.urlencode({
    })

    try:
        userData = ""
        conn = httplib.HTTPSConnection('api.projectoxford.ai')
        conn.request("GET", "/face/v1.0/facelists/" + faceListId + "?%s" % params, "", headers)
        response = conn.getresponse()
        data = response.read()
        conn.close()
        decoded = json.loads(data)
        return decoded
    except Exception,e:
        print str(e)


def getFaceNames(faceListId):
    decoded = getFaceList(faceListId)
    try:
        faceNames = []
        for face in decoded["persistedFaces"]:
            # Use encode() to convert the Unicode strings contained in JSON to ASCII.
            faceNames.append(face["userData"].encode('ascii', 'ignore'))
        return faceNames
    except Exception,e:
        print str(e)


def getFaceInfo(faceListId, faceId):
    decoded = getFaceList(faceListId)
    try:
        userData = ""
        for face in decoded["persistedFaces"]:
            if face["persistedFaceId"] == faceId:
                # Use encode() to convert the Unicode strings contained in JSON to ASCII.
                userData = face["userData"].encode('ascii', 'ignore')
                break
        return userData
    except Exception,e:
        print str(e)


####################################

while True:
    line = raw_input('"a" to take a picture and add to the dadabase\n"r" to start recognition\n"c" to create and fill new database\n"d" to delete database\n"l" to list database\n"q" to quit\n: ')
    if line == 'q':
        break
    elif line == 'a':
        os.system('/Applications/imagesnap')
        line = raw_input('enter your name\n: ')
        addFaceToList("42", "./snapshot.jpg", line)
    elif line == 'c':
        createFaceList("42", "newlist")
        addFaceToList("42", "/Users/fhict/Downloads/Faces/face1.jpg", "face 1")
        addFaceToList("42", "/Users/fhict/Downloads/Faces/face2.jpg", "face 2")
        addFaceToList("42", "/Users/fhict/Downloads/Faces/face3.jpg", "face 3")
        addFaceToList("42", "/Users/fhict/Downloads/Faces/face4.jpg", "face 4")
        addFaceToList("42", "/Users/fhict/Downloads/Faces/face5.jpg", "face 5")
        addFaceToList("42", "/Users/fhict/Downloads/Faces/face6.jpg", "face 6")
        addFaceToList("42", "/Users/fhict/Downloads/Faces/face7.jpg", "face 7")
        addFaceToList("42", "/Users/fhict/Downloads/Faces/face8.jpg", "face 8")
        addFaceToList("42", "/Users/fhict/Downloads/Faces/face9.jpg", "face 9")
        addFaceToList("42", "/Users/fhict/Downloads/Faces/face10.jpg", "face 10")
        #addFaceToList("42", "/Users/fhict/Downloads/Faces/reneb.jpg", "ReneB")
    elif line == 'd':
        deleteFaceList("42")
    elif line == 'r':
        os.system('/Applications/imagesnap')
        newFaceId = getFaceIdFromNewFace("./snapshot.jpg")
        print "new face ID:", newFaceId
        persistedFaceId = getRecognizedFaceId("42", newFaceId)
        print "recognized face ID:", persistedFaceId
        name = getFaceInfo("42", persistedFaceId)
        print "***** recognized face name:", name, "*****"
    elif line == 'l':
        print getFaceNames("42")



