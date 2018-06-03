# File Path Manager
# import os
# import sys
# sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import socket

from adapt.intent import IntentBuilder
from mycroft import MycroftSkill, intent_handler
from mycroft.util.log import LOG

# TODO: Make sure "." before module name is not missing
from .code.misc.receiver import Receiver
from .code.misc.sender import Sender
from .code.message.image_to_text_message import ImageToTextMessage
from .code.misc.camera import Camera

LOG.warning('Running Skill Image Captioning 0')

try:
    import picamera
except ImportError:
    # re-install yourself
    from msm import MycroftSkillsManager

    msm = MycroftSkillsManager()
    msm.install("https://github.com/ITE-5th/skill-image-caption")

IMAGE_CAPTIONING_PORT = 8888

LOG.warning('Running Skill Image Captioning 1')


class ImageCaptionSkill(MycroftSkill):
    def __init__(self):
        super(ImageCaptionSkill, self).__init__("ImageCaptionSkill")
        LOG.warning('Running Skill Image Captioning ')

        if "model" not in self.settings:
            self.settings["model"] = "vgg"
        if "server_url" not in self.settings:
            self.settings["server_url"] = "192.168.1.7"
        # TODO resize image according to specific network

        self.socket = None
        self.receiver = None
        self.sender = None
        self.camera = Camera(width=800, height=600)
        self.port = IMAGE_CAPTIONING_PORT
        self.host = self.settings["server_url"]
        LOG.info("Socket Skill started " + self.host + ":" + str(self.port))
        self.connect()

    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))
        self.receiver = Receiver(self.socket, json=True)
        self.sender = Sender(self.socket, json=True)

        LOG.info('connected to server:' + self.host + ' : ' + str(self.port))

    # @intent_file_handler('ImageCaption.voc')
    @intent_handler(IntentBuilder("CaptionIntent").require('ImageCaption'))
    def caption(self, message):
        # LOG.info('Handling ' + message)
        try:
            image, _ = self.camera.take_image()

            msg = ImageToTextMessage(image)
            retries = 3
            while retries > 0:
                try:
                    self.sender.send(self.socket, msg)
                    retries -= 1
                    break
                except Exception as e:
                    self.connect()
                    print(str(e))

            message = self.sender.send(self.socket)
            LOG.info(message)
            self.speak(message['result'])

        except Exception as e:
            LOG.info('Something is wrong')
            LOG.info(str(e))
            self.speak("Exception")
            self.connect()
            return False
        return True

    def stop(self):
        super(ImageCaptionSkill, self).shutdown()
        LOG.info("Image Captioning Skill CLOSED")
        self.socket.close()


def create_skill():
    return ImageCaptionSkill()
