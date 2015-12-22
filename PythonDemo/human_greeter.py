# -*- encoding: UTF-8 -*-
""" Say 'hello, you' each time a human face is detected

"""

import sys
import time

from naoqi import ALProxy
from naoqi import ALBroker
from naoqi import ALModule

# Global variables
SpeechRecognizer = None
memorySpeech = None
HumanGreeter = None
memoryFace = None


class speechRecognizerModule(ALModule):
    """ A simple module able to react to speech events.
    Leave this doc string else this module will not be bound!

    """
    def __init__(self, name):
        global memorySpeech
        ALModule.__init__(self, name)
        # No need for IP and port here because
        # we have our Python broker connected to NAOqi broker
        memorySpeech = ALProxy("ALMemory")
        # Unsubscribe to event if still subscribed to stop ASR engine.
        try:
            memorySpeech.unsubscribeToEvent("WordRecognized", "SpeechRecognizer")
        except Exception, e:
            pass
        self.asr = ALProxy("ALSpeechRecognition")
        vocabulary = ["rene", "bianca", "lara", "demi", "selma"]
        self.asr.setVocabulary(vocabulary, False )
        self.asr.setVisualExpression(True)
        self.word = ""
    
    def startListening(self):
        global memorySpeech
        # Subscribe to the WordRecognized event:
        try:
            memorySpeech.subscribeToEvent("WordRecognized", "SpeechRecognizer", "onWordRecognized")
        except Exception, e:
            pass

    def stopListening(self):
        global memorySpeech
        # Subscribe to the WordRecognized event:
        try:
            memorySpeech.unsubscribeToEvent("WordRecognized", "SpeechRecognizer")
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
        global memorySpeech
        if(len(value) > 1 and value[1] >= 0.3):
            # Stop speech recognition.
            self.stopListening()
            self.word = value[0]

class HumanGreeterModule(ALModule):
    """ A simple module able to react to facedetection events.
    Leave this doc string else this module will not be bound!

    """
    def __init__(self, name):
        global memoryFace
        ALModule.__init__(self, name)
        # No need for IP and port here because
        # we have our Python broker connected to NAOqi broker
        memoryFace = ALProxy("ALMemory")
        # Unsubscribe to event if still subscribed.
        try:
            memoryFace.unsubscribeToEvent("FaceDetected", "HumanGreeter")
        except Exception, e:
            pass
        self.timeFaceDetectionStartedInSeconds = 0
        self.timeFirstRecognitionInSeconds = 0
        self.previousTimeInSeconds = 0
        self.face = ""
        self.leds = ALProxy("ALLeds")
    
    def startFaceDetection(self):
        global memorySpeech
        # Subscribe to the WordRecognized event:
        try:
            self.timeFaceDetectionStartedInSeconds = int(time.time())
            memoryFace.subscribeToEvent("FaceDetected", "HumanGreeter", "onFaceDetected")
            self.leds.fadeRGB("FaceLeds", 255*256*0 + 256*0 + 255, 0.2)
        except Exception, e:
            pass

    def stopFaceDetection(self):
        global memorySpeech
        # Subscribe to the WordRecognized event:
        try:
            memoryFace.unsubscribeToEvent("FaceDetected", "HumanGreeter")
            self.leds.fadeRGB("FaceLeds", 255*256*100 + 256*100 + 100, 0.2)
        except Exception, e:
            pass

    def getFace(self):
        global memoryFace
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
        global memoryFace, timeInSeconds
        val = memoryFace.getData("FaceDetected")
        if(val and isinstance(val, list) and len(val) >= 2):
            # We detected faces !
            # For each face, we can read its shape info and ID.
            # First Field = TimeStamp.
            # Second Field = array of face_Info's.
            timeInSeconds = val[0][0]
            # After calling subscribeToEvent() the face detection module will generate some events.
            # The reason is unknown, they might be older events from just before the call to unsubscribeToEvent(), although the timestamp
            # is new.
            # Therefore we ignore the events generated right after the call to startFaceDetection().
            if int(time.time()) - self.timeFaceDetectionStartedInSeconds < 3:
                return
            # Set timeFirstRecognitionInSeconds if this is the start of a new recognition.
            if self.timeFirstRecognitionInSeconds == 0:
                print "**************** started"
                self.timeFirstRecognitionInSeconds = timeInSeconds
            faceInfoArray = val[1]
            try:
                faceInfo = faceInfoArray[0]
                Time_Filtered_Reco_Info = faceInfoArray[1]
                # First Field = Shape info.
                faceShapeInfo = faceInfo[0]
                # Second Field = Extra info (empty for now).
                faceExtraInfo = faceInfo[1]
                print "face detected!, confidence = " + str(faceExtraInfo[1]) + ", length = " + str(len(Time_Filtered_Reco_Info))
                if faceExtraInfo[1] > 0.5:
                    # Stop face detection.
                    self.stopFaceDetection()
                    self.face = faceExtraInfo[2]
                    # Indicate the end of this recognition.
                    self.timeFirstRecognitionInSeconds = 0
                else:
                    if self.timeFirstRecognitionInSeconds != 0 and timeInSeconds - self.timeFirstRecognitionInSeconds > 3:
                        # Face is not recognized for more then three seconds, so we consider it to be unknown.
                        # Stop face detection.
                        self.stopFaceDetection()
                        self.face = "unknown"
                        # Indicate the end of this recognition.
                        self.timeFirstRecognitionInSeconds = 0
                self.previousTimeInSeconds = timeInSeconds
        
            except Exception, e:
                print str(e)


