# -*- encoding: UTF-8 -*-
""" Say 'hello, you' each time a human face is detected.
If no face is detected sound tracking is activated.
If a face is detected face tracking is activated.
If a face is recognized Nao sais hello and waves its hand.
"""

import sys
import time
import re
import subprocess
import json
import httplib, urllib, base64

from naoqi import ALProxy
from naoqi import ALBroker
from naoqi import ALModule


# Global variables. Module names must be global otherwise the callback functions will report for example:
# 'python object not found FaceDetector'.
SpeechRecognizer = None
FaceDetector = None
ReactToTouch = None


# runShellCommandWait(cmd) will block until 'cmd' is finished.
# This because the communicate() method is used to communicate to interact with the process through the redirected pipes.
def runShellCommandWait(cmd):
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True).communicate()[0]


def testConnected():
    try :
        stri = "http://www.google.com"
        data = urllib.urlopen(stri)
        return True
    except Exception, e:
        return False


# The below class is an alternative to the Nao speech recognition.
# The Nao speech recognition only works with predefined words while with the Google Speech to Text
# all speech can be recognized. The below class is not a module in the NAOqi sense because we do not
# register it with ALModule.__init__(). This is not needed as we do not use subscribeToEvent().
# Instead we just wait for Google to respond.
class speechRecognitionGoogleModule():
    def __init__(self):
        try:
            self.recorder = ALProxy("ALAudioRecorder")
            self.player = ALProxy('ALAudioPlayer')
            self.leds = ALProxy("ALLeds")
        except Exception, e:
            print "speechRecognitionGoogleModule exception: " + str(e)
    def speechToText(self):
        text = ""
        try:
            # Stop recording if recorder is still recording, added for robustness.
            try:
                self.recorder.stopMicrophonesRecording()
            except Exception, e:
                pass
            self.player.playFile("/usr/share/naoqi/wav/begin_reco.wav")
            # Start recording 16000 Hz, ogg format, front microphone.
            self.recorder.startMicrophonesRecording("/home/nao/reneb/speech.ogg", "ogg", 16000, (0,0,1,0))
            for _ in range(8):
            # Twinkle eye leds to indicate Nao is listening.
                self.leds.fadeRGB("FaceLeds", 255*256*0 + 256*0 + 0, 0.2)
                self.leds.fadeRGB("FaceLeds", 255*256*0 + 256*0 + 255, 0.2)
            self.recorder.stopMicrophonesRecording()
            self.player.playFile("/usr/share/naoqi/wav/end_reco.wav")
            runShellCommandWait('ffmpeg -y -i /home/nao/reneb/speech.ogg /home/nao/reneb/speech.flac')
            stdOutAndErr = runShellCommandWait('curl -s -X POST --header "content-type: audio/x-flac; rate=16000;" --data-binary @"/home/nao/reneb/speech.flac" "http://www.google.com/speech-api/v2/recognize?client=chromium&lang=en_US&key=AIzaSyC3qc74SxJI7fIv747QPlSQPS0rl4AnSAM"')
        except Exception, e:
            print "speechToText exception: " + str(e)
            return text
        # Google always replies with an empty JSON response '{"result":[]}' on the first line.
        # If there is speech, The second line contains the actual JSON result.
        # If there is no speech, there is no second line so we have to check this.
        if len(stdOutAndErr.splitlines()) != 2:
            # Return empty text to indicate the speech is invalid.
            return text
        stdOutAndErr = stdOutAndErr.splitlines()[1]
        # Now stdOutAndErr contains the JSON response from the STT engine.
        decoded = json.loads(stdOutAndErr)
        try:
            confidence = decoded["result"][0]["alternative"][0]["confidence"]  # not a string but a float
        except Exception, e:
            print "speechToText exception: " + str(e)
            pass
        try:
            # Use encode() to convert the Unicode strings contained in JSON to ASCII.
            text = decoded["result"][0]["alternative"][0]["transcript"].encode('ascii', 'ignore')
        except Exception, e:
            print "speechToText exception: " + str(e)
            pass

        return text


