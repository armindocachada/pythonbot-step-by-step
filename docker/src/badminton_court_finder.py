# import external libraries.
from selenium import webdriver as wd
from selenium.webdriver.chrome.options import Options
from pyvirtualdisplay import Display





############################################################
from bs4 import BeautifulSoup
from selenium.webdriver.common.keys import Keys
import datetime
from datetime import date
import time
import json
import pandas as pd

def startBooking(driver):
    bookNowButton = driver.find_element_by_xpath("/html/body/div/div[2]/div/landing-page-base/div/div/div[2]/landing-page-bookings-base/div/div[2]/account-booking-actions/div/div/div/a")
    bookNowButton.click()
    
def selectClub(club, driver):
    driver.find_element_by_class_name("select2-selection__choice__remove").click()
    
    select_site = driver.find_element_by_xpath("//span[contains(@class, 'select2-selection')]")
    is_expanded = select_site.get_attribute("aria-expanded") == 'true'
    print(is_expanded)
    driver.find_element_by_xpath(f"//li[text()='{club}']").click()
    
    if not is_expanded:
        print("About to open dropdown")
        wd.find_element_by_xpath("//span[@class='selection']").click()

        
def selectBadminton(driver):
    driver.find_element_by_xpath('//input[@type="radio" and @data-test-id="bookings-category-categories-racket-sports"]').click()
    driver.find_element_by_xpath('//input[@type="checkbox" and @data-test-id="bookings-activities-activity-badminton-60-mins"]').click()
    driver.find_element_by_xpath('//button[@data-test-id="bookings-viewtimetable"]').click()
    
def loginToSportsCenterWebsite():
    print('building session')

    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    driver = wd.Chrome(options=chrome_options)
    driver.implicitly_wait(10)
    driver.set_window_size(1500, 1000)
    
    driver.get("https://legacyleisure.legendonlineservices.co.uk/crook_log/account/login")
    credentials = dict(line.strip().split('=') for line in open('leisure_centre.properties'))
    email_address = driver.find_element_by_xpath('//*[@id="account-login-email"]')
    email_address.send_keys(credentials["username"])
    
    password = driver.find_element_by_xpath('//*[@id="account-login-password"]')
    password.send_keys(credentials["password"])
    
    submitLoginButton = driver.find_element_by_xpath('//span[@id="account-login-submit-message"]/ancestor::button')
    submitLoginButton.click()
    return driver

# Using Dataframe.apply() to apply function to every row
def calculate_max_duration(row, all_available_times):
    startTime = row["Time"]
    duration = 1
    previousTime = startTime
    while True:
        nextTime = previousTime + datetime.timedelta(hours=1)         
        indices = all_available_times["Time"] == nextTime
        if not all_available_times.loc[indices].empty:
           duration+=1
           previousTime = nextTime
        else:
           break
        
    return duration
        

def getAvailabilityForDate(queryDate, driver):
    queryDateStr = queryDate.strftime("%d %b %Y")
    # find date picker
    datePicker = driver.find_element_by_xpath("//span[@class='Zebra_DatePicker_Icon_Wrapper']/input")
    datePicker.clear()
    # set date
    datePicker.send_keys(queryDateStr)
    datePicker.send_keys(Keys.TAB);
    # we need to wait because otherwise we pick an empty list of results
    # there are different techniques to ensure that we have a fresh list of results
    # for instance we could wait for a cer
    current_date = datePicker.get_attribute('value')
    time.sleep(3)
    soup = BeautifulSoup(driver.page_source)
    activity_rows = soup.findAll("div", {"class": "activityBox"})
    df_rows = []
    for activity_row in activity_rows:
        location = activity_row.find("div", {"class": "activityDetailsMajor"})
        timeOfDay= activity_row.find("div", {"class": "timeOfDay"})
        available = activity_row.find("div", {"class": "spaceDetailsText"})
        df_rows.append([current_date,location.text, timeOfDay.text, available.text])

    df = pd.DataFrame(df_rows, columns=["Date", "Location", "Time", "Availability"])
    # complicated version with regex
    df["Availability"].str.replace(r"(\d+) Slots", lambda m: m.group(1))
    # simple version
    df["Availability"] = df["Availability"].str.replace(" Slots", "").replace("Full", "0")
    df['Availability'] = pd.to_numeric(df['Availability'])
    df['Time'] = pd.to_datetime(df["Date"] + " " + df["Time"], format="%d %b %Y %H:%M")

    return df


def selectHome(driver):
    driver.find_element_by_xpath("//*[@id='lgd-navigation-menu-options']/li[1]/a/span[2]").click()


def findAvailableSlots(clubs, earliestDate=date.today(), numberOfDaysInFuture=1, earliestTime="8:00", latestTime="21:00", numberOfHours=1, slots=1):
    ''' Finds slots available using the given search criteria:
    club: the name of the club for which we want to search for availability
    earliestDate: the earliest date for which we want to look for available slots. If not specified, it defaults to today.
    numberOfDaysInTheFuture: 
    earliestTime: the earliest time for which we are searching for slots
    latestTime: the latest time for which we are searching for slots
    numberOfHours: How long we want to play for
    slots: How many Slots?
    '''
    ############################################################
    # set xvfb display since there is no GUI in docker container.
    display = Display(visible=0, size=(2500, 2500))
    display.start()

    # login
    driver = loginToSportsCenterWebsite()
    df_clubs_list = []
    json_result = {}
    # try:
    for club in clubs:
    
        startBooking(driver)
        selectClub(club, driver)
        selectBadminton(driver)
        startDate = earliestDate

        dframes= []
        for n in range(numberOfDaysInFuture+1):
            df = getAvailabilityForDate(startDate + datetime.timedelta(days=n), driver)
            # filter by number of slots
            df = df[df["Availability"] > slots]
            # filter by time range
            index = pd.DatetimeIndex(df['Time'])
            df = df.iloc[index.indexer_between_time(earliestTime, latestTime)]
            # # filter by desired duration
            dframes.append(df)
            # go back to home so we can search for availability in next club
        
        
        selectHome(driver)
        
        df_club = pd.concat(dframes)
        df_club["Max Duration"] = df_club.apply(lambda x:calculate_max_duration(x,df_club), axis=1)
        df_club = df_club[df_club["Max Duration"] >= numberOfHours]

        df_clubs_list.append(df_club)
        
    
    df_clubs = pd.concat(df_clubs_list)
    json_result = df_clubs.to_json(orient="records", date_format="iso")
    
    driver.close()
    driver.quit()
    display.stop()
    # finally:
    #     driver.save_screenshot("/screenshot/screenshot.png")

    return json_result

if __name__ == "__main__":
    json_result = findAvailableSlots("Erith", numberOfDaysInFuture=5, slots=1, earliestTime="19:00", latestTime="21:00", numberOfHours=2 )  

    json_formatted_str = json.dumps(json.loads(json_result), indent=4)
    print(json_formatted_str)






