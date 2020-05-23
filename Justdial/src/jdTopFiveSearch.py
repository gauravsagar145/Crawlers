import os
import json
import time
from tqdm import tqdm
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def get_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.113 Safari/537.36")
    driver = webdriver.Chrome(os.path.abspath(
        '../../driver/chromedriver'), options=options)
    return driver


def load_json_file(filename):
    try:
        with open(filename, 'r') as f:
            distros_dict = json.load(f)
    except Exception as e:
        print('Error occured while reading the file : {0} as {1}'.format(
            filename, e))

    return distros_dict


def getTopFiveSearchResult_method1(row, finalOutput):
    # Get Driver and hit url
    try:
        driver = get_driver()
        url = "https://www.justdial.com/" + \
            row.get('primary_city') + "/search?q=" + row.get('name')
        driver.get(url)
    except Exception as e:
        print('An exception occured : {0}'.format(e))
        return

    # Get Basic Info
    try:
        name = driver.find_elements_by_xpath(
            '//div[1]/section/div[1]/h2/span/a/span[@class="lng_cont_name"]')
        completeAddress = driver.find_elements_by_xpath(
            '//*[@class="mrehover dn"]/span[@class = "cont_fl_addr"]')
        restUrls = driver.find_elements_by_xpath(
            '//div[1]/section/div[1]/h2/span[@class="jcn"]/a')
    except Exception as e:
        print('Error geting basic details : {0} '.format(e))
        return

    try:
        # Process top Five
        if len(name) > 5:
            topFive = 5
        else:
            topFive = len(name)

        tempList = list()
        for i in range(0, topFive):
            tempyDict = {}
            tempyDict['requestId'] = row.get('requestId')
            tempyDict['Name'] = name[i].text
            tempyDict['Address'] = completeAddress[i].get_attribute(
                'innerHTML')
            tempyDict['URL'] = restUrls[i].get_attribute('href')

            tempList.append(tempyDict)

        finalOutput[row.get('requestId')] = tempList
    except Exception as e:
        print('An exception occured while processing info : {0}'.format(e))
        return
    finally:
        driver.quit()
        return finalOutput

def main():
    finalOutput = {}
    try:
        # Load data to be searched
        fileName = os.path.abspath('./finalOfferDB.json')

        data = load_json_file(fileName)
        
        # startIndex and endingIndex to be replaced accordingly
        startIndex = 0
        endingIndex = 1

        for row in tqdm(data[startIndex:endingIndex]):
            getTopFiveSearchResult_method1(row, finalOutput)
    except Exception as e:
        print('Uncaught Error in main : {0}'.format(e))
        return
    finally:
        jsonData = json.dumps(finalOutput, ensure_ascii=False)

        #it will override the previous file content
        f = open('output.json', 'w')
        f.write(jsonData)
        f.close()
        # TO_DO : will update the logic to read previous data and append list later.

        print('Completed the fetch from {0} to {1} !!'.format(startIndex,endingIndex))


if __name__ == "__main__":
    main()