# Class to react on touch.
class ReactToTouchModule(ALModule):
    """ A simple module able to react to sensor events.
    Leave this doc string else this module will not be bound!

    """
    def __init__(self, name):
        ALModule.__init__(self, name)
        # No need for IP and port here because
        # we have our Python broker connected to NAOqi broker
        self.memory = ALProxy("ALMemory")
        # Unsubscribe to event if still subscribed.
        try:
            self.memory.unsubscribeToEvent("TouchChanged", "ReactToTouch")
        except Exception, e:
            pass
        self.memory.subscribeToEvent("TouchChanged", "ReactToTouch", "onTouched")
        self.touched = ""
    
    def onTouched(self, strVarName, value):
        self.touched = str(value)

    def getTouch(self):
        if self.touched != "":
            tmpTouched = self.touched
            self.touched = ""
            return tmpTouched
        else:
            return ""


# Class for native Nao speech recognition. This recognition must be fed with predefined keywords.
class speechRecognitionNaoModule(ALModule):
    """ A simple module able to react to speech events.
    Leave this doc string else this module will not be bound!

    """
    def __init__(self, name):
        ALModule.__init__(self, name)
        # No need for IP and port here because
        # we have our Python broker connected to NAOqi broker
        self.memory = ALProxy("ALMemory")
        # Unsubscribe to event if still subscribed to stop ASR engine.
        try:
            self.memory.unsubscribeToEvent("WordRecognized", "SpeechRecognizer")
        except Exception, e:
            pass
        self.asr = ALProxy("ALSpeechRecognition")
        vocabulary = ["rene", "james"]
        self.asr.setVocabulary(vocabulary, False )
        self.asr.setVisualExpression(True)
        self.word = ""
    
    def startListening(self):
        # Subscribe to the WordRecognized event:
        try:
            self.memory.subscribeToEvent("WordRecognized", "SpeechRecognizer", "onWordRecognized")
        except Exception, e:
            pass

    def stopListening(self):
        # Unsubscribe to the WordRecognized event:
        try:
            self.memory.unsubscribeToEvent("WordRecognized", "SpeechRecognizer")
        except Exception, e:
            pass

    def speechToText(self):
        self.startListening()
        startTime = int(time.time())
        wordRecognized = ""
        while True:
            if int(time.time()) - startTime > 5:
                # Timeout.
                self.stopListening()
                break
            if self.word != "":
                wordRecognized = self.word
                self.word = ""
                break
            time.sleep(0.5)
        return wordRecognized

    def onWordRecognized(self, key, value, message):
        if(len(value) > 1 and value[1] >= 0.3):
            # Stop speech recognition.
            self.stopListening()
            self.word = value[0]

