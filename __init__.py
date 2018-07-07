# File Path Manager
# import os
# sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import socket
import sys
import traceback

from adapt.intent import IntentBuilder
from mycroft import MycroftSkill, intent_handler
from mycroft.util.log import LOG

from .code.message.image_to_text_message import ImageToTextMessage
from .code.misc.camera import Camera
from .code.misc.receiver import Receiver
from .code.misc.sender import Sender
from .default_config import DefaultConfig

# TODO: Make sure "." before module name is not missing

LOG.warning('Running Skill Image Captioning On Python ' + sys.version)

try:
    import picamera
except ImportError:
    # re-install yourself
    from msm import MycroftSkillsManager

    msm = MycroftSkillsManager()
    msm.install("https://github.com/ITE-5th/skill-image-caption")


class ImageCaptionSkill(MycroftSkill):
    def __init__(self):
        super(ImageCaptionSkill, self).__init__("ImageCaptionSkill")
        LOG.warning('Running Skill Image Captioning ')

        # if "server_url" not in self.settings:
        #     self.settings["server_url"] = "192.168.43.243"
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
            self.port = DefaultConfig.IMAGE_CAPTIONING_PORT
            self.host = self.settings.get("server_url", DefaultConfig.server_url)
            LOG.info("Image Captioning Skill started " + self.host + ":" + str(self.port))
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.receiver = Receiver(self.socket, json=True)
            self.sender = Sender(self.socket, json=True)
            LOG.info('connected to server:' + self.host + ' : ' + str(self.port))
        except Exception as e:
            LOG.warning(str(e))

    def ensure_send(self, msg):
        retries = 3
        while retries > 0:
            try:
                retries -= 1
                self.sender.send(msg)
                break
            except Exception as e:
                if retries <= 0:
                    LOG.warning('Cannot Connect')
                    return False
                self.connect()
                LOG.warning(str(e))
        return True

    @intent_handler(IntentBuilder("CaptionIntent").require('ImageCaption'))
    def caption(self, message):
        # LOG.info('Handling ' + message)
        try:
            self.speak_dialog('Start')
            image, _ = self.camera.take_image()

            msg = ImageToTextMessage(image)
            sent = self.ensure_send(msg)
            if not sent:
                self.speak_dialog('ConnectionError')
                return False

            result = self.receiver.receive()
            LOG.info(result)
            self.speak_dialog("Result", result)

        except Exception as e:
            LOG.info('Something is wrong')
            LOG.info(str(e))
            LOG.info(str(traceback.format_exc()))
            self.speak_dialog("UnknownError")
            self.connect()
            return False
        return True

    def stop(self):
        super(ImageCaptionSkill, self).shutdown()
        LOG.info("Image Captioning Skill CLOSED")
        self.socket.close()


def create_skill():
    return ImageCaptionSkill()
