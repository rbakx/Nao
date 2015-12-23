# -*- encoding: UTF-8 -*-
""" Say 'hello, you' each time a human face is detected

"""

import sys
import time
import re

from naoqi import ALProxy
from naoqi import ALBroker
from naoqi import ALModule


# Global variables. These must be global otherwise the callback functions will report for example: 'python object not found FaceRecognizer'.
SpeechRecognizer = None
FaceRecognizer = None
ReactToTouch = None


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
        self.touched = value[0][0]

    def getTouch(self):
        if self.touched != "":
            tmpTouched = self.touched
            self.touched = ""
            return tmpTouched
        else:
            return ""


class speechRecognitionModule(ALModule):
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
        vocabulary = ["rene", "bianca", "lara", "demi", "selma"]
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

    def getWord(self):
        if self.word != "":
            tmpWord = self.word
            self.word = ""
            return tmpWord
        else:
            return ""

    def onWordRecognized(self, key, value, message):
        if(len(value) > 1 and value[1] >= 0.3):
            # Stop speech recognition.
            self.stopListening()
            self.word = value[0]

class FaceRecognitionModule(ALModule):
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
            self.memory.unsubscribeToEvent("FaceDetected", "FaceRecognizer")
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
            print str(e)


    def unlearnAllFaces(self):
        # Create a proxy to ALFaceDetection
        try:
            faceProxy = ALProxy("ALFaceDetection")
            faceProxy.clearDatabase()
        except Exception, e:
            print str(e)

    
    def startFaceDetection(self):
        # Subscribe to the FaceDetected event:
        try:
            self.timeFaceDetectionStartedInSeconds = int(time.time())
            self.memory.subscribeToEvent("FaceDetected", "FaceRecognizer", "onFaceDetected")
            # Set eye leds.
            self.leds.fadeRGB("FaceLeds", 255*256*0 + 256*0 + 255, 0.2)
        except Exception, e:
            print str(e)

    def stopFaceDetection(self):
        # Unsubscribe to the FaceDetected event:
        try:
            self.memory.unsubscribeToEvent("FaceDetected", "FaceRecognizer")
            self.leds.fadeRGB("FaceLeds", 255*256*100 + 256*100 + 100, 0.2)
        except Exception, e:
            print str(e)

    def startFaceTracking(self):
        try:
            # Start face tracking.
            self.tracker.registerTarget("Face", 0.2)
            self.tracker.setMode("Head")  # Only move head.
            self.tracker.track("Face")
            # Set stiffness of head to 1.0 as this is required for face tracking.
            self.motion.setStiffnesses("Head", 1.0)
        except Exception, e:
            print str(e)

    def stopFaceTracking(self):
        try:
            # Stop face tracking.
            self.tracker.stopTracker()
            self.tracker.unregisterAllTargets()
        except Exception, e:
            print str(e)

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
            # We detected faces !
            # For each face, we can read its shape info and ID.
            # First Field = TimeStamp.
            # Second Field = array of face_Info's.
            self.timeInSeconds = val[0][0]
            # After calling subscribeToEvent() the face detection module will generate some events.
            # The reason is unknown, they might be older events from just before the call to unsubscribeToEvent(), although the timestamp
            # is new.
            # Therefore we ignore the events generated right after the call to startFaceDetection().
            if int(time.time()) - self.timeFaceDetectionStartedInSeconds < 3:
                return
            # Set timeFirstRecognitionInSeconds if this is the start of a new recognition.
            if self.timeFirstRecognitionInSeconds == 0:
                self.timeFirstRecognitionInSeconds = self.timeInSeconds
            faceInfoArray = val[1]
            try:
                faceInfo = faceInfoArray[0]
                Time_Filtered_Reco_Info = faceInfoArray[1]
                # First Field = Shape info.
                faceShapeInfo = faceInfo[0]
                # Second Field = Extra info (empty for now).
                faceExtraInfo = faceInfo[1]
                #print "face detected!, confidence = " + str(faceExtraInfo[1]) + ", length = " + str(len(Time_Filtered_Reco_Info))
                if faceExtraInfo[1] > 0.5:
                    # Stop face detection.
                    self.stopFaceDetection()
                    self.face = faceExtraInfo[2]
                    # Indicate the end of this recognition.
                    self.timeFirstRecognitionInSeconds = 0
                else:
                    if self.timeFirstRecognitionInSeconds != 0 and self.timeInSeconds - self.timeFirstRecognitionInSeconds > 3:
                        # Face is not recognized for more then three seconds, so we consider it to be unknown.
                        # Stop face detection.
                        self.stopFaceDetection()
                        self.face = "unknown"
                        # Indicate the end of this recognition.
                        self.timeFirstRecognitionInSeconds = 0
                self.previousTimeInSeconds = self.timeInSeconds
        
            except Exception, e:
                print str(e)


