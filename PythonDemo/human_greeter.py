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
        vocabulary = ["yes", "no", "please"]
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
            # Unsubscribe to the event to avoid repetitions
            memorySpeech.unsubscribeToEvent("WordRecognized", "SpeechRecognizer")
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
        self.previousTimeStampInSeconds = 0
        self.face = ""
    
    def startFaceDetection(self):
        global memorySpeech
        # Subscribe to the WordRecognized event:
        try:
            memoryFace.subscribeToEvent("FaceDetected", "HumanGreeter", "onFaceDetected")
        except Exception, e:
            pass

    def stopFaceDetection(self):
        global memorySpeech
        # Subscribe to the WordRecognized event:
        try:
            memoryFace.unsubscribeToEvent("FaceDetected", "HumanGreeter")
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
        global memoryFace, timeStampInSeconds
        val = memoryFace.getData("FaceDetected")
        if(val and isinstance(val, list) and len(val) >= 2):
            # We detected faces !
            # For each face, we can read its shape info and ID.
            # First Field = TimeStamp.
            # Second Field = array of face_Info's.
            faceInfoArray = val[1]
            try:
                faceInfo = faceInfoArray[0]
                # First Field = Shape info.
                faceShapeInfo = faceInfo[0]
                # Second Field = Extra info (empty for now).
                faceExtraInfo = faceInfo[1]
                print "face detected!, confidence = " + str(faceExtraInfo[1])
                if faceExtraInfo[1] > 0.5:
                    timeStampInSeconds = val[0][0]
                    if timeStampInSeconds - self.previousTimeStampInSeconds < 3:
                        return
                    # Unsubscribe to the event to avoid repetitions
                    memoryFace.unsubscribeToEvent("FaceDetected", "HumanGreeter")
                    self.previousTimeStampInSeconds = timeStampInSeconds
                    self.face = faceExtraInfo[2]
            except Exception, e:
                print str(e)


def learnFace(face):
    # Create a proxy to ALFaceDetection
    try:
      faceProxy = ALProxy("ALFaceDetection")
      # First forget face to be enable to learn it again.
      faceProxy.forgetPerson(face)
      faceProxy.learnFace(face)
    except Exception, e:
      print str(e)
      exit(1)


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

    print "going to learn face"
    learnFace("rene")
    print "ready to learn face"

    HumanGreeter = HumanGreeterModule("HumanGreeter")
    tts = ALProxy("ALTextToSpeech")

    try:
        SpeechRecognizer.startListening()
        HumanGreeter.startFaceDetection()
        while True:
            word = SpeechRecognizer.getWord()
            if word != "":
                tts.say("you said, " + word)
                print "word recognized!", word
                time.sleep(2)
                SpeechRecognizer.startListening()
            face = HumanGreeter.getFace();
            if face != "":
                tts.say("Hello, " + face)
                print "face recognized!", face
                time.sleep(2)
                HumanGreeter.startFaceDetection()
            time.sleep(0.5)
    except Exception, e:
        print str(e)
        myBroker.shutdown()
        sys.exit(0)


if __name__ == "__main__":
    main()