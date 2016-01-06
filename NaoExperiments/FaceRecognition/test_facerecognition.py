#!/usr/bin/python
########### Python 2.7 #############
import httplib, urllib, base64
import json


def getFaceData(pic):
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
        faceId = decoded[0]["faceId"]
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
        print(data)
        conn.close()
    except Exception as e:
        print("[Errno {0}] {1}".format(e.errno, e.strerror))


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
        print(data)
        conn.close()
    except Exception as e:
        print("[Errno {0}] {1}".format(e.errno, e.strerror))


def addFaceToList(faceListId, pic):
    headers = {
        # Request headers
        'Content-Type': 'application/octet-stream',
        'Ocp-Apim-Subscription-Key': 'b269028dbbf64564934cd2a1261890f9',
    }

    params = urllib.urlencode({
        # Request parameters
    })

    try:
        conn = httplib.HTTPSConnection('api.projectoxford.ai')
        conn.request("POST", "/face/v1.0/facelists/" + faceListId + "/persistedFaces?%s" % params, open(pic,"rb").read(), headers)
        response = conn.getresponse()
        data = response.read()
        print(data)
        conn.close()
    except Exception as e:
        print("[Errno {0}] {1}".format(e.errno, e.strerror))


def getFaceId(faceListId, faceId):
    headers = {
        # Request headers
        'Content-Type': 'application/json',
        'Ocp-Apim-Subscription-Key': 'b269028dbbf64564934cd2a1261890f9',
    }

    params = urllib.urlencode({
    })

    body = '{"faceId":"' + faceId + '",\
        "faceListId":"' + faceListId + '",\
        "maxNumOfCandidatesReturned":10\
    }'
    
    print '\n\n\n'
    print body
    print '\n\n\n'
    
    try:
        conn = httplib.HTTPSConnection('api.projectoxford.ai')
        conn.request("POST", "/face/v1.0/findsimilars?%s" % params, body, headers)
        response = conn.getresponse()
        data = response.read()
        print(data)
        conn.close()
    except Exception as e:
        print("[Errno {0}] {1}".format(e.errno, e.strerror))


####################################

faceId = getFaceData("/Users/fhict/Downloads/Faces/reneb2.jpg")
print "face ID:", faceId
getFaceId("42", str(faceId))

#deleteFaceList("42")
#createFaceList("42", "newlist")
#addFaceToList("42", "/Users/fhict/Downloads/Faces/face1.jpg")
#addFaceToList("42", "/Users/fhict/Downloads/Faces/face2.jpg")
#addFaceToList("42", "/Users/fhict/Downloads/Faces/face3.jpg")
#addFaceToList("42", "/Users/fhict/Downloads/Faces/face4.jpg")
#addFaceToList("42", "/Users/fhict/Downloads/Faces/face5.jpg")
#addFaceToList("42", "/Users/fhict/Downloads/Faces/face6.jpg")
#addFaceToList("42", "/Users/fhict/Downloads/Faces/face7.jpg")
#addFaceToList("42", "/Users/fhict/Downloads/Faces/face8.jpg")
#addFaceToList("42", "/Users/fhict/Downloads/Faces/face9.jpg")
#addFaceToList("42", "/Users/fhict/Downloads/Faces/face10.jpg")
#addFaceToList("42", "/Users/fhict/Downloads/Faces/reneb.jpg")