# Face detection class to detect faces.
# This class also contains face tracking and sound tracking functionality.
class FaceDetectionModule(ALModule):
    """ A simple module able to react to facedetection events.
    Leave this doc string else this module will not be bound!

    """
    def __init__(self, name):
        ALModule.__init__(self, name)
        # No need for IP and port here because
        # we have our Python broker connected to NAOqi broker
        self.memory = ALProxy("ALMemory")
        # Unsubscribe to event if still subscribed.
        try:
            self.memory.unsubscribeToEvent("FaceDetected", "FaceDetector")
        except Exception, e:
            pass
        self.tracking = ALProxy("ALTracker")
        self.timeFaceDetectionStartedInSeconds = 0
        self.timeFirstRecognitionInSeconds = 0
        self.previousTimeInSeconds = 0
        self.timeInSeconds = 0
        self.face = ""
        self.tracker = ALProxy("ALTracker")
        self.motion = ALProxy("ALMotion")
        self.leds = ALProxy("ALLeds")
        
    def learnFace(self, face):
        # Create a proxy to ALFaceDetection
        try:
            faceProxy = ALProxy("ALFaceDetection")
            # First forget face to be enable learning it again.
            faceProxy.forgetPerson(face)
            faceProxy.learnFace(face)
        except Exception, e:
            print "learnFace exception: " + str(e)


    def unlearnAllFaces(self):
        # Create a proxy to ALFaceDetection
        try:
            faceProxy = ALProxy("ALFaceDetection")
            faceProxy.clearDatabase()
        except Exception, e:
            print "unlearnAllFaces exception: " + str(e)

    def lookForward(self):
        self.tracker.lookAt([1.0, 0.0, 0.0], 0, 0.20, False)

    def startFaceDetection(self):
        # Subscribe to the FaceDetected event:
        try:
            self.timeFaceDetectionStartedInSeconds = int(time.time())
            self.memory.subscribeToEvent("FaceDetected", "FaceDetector", "onFaceDetected")
            # Set eye leds.
            self.leds.fadeRGB("FaceLeds", 255*256*0 + 256*0 + 255, 0.2)
        except Exception, e:
            print "startFaceDetection exception: " + str(e)

    def stopFaceDetection(self):
        # Unsubscribe to the FaceDetected event:
        try:
            self.memory.unsubscribeToEvent("FaceDetected", "FaceDetector")
            self.leds.fadeRGB("FaceLeds", 255*256*100 + 256*100 + 100, 0.2)
        except Exception, e:
            print "stopFaceDetection exception: " + str(e)

    def startFaceTracking(self):
        try:
            # Start face tracking.
            self.tracker.registerTarget("Face", 0.2)
            self.tracker.setMode("Head")  # Only move head.
            self.tracker.track("Face")
            # Set stiffness of head to 1.0 as this is required for face tracking.
            self.motion.setStiffnesses("Head", 1.0)
        except Exception, e:
            print "startFaceTracking exception: " + str(e)
            pass

    def stopFaceTracking(self):
        try:
            # Stop face tracking.
            self.tracker.stopTracker()
            self.tracker.unregisterTarget("Face")
        except Exception, e:
            print "stopFaceTracking exception: " + str(e)
            pass

    def startSoundTracking(self):
        try:
            # Start face tracking.
            self.soundLocation = ALProxy("ALSoundLocalization")
            self.soundLocation.setParameter("Sensitivity", 0.7)
            self.tracker.setEffector("None")
            self.tracker.registerTarget("Sound", [0.5, 0.1])
            self.tracker.setRelativePosition([-0.3, 0.0, 0.0, 0.1, 0.1, 0.3])
            self.tracker.setMode("Head")  # Only move head.
            self.tracker.track("Sound")
            # Set stiffness of head to 1.0 as this is required for face tracking.
            self.motion.setStiffnesses("Head", 1.0)
        except Exception, e:
            print "startSoundTracking exception: " + str(e)
            pass

    def stopSoundTracking(self):
        try:
            # Stop face tracking.
            self.tracker.setEffector("None")
            self.tracker.stopTracker()
            self.tracker.unregisterTarget("Sound")
        except Exception, e:
            print "stopSoundTracking exception: " + str(e)
            pass

    def getFace(self):
        if self.face != "":
            tmpFace = self.face
            self.face = ""
            return tmpFace
        else:
            return ""

    def onFaceDetected(self, *_args):
        """ This will be called each time a face is
        detected.
        Leave this doc string else this method will not be bound!
        """
        val = self.memory.getData("FaceDetected")
        if(val and isinstance(val, list) and len(val) >= 2):
            # Stop face detection.
            self.stopFaceDetection()
            # indicata a face is detected.
            self.face = "detected"


