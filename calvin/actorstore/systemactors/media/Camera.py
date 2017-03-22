from calvin.actor.actor import Actor, manage, condition, stateguard


class Camera(Actor):

    """
    When input trigger goes high fetch image from given device.

    Inputs:
      trigger: binary input
    Outputs:
      image: generated image
    """

    @manage(['device', 'width', 'height', 'trigger'])
    def init(self, device=0, width=640, height=480):
        self.device = device
        self.width = width
        self.height = height
        self.trigger = None
        self.setup()

    def setup(self):
        self.use("calvinsys.media.camerahandler", shorthand="camera")
        self.use("calvinsys.media.image", shorthand="image")
        self.use('calvinsys.native.python-base64', shorthand="base64")

        self.camera = self["camera"].open(self.device, self.width, self.height)

    def did_migrate(self):
        self.setup()

    def will_end(self):
        self.camera.close()

    def will_migrate(self):
        self.camera.close()

    @stateguard(lambda self: self.trigger is True)
    @condition(action_output=['image'])
    def get_image(self):
        self.trigger = None
        img = self.camera.get_image()
        result = self['base64'].b64encode(img)

        return (result, )

    @stateguard(lambda self: self.trigger is None)
    @condition(action_input=['trigger'])
    def trigger_action(self, trigger):
        self.trigger = True if trigger else None

    action_priority = (get_image, trigger_action)
    requires = ['calvinsys.media.image', 'calvinsys.native.python-base64', 'calvinsys.media.camerahandler']
