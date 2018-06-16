import logging

def login_required(method):

    def check(self, *args):
        if self.is_logged_in:
            return method(self, *args)
        else:
            logging.warn("YOU MUST SIGN ON FACEBOOK.")

    return check
