from adapt.intent import IntentBuilder
from mycroft import MycroftSkill, intent_handler


class ImageCaptionSkill(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)

    @intent_handler(IntentBuilder().require('ImageCaption'))
    def handle_image_caption(self, message):
        self.speak_dialog('image.caption')


def create_skill():
    return ImageCaptionSkill()

