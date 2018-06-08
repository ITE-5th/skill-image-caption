# File Path Manager
# import os
# sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import socket
import sys
import traceback

from adapt.intent import IntentBuilder
from mycroft import MycroftSkill, intent_handler
from mycroft.util.log import LOG

# TODO: Make sure "." before module name is not missing
from .code.message.image_to_text_message import ImageToTextMessage
from .code.misc.camera import Camera
from .code.misc.receiver import Receiver
from .code.misc.sender import Sender

LOG.warning('Running Skill Image Captioning On Python ' + sys.version)

try:
    import picamera
except ImportError:
    # re-install yourself
    from msm import MycroftSkillsManager

    msm = MycroftSkillsManager()
    msm.install("https://github.com/ITE-5th/skill-image-caption")

IMAGE_CAPTIONING_PORT = 8888


class ImageCaptionSkill(MycroftSkill):
    def __init__(self):
        super(ImageCaptionSkill, self).__init__("ImageCaptionSkill")
        LOG.warning('Running Skill Image Captioning ')

        if "model" not in self.settings:
            self.settings["model"] = "vgg"
        if "server_url" not in self.settings:
            self.settings["server_url"] = "192.168.43.243"
        # TODO resize image according to specific network

        self.socket = None
        self.receiver = None
        self.sender = None
        self.port = None
        self.host = None
        self.camera = Camera(width=800, height=600)
        self.connect()

    def connect(self):
        try:
            self.port = IMAGE_CAPTIONING_PORT
            self.host = self.settings.get("server_url", "192.168.43.243")
            LOG.info("Image Captioning Skill started " + self.host + ":" + str(self.port))
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.receiver = Receiver(self.socket, json=True)
            self.sender = Sender(self.socket, json=True)
            LOG.info('connected to server:' + self.host + ' : ' + str(self.port))
        except Exception as e:
            LOG.warning(str(e))

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
                    retries -= 1
                    self.sender.send(msg)
                    break
                except Exception as e:
                    if retries <= 0:
                        LOG.warning('Cannot Connect')
                        self.speak('Cannot Connect')
                        return
                    self.connect()
                    LOG.warning(str(e))

            result = self.receiver.receive()
            LOG.info(message)
            self.speak_dialog("result", result)

        except Exception as e:
            LOG.info('Something is wrong')
            LOG.info(str(e))
            LOG.info(str(traceback.format_exc()))
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
