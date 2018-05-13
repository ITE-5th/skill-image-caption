class Message:
    pass


class ImageMessage(Message):
    def __init__(self, image):
        self.image = image
