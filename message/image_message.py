from message.message import AMessage


class ImageMessage(AMessage):
    def __init__(self, image):
        self.image = image