# The below class is an alternative to the Nao face recognition, which is quite limited.
# This class makes use of cloud services to recognize faces.
class FaceRecognition():
    def __init__(self):
        self.key = '43acf60f71204ca78c4c09a1cb2c6916'

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

        faceId = None
        try:
            conn = httplib.HTTPSConnection('api.projectoxford.ai')
            conn.request("POST", "/face/v1.0/detect?%s" % params, open(pic,"rb").read(), headers)
            response = conn.getresponse()
            data = response.read()
            conn.close()
            decoded = json.loads(data)
            # Use encode() to convert the Unicode strings contained in JSON to ASCII.
            try:
                faceId = decoded[0]["faceId"].encode('ascii', 'ignore')
            except:
                pass
            return faceId
        except Exception,e:
            print "getFaceIdFromNewFace exception: " + str(e)
            return faceId

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
            return True
        except Exception,e:
            print "createFaceList exception: " + str(e)
            return False

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
            return True
        except Exception,e:
            print "deleteFaceList exception: " + str(e)
            return False

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
            return True
        except Exception,e:
            print "addFaceToList exception: " + str(e)
            return False

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
            return True
        except Exception,e:
            print "deleteFaceFromList exception: " + str(e)
            return False

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
        
        faceId = ""
        confidence = 0
        try:
            conn = httplib.HTTPSConnection('api.projectoxford.ai')
            conn.request("POST", "/face/v1.0/findsimilars?%s" % params, body, headers)
            response = conn.getresponse()
            data = response.read()
            conn.close()
            decoded = json.loads(data)
            try:
                # Use encode() to convert the Unicode strings contained in JSON to ASCII.
                faceId = decoded[0]["persistedFaceId"].encode('ascii', 'ignore')
                confidence = decoded[0]["confidence"]
            except:
                pass
            return faceId, confidence
        except Exception,e:
            print "getRecognizedFaceId exception: " + str(e)
            return faceId, confidence

    def getFaceList(self, faceListId):
        headers = {
            # Request headers
            'Ocp-Apim-Subscription-Key': self.key,
        }

        params = urllib.urlencode({
        })

        decoded = None
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
            return decoded

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


# ********** REMOVE THIS DUMMY GeneratedClass() WHEN RUNNING IN CHOREGRAPHE **********
class GeneratedClass():
    def __init__(self):
        pass

# Main Class containing the standard block methods. When used in Choregraphe this class is initiated automatically by NAOqi.
class MyClass(GeneratedClass):
    def __init__(self):
        GeneratedClass.__init__(self)
        # Do not initialize modules here because in Choregraphe __init__() is called whenever the behavior starts,
        # even if this block is not started yet. Stopping the behavior will not call onUnload() then which means the module's exit()
        # function is not called. This gives problems the next time the behavior is started.
        # Instead, initialize the modules in onLoad(). This method is only called when the block is started. Stopping the behavior in
        # Choregraphe will then also stop the block by calling onUnload().
    
    def onLoad(self):
        # Put initialization code here
        # Warning: module names must be global variables.
        # The name given to the constructor must be the name of the variable.
        global SpeechRecognizer, FaceDetector, ReactToTouch
        # Enable one of the two next lines for Nao speech recognition or Google speech recognition
        #SpeechRecognizer = speechRecognitionNaoModule("SpeechRecognizer")
        SpeechRecognizer = speechRecognitionGoogleModule()
        
        FaceDetector = FaceDetectionModule("FaceDetector")
        ReactToTouch = ReactToTouchModule("ReactToTouch")
        self.faceRecognition = FaceRecognition()
        self.faceListId = "42"
        self.tts = ALProxy("ALTextToSpeech")
        self.doContinue = False
        
    def onUnload(self):
        # Put clean-up code here.
        # This method is called when the onInput_onStart() thread ends which will activate the onStopped output
        # AND this onStopped output is connected to the onStopped output of the Choregraphe bounding box.
        # This method is also called when the behavior is stopped in Choregraphe.
        # The behavior can be stopped in Choregraphe using the red 'Stop' button, or by using the 'Run Behavior'
        # box and activating the 'onStop' input. In Python this means the ALBehaviorManager method stopBehavior() is called.
        # First set self.doContinue to False otherwise the onInput_onStart() thread will continue if it is still running.
        self.doContinue = False
        # Important to call exit on the modules created, otherwise the next time ALModule.__init__(self, name)
        # will fail because the modules are already registered!
        # Use try...except here in case the (one of the) modules have already exitted.
        try:
            FaceDetector.stopFaceDetection()
        except Exception, e:
            pass
        try:
            FaceDetector.stopFaceTracking()
        except Exception, e:
            pass
        try:
            FaceDetector.stopSoundTracking()
        except Exception, e:
            pass
        try:
            FaceDetector.exit()
        except Exception, e:
            pass
        
        # For Google speech recognition instead of Nao speech recognition disable the next try...except block.
