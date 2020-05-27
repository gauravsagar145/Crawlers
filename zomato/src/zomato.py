import pickle
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tqdm import tqdm
from bs4 import BeautifulSoup
import datetime
import json
import os
from selenium.common.exceptions import NoSuchElementException


def fetch_all_urls(filename):
    file = open(filename, "rb")
    all_restro_urls_citywise_dict = pickle.load(file)

    # fetching all the urls
    all_urls = []
    for city in list(all_restro_urls_citywise_dict.keys()):
        all_urls.extend(all_restro_urls_citywise_dict.get(city))

    return all_urls


def get_date(string):
    if 'yesterday' in string:
        dt = datetime.datetime.now() - datetime.timedelta(days=int(1))
    elif 'day' in string:
        dt = datetime.datetime.now() - \
            datetime.timedelta(days=int(string.split()[0]))
    elif 'month' in string:
        if 'one' in string:
            dt = datetime.datetime.now() - datetime.timedelta(days=int(1)*30)
        else:
            dt = datetime.datetime.now() - \
                datetime.timedelta(days=int(string.split()[0])*30)
    elif 'year' in string:
        dt = datetime.datetime.now() - \
            datetime.timedelta(days=int(string.split()[0])*365)
    else:
        dt = datetime.datetime.strptime(string, '%b %d, %Y')
    year = dt.year
    month = dt.month
    day = dt.day
    date = str(day)+'-'+str(month)+'-'+str(year)
    return date


def get_driver(path):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.113 Safari/537.36")

    driver = webdriver.Chrome(executable_path=path, options=options)

    return driver


def fetch_zomato_info(url_list, chromeDriver_path, limit):
    try:
        output = list()
        driver = get_driver(chromeDriver_path)

        for url in tqdm(url_list):
            temp = {}
            driver.get(url)

            # get Restaurants name
            try:
                name = WebDriverWait(driver, 5).until(EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="root"]/main/div/section[3]/section/section[1]/h1'))).text
                # print(name)
            except Exception as e:
                name = "N/A"
                print(e)

            # Status
            status = ""
            try:
                status = WebDriverWait(driver, 10).until(EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="root"]/main/div/section[3]/section/section[1]/section[2]/span[1]'))).text
            except Exception as e:
                print(e)
                pass

            # Get latitude and longitude
            direction = {}
            try:
                dir = WebDriverWait(driver, 4).until(EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="root"]/main/div/section[3]/div[1]/section/a'))).get_attribute('href').split('=')
                # driver.find_element_by_xpath(
                #     '//*[@id="root"]/main/div/section[3]/div[1]/section/a').get_attribute('href').split('=')

                direction["latitude"] = dir[-1].split(',')[0]
                direction["longitude"] = dir[-1].split(',')[1]
            except Exception as e:
                print(e)
                pass

            # Contact Details
            all_contacts = {}
            try:
                contacts = driver.find_elements_by_xpath(
                    '//*[@id="root"]/main/div/section[4]/section/article/p[text()]')
                for i in range(len(contacts)):
                    all_contacts["Phone No. {0}".format(
                        i+1)] = contacts[i].text
            except Exception as e:
                print("No contact found")
                print(e)

            # Address
            address = ""
            try:
                address = WebDriverWait(driver,5).until(EC.presence_of_element_located((By.XPATH,'//*[@id="root"]/main/div/section[4]/section/article/section/p'))).text
            except Exception as e:
                print(e)
                address = ""
                pass

            # Get Online Order Status
            try:
                online_order_button = driver.find_element_by_link_text(
                    'Order Online').text
                if online_order_button:
                    oo_status = 'Yes'
                else:
                    oo_status = 'No'
            except:
                oo_status = 'No'

            # check table booking status
            try:
                table_booking_button = driver.find_element_by_link_text(
                    'Book a Table').text
                if table_booking_button:
                    book_table = 'Yes'
                else:
                    book_table = 'No'
            except:
                book_table = 'No'

            # cuisines
            all_cuisines = list()
            try:
                cuisines_element = driver.find_elements_by_xpath(
                    '//*[@id="root"]/main/div/section[3]/section/section[1]/section[1]/div/a')
                for cuisine in cuisines_element:
                    all_cuisines.append(cuisine.text)
            except Exception as e:
                print(e)
                pass

            # Ratings Updated according to latest UI
            ratings = {}
            try:
                try:
                    dining = 0.0
                    dining = driver.find_element_by_xpath(
                        '//*[@id="root"]/main/div/section[3]/section/section[2]/section[1]/div[1]/p').text
                except:
                    pass
                try:
                    delivery = 0.0
                    delivery = driver.find_element_by_xpath(
                        '//*[@id="root"]/main/div/section[3]/section/section[2]/section[2]/div[1]/p').text
                except:
                    pass

                ratings['Dining'] = dining
                ratings['Delivery'] = delivery
            except:
                pass

            # get Photos count with type
            photos = {}
            try:
                WebDriverWait(driver,5).until(EC.presence_of_element_located((By.LINK_TEXT,'Photos'))).click()
                # photo_button = driver.find_element_by_link_text(
                #     'Photos').click()
                photos_element = WebDriverWait(driver, 5).until(EC.presence_of_all_elements_located(
                    (By.XPATH, '//*[@id="root"]/main/div/section[4]/div/div[1]/div/button/span/span')))

                for p in photos_element:
                    photos[p.text.split(' ')[0]] = p.text.split(' ')[1][1:-1]
            except NoSuchElementException as e:
                print("Photos element missing")
                pass

            # Get all reviews
            # print('Starting to scrap Reviews...')
            reviews = list()
            total_review_count = 0
            try:
                reviews,total_review_count = get_all_review(driver, limit)
            except Exception as e:
                print(e)
                pass

            temp['Name'] = name
            temp["URL"] = url
            temp['Current Status'] = status
            temp["Direction"] = direction
            temp['Contacts'] = all_contacts
            temp['Address'] = address
            temp['Online Order Accepts'] = oo_status
            temp['Table Booking Available'] = book_table
            temp['All Cuisines'] = all_cuisines
            temp['Photos'] = photos
            temp['Total Votes/Reviews'] = total_review_count
            temp['Rating'] = ratings
            temp['Reviews'] = reviews

            output.append(temp)

    except Exception as e:
        print(e)
        pass
    finally:
        driver.quit()
        return output


