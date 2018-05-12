try:
    import cPickle as pickle
except:
    import pickle

import socket
from os.path import join, dirname, exists

from adapt.intent import IntentBuilder
from mycroft import MycroftSkill, intent_handler
from mycroft.util.log import LOG

try:
    import picamera
except ImportError:
    # re-install yourself
    from msm import MycroftSkillsManager

    msm = MycroftSkillsManager()
    msm.install_by_url("https://github.com/ITE-5th/skill-image-caption", True)
    # trigger reload
    msm.reload_skill("skill-image-caption")

IMAGE_CAPTIONING_PORT = 9001

LOG.warning('Running Skill Image Captioning 1')


class ImageCaptionSkill(MycroftSkill):
    def __init__(self):
        super(ImageCaptionSkill, self).__init__("ImageCaptionSkill")
        # MycroftSkill.__init__("ImageCaptionSkill")
        LOG.warning('Running Skill Image Captioning ')

        if "model" not in self.settings:
            self.settings["model"] = "vgg"
        if "server_url" not in self.settings:
            self.settings["server_url"] = "192.168.1.7"

        create_settings_meta()

        LOG.info("Image Captioning Skill started")
        # TODO resize image according to specific network
        self.camera = Camera(width=800, height=600)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.port = IMAGE_CAPTIONING_PORT
        self.host = self.settings["server_url"]

        self.socket.connect((self.host, self.port))
        LOG.info('connected to server:' + self.host + ' : ' + {str(self.port)})

    @intent_handler(IntentBuilder("CaptionIntent").require('ImageCaption'))
    def handle_image_caption(self, message):
        LOG.info('Handling ' + message)

        image, _ = self.camera.take_image()
        if image is None:
            return False

        order_message = ImageToTextMessage(image)
        ConnectionHelper.send_pickle(self.socket, order_message)
        response = ConnectionHelper.receive_json(self.socket)
        print(message)
        self.speak_dialog('image.caption', response)
        return True

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


# Connection Helper
import json

LOG.warning('Running Skill Image Captioning 2')


class ConnectionHelper:

    @staticmethod
    def send_json(socket, data):
        try:
            serialized = json.dumps(data)
        except (TypeError, ValueError) as e:
            raise Exception('You can only send JSON-serializable data')
        # send the length of the serialized data first
        socket.send('%d\n'.encode() % len(serialized))
        # send the serialized data
        socket.sendall(serialized.encode())

    @staticmethod
    def receive_json(socket):
        view = ConnectionHelper.receive(socket).decode()
        try:
            deserialized = json.loads(view)
        except (TypeError, ValueError) as e:
            raise Exception('Data received was not in JSON format')
        return deserialized

    @staticmethod
    def send_pickle(socket, object):
        try:
            serialized = pickle.dumps(object)
        except (TypeError, ValueError) as e:
            raise Exception('You can only send JSON-serializable data')
        # send the length of the serialized data first
        socket.send('%d\n'.encode() % len(serialized))
        # send the serialized data
        socket.sendall(serialized)

    @staticmethod
    def receive_pickle(socket):
        view = ConnectionHelper.receive(socket)
        try:
            deserialized = pickle.loads(view)
        except (TypeError, ValueError) as e:
            raise Exception('Data received was not in JSON format')
        return deserialized

    @staticmethod
    def receive(socket):
        # read the length of the data, letter by letter until we reach EOL
        length_str = ''
        char = socket.recv(1).decode()
        if char == '':
            return char
        while char != '\n':
            length_str += char
            char = socket.recv(1).decode()
        total = int(length_str)
        # use a memoryview to receive the data chunk by chunk efficiently
        view = memoryview(bytearray(total))
        next_offset = 0
        while total - next_offset > 0:
            recv_size = socket.recv_into(view[next_offset:], total - next_offset)
            next_offset += recv_size
        view = view.tobytes()
        return view


# Message Classes


class Message:
    pass


class CloseMessage(Message):
    pass


class ImageMessage(Message):
    def __init__(self, image):
        self.image = image


class ImageToTextMessage(ImageMessage):
    pass


# Camera

import base64

LOG.warning('Running Skill Image Captioning 3')
import time

LOG.warning('Running Skill Image Captioning 4')

pi_camera = picamera.PiCamera()


class Camera:

    def __init__(self, width=800, height=600, vflip=True, hflip=True):
        self.camera = pi_camera
        self.camera.vflip = vflip
        self.camera.hflip = hflip
        self.camera.resolution = (width, height)

    def take_image(self, face_count=0):
        import os
        temp_dir = './temp/'
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        file_name = temp_dir + time.strftime("%Y%m%d-%H%M%S") + '.jpg'

        self.camera.capture(file_name)
        with open(file_name, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        if face_count > 0:
            return encoded_string, file_name if self.check_faces(file_name=file_name, faces_count=face_count) else -1
        # with open("../Image.jpg", "rb") as image_file:
        #     encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        return encoded_string, file_name

    def check_faces(self, file_name='./temp/Image.jpg', faces_count=1):
        import dlib
        from skimage import io
        print('analysing faces count')
        detector = dlib.get_frontal_face_detector()
        image = io.imread(file_name)
        rects = detector(image, 1)
        has_one_face = len(rects) == faces_count
        print(has_one_face)
        return has_one_face

    def close(self):
        self.camera.close()
