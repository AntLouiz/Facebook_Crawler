import logging

def login_required(method):

    def check(self, *args):
        if self.logged:
            return method(self, *args)
        else:
            logging.warn("YOU MUST SIGN ON FACEBOOK.")

    return check