def get_all_review(driver, limit):
    reviews = list()
    total_reviews = 0
    try:
        reviews_button = driver.find_element_by_link_text('Reviews').click()
        total_reviews_text  = WebDriverWait(driver,5).until(EC.presence_of_element_located((By.XPATH,'//*[@id="root"]/main/div/section[4]/div/div/section[2]/div[1]/div[1]/div/div/div/span/p'))).text
        if len(total_reviews_text) >0:
            total_reviews  = int(total_reviews_text.split('(')[1][:-1])
            limit = total_reviews
        else:
            total_reviews = 0
        
        ps = str(driver.page_source)
        ps = ps[ps.find('res_id')+9:]
        res_id = ps.split(',')[0]
        # print(res_id)
        try:
            api = "https://www.zomato.com/webroutes/reviews/loadMore?res_id={0}&limit={1}".format(
                res_id, limit)
            driver.get(api)
        except Exception as e:
            print(e)

        json_response = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, '/html/body/pre'))).text

        data = json.loads(json_response)
        # print(data)
        noOfPages = data.get('page_data').get('sections').get(
            'SECTION_REVIEWS').get('numberOfPages')
        if noOfPages > 0:
            l = list(data.get('entities').get('RATING').items())
            r = list(data.get('entities').get('REVIEWS').items())
            for i in range(len(l)):
                reviews.append([
                    r[i][1].get('userName'),
                    l[i][1].get('rating'),
                    get_date(r[i][1].get('timestamp')),
                    r[i][1].get('reviewText')
                ])
        else:
            pass

    except Exception as e:
        print(e)
    finally:
        return reviews,total_reviews


def data_write(data,username,start,end):
    try:
        json_data = json.dumps(data, ensure_ascii=False)
        f = open('{0}_data_{1}_{2}.json'.format(username,start,end), 'w')
        f.write(json_data)
        f.close()
    except Exception as e:
        print(e)
        pass


def main():
    fName = os.path.abspath("../resources/all_restro_urls_citywise (1).pickle")
    try:
        urls = fetch_all_urls(filename=fName)
    except Exception as e:
        print(e)
    path = os.path.abspath("../../driver/chromedriver")
    #define some limit if reviwes count not available
    limit = 100000
    print('Starting to scrap zomato info at - {0}\n'.format(datetime.datetime.now()))
    print('Available range of urls is from : 0 to {0}\n'.format(len(urls)))

    username = input('Please input your name : this is just for file tracking :  ')
    start = int(input('Enter starting index : '))
    end = int(input('Enter ending index : '))
    data = fetch_zomato_info(urls[start:end], path, limit)
    print('scraping process Ended {0}'.format(datetime.datetime.now()))
    data_write(data,username,start,end)


if __name__ == '__main__':
    main()