#        try:
#            SpeechRecognizer.stopListening()
#            SpeechRecognizer.exit()
#        except Exception, e:
#            pass

        try:
            ReactToTouch.exit()
        except Exception, e:
            pass
    
    def onInput_onStart(self):
        global SpeechRecognizer, FaceDetector, ReactToTouch
        
        self.audiodevice = ALProxy("ALAudioDevice")
        self.audiodevice.setOutputVolume(50)
        
        self.doContinue = True
        self.tts.say("let's greet some people")
        while self.doContinue:
            # Check if connected to the internet.
            while self.doContinue and testConnected() == False:
                self.tts.say("not connected to the internet")
                time.sleep(5)
            FaceDetector.startFaceDetection()
            FaceDetector.startSoundTracking()
            face = ""
            count = 0
            while self.doContinue:
                if count == 10:
                    FaceDetector.lookForward()
                    count = 0
                count = count + 1
                face = FaceDetector.getFace();
                if face != "":
                    break
                time.sleep(0.5)
            # When the behaviour was stopped in Choregraphe by using the red 'Stop' button, onUnload() will be
            # called which will set self.doContinue to False. If this is the case, this thread must also be stopped.
            if self.doContinue == False:
                return
            print "face detected, going to take a picture"
            self.tts.say("let me check on you")
            FaceDetector.startFaceTracking()
            try:
                photoCapture = ALProxy("ALPhotoCapture")
                photoCapture.setResolution(3) # 1280x960 resolution
                photoCapture.setCameraID(0) # Top camera
                photoCapture.setPictureFormat("jpg")
                photoCapture.takePicture("/home/nao/reneb", "snapshot.jpg")
            except Exception, e:
                print "photoCapture exeption: " + str(e)
            newFaceId = self.faceRecognition.getFaceIdFromNewFace("/home/nao/reneb/snapshot.jpg")
            if newFaceId is not None:
                print "new face ID: " + newFaceId
                persistedFaceId, confidence = self.faceRecognition.getRecognizedFaceId(self.faceListId, newFaceId)
                print "recognized face ID: " + persistedFaceId + ", confidence: " + str(confidence)
                name = self.faceRecognition.faceIdToName(self.faceListId, persistedFaceId)
                print "\n***** recognized face name: " + name + ", confidence: " + str(confidence) + " *****\n"
                if self.doContinue and name == "":
                    self.tts.say("what is your name?")
                    name = SpeechRecognizer.speechToText()
                    if self.doContinue and name != "":
                        self.tts.say("nice to meet you, " + name + ", please keep still for a moment")
                        if self.faceRecognition.addFaceToList(self.faceListId, "/home/nao/reneb/snapshot.jpg", name) == True:
                            self.tts.say("thank you, I will remember you!")
                        else:
                            self.tts.say("could not add face to facelist")
                elif self.doContinue:
                    # ********** UNCOMMENT THE LINE BELOW WHEN RUNNING IN CHOREGRAPHE **********
                    #self.onRecognized()
                    self.tts.say("hi again," + name)
            else:
                self.tts.say("sorry, could not take a good picture")
            time.sleep(5.0)

    def finish(self):
        try:
            FaceDetector.stopFaceDetection()
        except Exception, e:
            pass
        try:
            FaceDetector.stopFaceTracking()
        except Exception, e:
            pass
        try:
            FaceDetector.stopSoundTracking()
        except Exception, e:
            pass
        self.doContinue = False
        # ********** UNCOMMENT THE LINE BELOW WHEN RUNNING IN CHOREGRAPHE **********
        #self.onStopped() #activate the output of the box

    def onInput_onStop(self):
        self.onStopped() #activate the output of the box


# ********** REMOVE main() WHEN RUNNING IN CHOREGRAPHE **********
def main():
    """ Main entry point

    """
    # We need this broker to be able to construct
    # NAOqi modules and subscribe to other modules
    # The broker must stay alive until the program exists
    myBroker = ALBroker("myBroker",
        "0.0.0.0",   # listen to anyone
        0,           # find a free port and use it
        "nao.local",         # parent broker IP
        9559)       # parent broker port

    myClass = MyClass()
    myClass.onLoad()
    myClass.onInput_onStart()
    myClass.onUnload()


if __name__ == "__main__":
    main()
