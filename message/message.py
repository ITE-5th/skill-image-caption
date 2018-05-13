class Message:
    pass


class ImageMessage(Message):
    def __init__(self, image):
        self.image = image


class ImageToTextMessage(ImageMessage):
    pass


class CloseMessage(Message):
    def __init__(self):
        pass
