import json
import socket
from os.path import join, dirname, exists

from adapt.intent import IntentBuilder
from mycroft import MycroftSkill, intent_handler
from mycroft.util.log import LOG

from misc.connection_helper import ConnectionHelper
from misc.order_message.close_message import CloseMessage
from misc.order_message.image_to_text_message import ImageToTextMessage

try:
    from camera import Camera
except ImportError:
    # re-install yourself
    from py_msm import MycroftSkillsManager

    msm = MycroftSkillsManager()
    msm.install_by_url("https://github.com/ITE-5th/skill-image-caption", True)
    # trigger reload
    msm.reload_skill("skill-image-caption")

IMAGE_CAPTIONING_PORT = 9001


class ImageCaptionSkill(MycroftSkill):
    def __init__(self):
        super(ImageCaptionSkill, self).__init__("ImageCaptionSkill")
        # MycroftSkill.__init__("ImageCaptionSkill")
        if "model" not in self.settings:
            self.settings["model"] = "vgg"
        if "server_url" not in self.settings:
            self.settings["server_url"] = "192.168.1.7"

        create_settings_meta()

        LOG.info("Image Captioning Skill started")

        self.camera = Camera(width=800, height=600)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.port = IMAGE_CAPTIONING_PORT
        self.host = self.settings["server_url"]

        self.socket.connect((self.host, self.port))
        LOG.info(f'connected to server {self.host } : {str(self.port)} ')

    @intent_handler(IntentBuilder("correct_name").require('ImageCaption'))
    def handle_image_caption(self, message):

        image, _ = self.camera.take_image()
        if image is None:
            return

        order_message = ImageToTextMessage(image)
        ConnectionHelper.send_pickle(self.socket, order_message)
        response = ConnectionHelper.receive_json(self.socket)
        print(message)
        self.speak_dialog('image.caption', response)

    def shutdown(self):
        super(ImageCaptionSkill, self).shutdown()
        LOG.info("Image Captioning Skill CLOSED")
        ConnectionHelper.send_pickle(self.socket, CloseMessage())
        print('closing socket')
        self.socket.close()

        self.camera.close()


def create_skill():
    return ImageCaptionSkill()


def create_settings_meta():
    meta = {
        "name": "Image Captioning Skill",
        "skillMetadata": {
            "sections": [
                {
                    "name": "Model",
                    "fields":
                        [
                            {
                                "name": "model",
                                "type": "select",
                                "label": "Options",
                                "options": "vgg|resnet",
                                "value": "vgg"
                            },
                            {
                                "name": "server_url",
                                "type": "text",
                                "label": "Remote Server URL:",
                                "value": ""
                            }
                        ]
                }
            ]
        }
    }
    meta_path = join(dirname(__file__), 'settingsmeta.json')
    if not exists(meta_path):
        with open(meta_path, 'w') as fp:
            json.dump(meta, fp)
