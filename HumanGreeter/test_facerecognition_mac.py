#!/usr/bin/python
########### Python 2.7 #############
import httplib, urllib, base64
import json
import readline
import os

class FaceRecognition():
    def __init__(self):
        self.key = 'b269028dbbf64564934cd2a1261890f9'

    def getFaceIdFromNewFace(self, pic):
        headers = {
            # Request headers
            'Content-Type': 'application/octet-stream',
            'Ocp-Apim-Subscription-Key': self.key,
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
            faceId = ""
            try:
                faceId = decoded[0]["faceId"].encode('ascii', 'ignore')
            except:
                pass
            return faceId
        except Exception,e:
            print "getFaceIdFromNewFace exception: " + str(e)

    def createFaceList(self, faceListId, facelistName):
        headers = {
            # Request headers
            'Content-Type': 'application/json',
            'Ocp-Apim-Subscription-Key': self.key,
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
            print "createFaceList exception: " + str(e)

    def deleteFaceList(self, faceListId):
        headers = {
            # Request headers
            'Ocp-Apim-Subscription-Key': self.key,
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
            print "deleteFaceList exception: " + str(e)

    def addFaceToList(self, faceListId, pic, userData):
        headers = {
            # Request headers
            'Content-Type': 'application/octet-stream',
            'Ocp-Apim-Subscription-Key': self.key,
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
            print "added face: " + data
            conn.close()
        except Exception,e:
            print "addFaceToList exception: " + str(e)

    def deleteFaceFromList(self, faceListId, name):
        faceId = self.nameToFaceId(faceListId, name)
        headers = {
            # Request headers
            'Ocp-Apim-Subscription-Key': self.key,
        }

        params = urllib.urlencode({
        })

        try:
            conn = httplib.HTTPSConnection('api.projectoxford.ai')
            conn.request("DELETE", "/face/v1.0/facelists/" + faceListId + "/persistedFaces/" + faceId + "?%s" % params, "", headers)
            response = conn.getresponse()
            data = response.read()
            conn.close()
        except Exception,e:
            print "deleteFaceFromList exception: " + str(e)

    def getRecognizedFaceId(self, faceListId, newFaceId):
        headers = {
            # Request headers
            'Content-Type': 'application/json',
            'Ocp-Apim-Subscription-Key': self.key,
        }

        params = urllib.urlencode({
        })

        body = '{"faceId":"' + newFaceId + '",\
            "faceListId":"' + faceListId + '",\
            "maxNumOfCandidatesReturned":1\
        }'
        
        try:
            conn = httplib.HTTPSConnection('api.projectoxford.ai')
            conn.request("POST", "/face/v1.0/findsimilars?%s" % params, body, headers)
            response = conn.getresponse()
            data = response.read()
            conn.close()
            decoded = json.loads(data)
            faceId = ""
            confidence = 0
            try:
                # Use encode() to convert the Unicode strings contained in JSON to ASCII.
                faceId = decoded[0]["persistedFaceId"].encode('ascii', 'ignore')
                confidence = decoded[0]["confidence"]
            except:
                pass
            return faceId, confidence
        except Exception,e:
            print "getRecognizedFaceId exception: " + str(e)

    def getFaceList(self, faceListId):
        headers = {
            # Request headers
            'Ocp-Apim-Subscription-Key': self.key,
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
            print "getFaceList exception: " + str(e)

    def getFaceNames(self, faceListId):
        faceNames = []
        decoded = self.getFaceList(faceListId)
        if decoded:
            try:
                for face in decoded["persistedFaces"]:
                    # Use encode() to convert the Unicode strings contained in JSON to ASCII.
                    faceNames.append(face["userData"].encode('ascii', 'ignore'))
            except Exception,e:
                pass
        return faceNames

    def faceIdToName(self, faceListId, faceId):
        name = ""
        decoded = self.getFaceList(faceListId)
        if decoded:
            try:
                for face in decoded["persistedFaces"]:
                    if face["persistedFaceId"] == faceId:
                        # Use encode() to convert the Unicode strings contained in JSON to ASCII.
                        name = face["userData"].encode('ascii', 'ignore')
                        break
            except Exception,e:
                pass
        return name

    def nameToFaceId(self, faceListId, name):
        faceId = ""
        decoded = self.getFaceList(faceListId)
        if decoded:
            try:
                for face in decoded["persistedFaces"]:
                    if face["userData"] == name:
                        # Use encode() to convert the Unicode strings contained in JSON to ASCII.
                        faceId = face["persistedFaceId"].encode('ascii', 'ignore')
                        break
            except Exception,e:
                pass
        return faceId



####################################
faceRecognition = FaceRecognition()
faceListId = "42"

while True:
    print('"a" to take a picture and add to the database')
    print('"r" to start recognition')
    print('"c" to create and fill a new database')
    print('"d" to remove a face by name from the database')
    print('"x" to delete the database')
    print('"l" to list the database')
    print('"q" to quit')
    line = raw_input(': ')
    if line == 'q':
        break
    elif line == 'a':
        os.system('/Applications/imagesnap')
        line = raw_input('enter your name\n: ')
        faceRecognition.addFaceToList(faceListId, "./snapshot.jpg", line)
    elif line == 'c':
        faceRecognition.createFaceList(faceListId, "newlist")
#        for i in range(20):
#            faceRecognition.addFaceToList(faceListId, "/Users/fhict/Downloads/Faces/face" + str(i) + ".jpg", "face " + str(i))
#        faceRecognition.addFaceToList(faceListId, "/Users/fhict/Downloads/Faces/reneb.jpg", "ReneB")
    elif line == 'd':
        line = raw_input('enter name of face to be removed\n: ')
        faceRecognition.deleteFaceFromList(faceListId, line)
    elif line == 'x':
        faceRecognition.deleteFaceList(faceListId)
    elif line == 'r':
        os.system('/Applications/imagesnap')
        newFaceId = faceRecognition.getFaceIdFromNewFace("./snapshot.jpg")
        print "new face ID: " + newFaceId
        persistedFaceId, confidence = faceRecognition.getRecognizedFaceId(faceListId, newFaceId)
        print "recognized face ID: " + persistedFaceId + ", confidence: " + str(confidence)
        name = faceRecognition.faceIdToName(faceListId, persistedFaceId)
        print "\n***** recognized face name: " + name + ", confidence: " + str(confidence) + " *****\n"
    elif line == 'l':
        print faceRecognition.getFaceNames(faceListId)



