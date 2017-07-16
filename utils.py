import time
from selenium.common.exceptions import NoSuchElementException
from selenium import webdriver

def get_user_url(email, password):
    driver = webdriver.PhantomJS(service_args=["--remote-debugger-port=9000"])
    driver.get("http://m.facebook.com/")
    time.sleep(3)
    
    print("Connected with facebook")
    
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
    print("Button login clicked")
    
    time.sleep(4)
    
    print("Entry on touch")
    
    ok_button = driver.find_element_by_xpath('//button[@value="OK"]').click()
    time.sleep(4)
    
    perfil = driver.find_element_by_xpath('//a/i[@class="img profpic"]').click()
    time.sleep(4)
    user_url = driver.current_url
    
    driver.close()
    return user_url
