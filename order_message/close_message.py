from multipledispatch import dispatch

from server.message.message import Message
from server.message.register_face_recognition_message import RegisterFaceRecognitionMessage
from server.message.start_face_recognition_message import StartFaceRecognitionMessage


class CloseMessage(Message):
    pass


