import requests
import re
import logging
import settings
from decouple import config
from pymongo import MongoClient
from bs4 import BeautifulSoup
from utils import get_all_publications

def start_crawl(session, collection, email, password):
    logging.getLogger().setLevel(logging.INFO)

    response = session.post('https://m.facebook.com/login.php', data={
        'email': facebook_email,
        'pass': facebook_password
    }, allow_redirects=False)

    logging.debug("User logged in.")

    page = session.get('https://m.facebook.com/home.php')
    parser = BeautifulSoup(page.content, 'html.parser')
    print(parser)

    perfil_link = parser.find('a', text='Perfil')
    perfil_page = session.get("https://m.facebook.com{0}".format(perfil_link.get('href')))
    perfil_parser = BeautifulSoup(perfil_page.content, 'html.parser')
    logging.info("Entering in the user perfil page.")

    get_all_publications(session, collection, perfil_parser)

if __name__ == '__main__':
    facebook_session = requests.session()

    facebook_session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux i686; rv:39.0) Gecko/20100101 Firefox/39.0'
    })

    facebook_email = config('FACEBOOK_EMAIL', default=False) 
    facebook_password = config('FACEBOOK_PASSWORD', default=False)

    conn = MongoClient('localhost', 27017)

    db = conn['facebook_reactions_database']

    timeline = db['timeline']

    start_crawl(
        facebook_session,
        timeline,
        facebook_email,
        facebook_password,
    )
