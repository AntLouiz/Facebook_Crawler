import time
import json
from decouple import config
from bs4 import BeautifulSoup
from selenium.common.exceptions import NoSuchElementException
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

email = config('FACEBOOK_EMAIL')
password = config('FACEBOOK_PASSWORD')
driver = webdriver.Firefox()
data = {}

driver.get("http://m.facebook.com/")
print("Connected with facebook")
time.sleep(2)

email_field = driver.find_element_by_name('email')
email_field.clear()
email_field.send_keys(email)
print("Email inserted")
    
pass_field = driver.find_element_by_name('pass') 
pass_field.clear()
pass_field.send_keys(password)
print("Password inserted")
    
login_button = driver.find_element_by_name('login')
login_button.click()
print("Button login clicked.")
time.sleep(2)

ok_button = driver.find_element_by_xpath('//input[@value="OK"]').click()
print("Ok pressed in Entry on touch page.")
time.sleep(2)
    
perfil = driver.find_element_by_link_text('Perfil').click()
print("Entry on Perfil.")
time.sleep(2)

year = driver.find_element_by_link_text('2017').click()
time.sleep(4)

more = driver.find_element_by_link_text('Mostrar mais')

while more:
    pubs = BeautifulSoup(driver.page_source, 'html.parser')
    try:
        main_window = driver.current_window_handle
        
        for pub in pubs.find_all('a', text='Curtir'):
            reaction_link = pub.find_previous_sibling('a').get('href')

            driver.execute_script('window.open("{0}");'.format(reaction_link))
            time.sleep(4)
            driver.switch_to_window(driver.window_handles[1])
            time.sleep(4)
            pub_date = driver.find_element_by_xpath('//abbr[1]').text

            data[pub_date] = {}

            driver.find_element_by_xpath('//div[@id="add_comment_switcher_placeholder"]/following-sibling::div/a').click()
            time.sleep(4)

            try:
                see_more = driver.find_element_by_link_text('Ver mais')
            except:
                see_more = 0
            finally:
                reactions = BeautifulSoup(driver.page_source, 'html.parser').find_all('li')

            if see_more:
                reactions = reactions[:len(reactions)-1]

            for reaction in reactions:
                reaction = reaction.find_all('img')[:2]
                user_name = reaction[0].get('alt')
                user_reaction = reaction[1].get('alt')

                try:
                    data[pub_date][user_reaction].append(user_name)
                except:
                    data[pub_date][user_reaction] = []
                    data[pub_date][user_reaction].append(user_name)
            driver.close()
            driver.switch_to_window(main_window)
    except:
        time.sleep(4)
        #the publication does have any reactions
        pass
    try:
        more = driver.find_element_by_link_text('Mostrar mais')
        more.click()
        time.sleep(2)
    except:
        more = 0
driver.close()

with open('facebook_data.json', 'w') as fb_data:
    json.dump(data, fb_data)

