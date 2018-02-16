from Queue import Queue, Empty

class Mailbox(object):
    def __init__(self):
        self.mailbox = Queue()

    def send_mail_message(self, header, payload):
        self.mailbox.put((header, payload))

    def _get_mail_messages(self):
        messages = []
        while not self.mailbox.empty():
            try:
                messages.append(self.mailbox.get_nowait())
            except Empty:
                break

        return messages

    def _get_mail_message_blocking(self):
        return self.mailbox.get(True)