# Remove this dummy GeneratedClass() when running in Choregraphe.
class GeneratedClass():
    def __init__(self):
        pass


class MyClass(GeneratedClass):
    def __init__(self):
        global SpeechRecognizer, FaceRecognizer, ReactToTouch
        GeneratedClass.__init__(self)
        # We need this broker to be able to construct
        # NAOqi modules and subscribe to other modules
        # The broker must stay alive until the program exists


        # Warning: module names must be global variables.
        # The name given to the constructor must be the name of the variable.
        SpeechRecognizer = speechRecognitionModule("SpeechRecognizer")
        FaceRecognizer = FaceRecognitionModule("FaceRecognizer")
        ReactToTouch = ReactToTouchModule("ReactToTouch")
        self.tts = ALProxy("ALTextToSpeech")

    def onLoad(self):
        #put initialization code here
        pass
        
    def onUnload(self):
        # put clean-up code here
        pass
    
    def onInput_onStart(self):
        global SpeechRecognizer, FaceRecognizer, ReactToTouch
        FaceRecognizer.unlearnAllFaces()
        doContinue = True
        self.tts.say("let's greet some people")
        FaceRecognizer.startFaceTracking()
        while doContinue:
            FaceRecognizer.startFaceDetection()
            face = ""
            while True:
                # Possibility to interrupt by touch.
                if re.search('.*bumper.*', ReactToTouch.getTouch(), re.IGNORECASE):
                    doContinue = False
                    break
                face = FaceRecognizer.getFace();
                if face != "":
                    break
                time.sleep(0.5)
                
            if doContinue and face == "unknown":
                self.tts.say("what is your name?")
                SpeechRecognizer.startListening()
                startTime = int(time.time())
                name = ""
                while True:
                    # Possibility to interrupt by touch.
                    if re.search('.*bumper.*', ReactToTouch.getTouch(), re.IGNORECASE):
                        doContinue = False
                        break
                    if int(time.time()) - startTime > 5:
                        # Timeout.
                        SpeechRecognizer.stopListening()
                        break
                    name = SpeechRecognizer.getWord()
                    if name != "":
                        break
                    time.sleep(0.5)
            
                if doContinue and name != "":
                    self.tts.say("nice to meet you, " + name + ",please keep still for a moment")
                    FaceRecognizer.learnFace(name)
                    self.tts.say("thank you, I will remember you!")
            elif doContinue:
                self.tts.say("hi again," + face)

        # Important to call exit on the modules created, otherwise the next time ALModule.__init__(self, name)
        # will fail because the modules are already registered!
        FaceRecognizer.stopFaceDetection()
        FaceRecognizer.stopFaceTracking()
        SpeechRecognizer.stopListening()
        SpeechRecognizer.exit()
        FaceRecognizer.exit()
        ReactToTouch.exit()
        # Uncomment the below line in Choregraphe.
        #self.onStopped() #activate the output of the box

    def onInput_onStop(self):
        self.onUnload() #it is recommended to reuse the clean-up as the box is stopped
        self.onStopped() #activate the output of the box


# Remove main() when running in Choregraphe.
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
    myClass.onInput_onStart()
    myClass.onUnload()


if __name__ == "__main__":
    main()
