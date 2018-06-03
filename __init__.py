# File Path Manager
# import os
# import sys
# sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import socket

from mycroft import MycroftSkill
from mycroft.util.log import LOG

# TODO: Make sure "." before module name is not missing
from .code.message.image_to_text_message import ImageToTextMessage
from .code.misc.camera import Camera
from .code.misc.connection_helper import ConnectionHelper

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

        LOG.info("Socket Skill started " + self.host + ":" + self.port)
        self.socket = None
        self.camera = Camera(width=800, height=600)
        self.port = IMAGE_CAPTIONING_PORT
        self.host = self.settings["server_url"]
        self.connect()

    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))
        LOG.info('connected to server:' + self.host + ' : ' + str(self.port))

    @intent_file_handler('caption.intent')
    def caption(self, message):
        LOG.info('Handling ' + message)
        try:
            image, _ = self.camera.take_image()

            msg = ImageToTextMessage(image)
            ConnectionHelper.send_json(self.socket, msg)
            message = ConnectionHelper.receive_json(self.socket)
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