def learnFace(face):
    # Create a proxy to ALFaceDetection
    try:
      faceProxy = ALProxy("ALFaceDetection")
      # First forget face to be enable learning it again.
      faceProxy.forgetPerson(face)
      faceProxy.learnFace(face)
    except Exception, e:
      print str(e)


def unlearnAllFaces():
    # Create a proxy to ALFaceDetection
    try:
      faceProxy = ALProxy("ALFaceDetection")
      faceProxy.clearDatabase()
    except Exception, e:
      print str(e)


def main():
    """ Main entry point

    """
    global SpeechRecognizer, HumanGreeter

    # We need this broker to be able to construct
    # NAOqi modules and subscribe to other modules
    # The broker must stay alive until the program exists
    myBroker = ALBroker("myBroker",
       "0.0.0.0",   # listen to anyone
       0,           # find a free port and use it
       "nao.local",         # parent broker IP
       9559)       # parent broker port


    # Warning: HumanGreeter must be a global variable
    # The name given to the constructor must be the name of the
    # variable
    # First kill previous instance of HumanGreeter if needed.
    p = None
    try:
        p = ALProxy("HumanGreeter")
    except Exception, e:
        pass
    if p:
        p.exit() # kill previous instance

    SpeechRecognizer = speechRecognizerModule("SpeechRecognizer")
    HumanGreeter = HumanGreeterModule("HumanGreeter")
    tts = ALProxy("ALTextToSpeech")

    try:
        unlearnAllFaces()
        while True:
            tts.say("let's greet some people")
            HumanGreeter.startFaceDetection()
            face = ""
            while True:
                face = HumanGreeter.getFace();
                if face != "":
                    break
                time.sleep(0.5)
                
            if face == "unknown":
                tts.say("what is your name?")
                SpeechRecognizer.startListening()
                startTime = int(time.time())
                name = ""
                while True:
                    if int(time.time()) - startTime > 5:
                        # Timeout.
                        SpeechRecognizer.stopListening()
                        break
                    name = SpeechRecognizer.getWord()
                    if name != "":
                        break
                    time.sleep(0.5)

                if name != "":
                    tts.say("nice to meet you, " + name + ",please keep still for a moment")
                    print "going to learn face"
                    learnFace(name)
                    print "ready to learn face"
                    tts.say("thank you, I will remember you!")
            else:
                tts.say("hi again," + face)

    except Exception, e:
        print str(e)
        myBroker.shutdown()
        sys.exit(0)


if __name__ == "__main__":
    main()