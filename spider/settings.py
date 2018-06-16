from decouple import config

USER_AGENT = {
	'User-Agent': 'Mozilla/5.0 (X11; Linux i686; rv:39.0) Gecko/20100101 Firefox/39.0'
}

DB_NAME = config('DB_NAME', default='mydb')

FACEBOOK_EMAIL = config('FACEBOOK_EMAIL')
FACEBOOK_PASSWORD = config('FACEBOOK_PASSWORD')
FACEBOOK_CREDENTIALS = (FACEBOOK_EMAIL, FACEBOOK_PASSWORD)
