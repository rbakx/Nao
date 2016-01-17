# -*- encoding: UTF-8 -*-
""" Say 'hello, you' each time a human face is detected

"""

from naoqi import ALProxy
from naoqi import ALBroker
from naoqi import ALModule


# Global variables. Module names must be global otherwise the callback functions will report for example:
# 'python object not found FaceDetector'.
SetVolume = None


class SetVolumeModule(ALModule):
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
            self.memory.unsubscribeToEvent("FrontTactilTouched", "SetVolume")
            self.memory.unsubscribeToEvent("RearTactilTouched", "SetVolume")
        except Exception, e:
            pass
        self.memory.subscribeToEvent("FrontTactilTouched", "SetVolume", "onFrontTouched")
        self.memory.subscribeToEvent("RearTactilTouched", "SetVolume", "onRearTouched")
        self.audiodevice = ALProxy("ALAudioDevice")
        self.tts = ALProxy("ALTextToSpeech")

    def onFrontTouched(self, strVarName, value):
        # Only react on touch down event.
        if value == 1.0:
            self.audiodevice.setOutputVolume(min(100, self.audiodevice.getOutputVolume() + 10.0))
            self.tts.say("volume up")
    
    def onRearTouched(self, strVarName, value):
        # Only react on touch down event.
        if value == 1.0:
            self.audiodevice.setOutputVolume(max(0, self.audiodevice.getOutputVolume() - 10.0))
            self.tts.say("volume down")


# Remove this dummy GeneratedClass() when running in Choregraphe.
class GeneratedClass():
    def __init__(self):
        pass


class MyClass(GeneratedClass):
    def __init__(self):
        global SetVolume
        GeneratedClass.__init__(self)
        # Warning: module names must be global variables.
        # The name given to the constructor must be the name of the variable.
        SetVolume = SetVolumeModule("SetVolume")

    def onLoad(self):
        #put initialization code here
        pass
        
    def onUnload(self):
        # Put clean-up code here.
        # This method will be called when the onInput_onStart() thread ends or when the behavior is stopped.
        # The behavior can be stopped in Choregraphe using the red 'Stop' button, or by using the 'Run Behavior'
        # box and activating the 'onStop' input. In Python this means the ALBehaviorManager method stopBehavior() is called.
        # Important to call exit on the modules created, otherwise the next time ALModule.__init__(self, name)
        # will fail because the modules are already registered!
        # Use try...except here in case the (one of the) modules have already exitted.
        try:
            SetVolume.exit()
        except Exception, e:
            pass
    
    def onInput_onStart(self):
        pass

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
    # onStart() only installs the callback() function so  wait here for events to occur and being handled.
    import time
    while True:
        time.sleep(1.0)
    myClass.onUnload()


if __name__ == "__main__":
    main()
