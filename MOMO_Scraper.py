#from selenium import webdriver
#from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait as wait
from selenium.webdriver.common.by import By
import undetected_chromedriver as uc
import time
import csv
import os
from datetime import datetime
import pandas as pd
import warnings
import re
import sys
import numpy as np
warnings.filterwarnings('ignore')
from multiprocessing import freeze_support


def read_inputs():

    file = os.getcwd() + '\\links.csv'
    if not os.path.exists(file):
        print("Couldn't find the input file 'links.csv', press any key to exit ...")
        input()
        sys.exit()

    try:
        df = pd.read_csv(file)
        df.drop_duplicates(inplace=True)
        df.dropna(inplace=True)
        links = df.iloc[:, 0].values.tolist()
    except:
        print("Error in processing the input file 'links.csv', exiting the program ...")
        sys.exit()

    return links

def initialize_bot():

    # Setting up chrome driver for the bot
    #chrome_options  = webdriver.ChromeOptions()
    chrome_options = uc.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_argument("--enable-javascript")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    #path = ChromeDriverManager().install()
    #driver = webdriver.Chrome(path, options=chrome_options)
    chrome_options.page_load_strategy = 'normal'
    driver = uc.Chrome(version_main=108, options=chrome_options)
    driver.set_window_size(1920, 1080, driver.window_handles[0])
    driver.maximize_window()
    driver.set_page_load_timeout(300)
    return driver

def process_links(driver, links, output):

    print('-'*100)
    print('Processing links before scraping')
    print('-'*100)
    selectors = ['div.TabContent', 'div.prdListArea.bt770class', 'div.hotRankingArea.btclass.bt770class', 'div.listArea']
    n = len(links)
    int_prods = {}
    for i, link in enumerate(links):
        print(f'Processing input link {i+1}/{n}')
        # processed link
        # single product link
        if 'https://www.momoshop.com.tw/goods/' in link:
            with open(output, 'a', newline='', encoding='utf-8-sig') as file:
                writer = csv.writer(file)
                writer.writerow([link])

            # checking other interests
            driver.get(link)
            try:
                divs = wait(driver, 2).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.recordAreaNew")))
                for div in divs:
                    if '別人也逛過' in div.text:
                        tags = wait(div, 2).until(EC.presence_of_all_elements_located((By.TAG_NAME, "a")))
                        top = 0
                        for tag in tags:
                            # scrape the top five links only
                            if top == 5: break
                            try:
                                url = tag.get_attribute('href')
                                if 'https://www.momoshop.com.tw/goods/' in url:
                                    top += 1
                                    if link not in int_prods:
                                        int_prods[link] = [url]
                                    else:
                                        int_prods[link].append(url)
                                    #with open(output, 'a', newline='', encoding='utf-8-sig') as file:
                                     #   writer = csv.writer(file)
                                     #   writer.writerow([url])
                            except:
                                pass
            except:
                pass

            continue

        driver.get(link)
        ## scrolling to the end of the page
        while True:  
            try:
                height1 = driver.execute_script("return document.body.scrollHeight")
                driver.execute_script(f"window.scrollTo(0, {height1})")
                time.sleep(1)
                height2 = driver.execute_script("return document.body.scrollHeight")
                if int(height2) == int(height1):
                    break
            except Exception as err:
                continue
         
        # checking if a category link is provided
        for sel in selectors:
            try:
                elems = wait(driver, 1).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, f"{sel}")))
            except:
                continue
            for elem in elems:
                try:
                    tags = wait(elem, 2).until(EC.presence_of_all_elements_located((By.TAG_NAME, "a")))
                    for tag in tags:
                        url = tag.get_attribute('href')
                        if url == None: continue
                        if 'https://www.momoshop.com.tw/goods/GoodsDetail.jsp?' in url:
                            with open(output, 'a', newline='',                  encoding='utf-8-sig') as file:
                                writer = csv.writer(file)
                                writer.writerow([url])
                except:
                    continue

    # return processed links
    df = pd.read_csv(output)
    df.drop_duplicates(inplace=True)
    prod_links = df['Link'].values.tolist()

    return prod_links, int_prods

def get_prod_details(prod, driver, link, ind):

    # check if the link is for a product or other interest
    other = False
    if ind != 0:
        other = True

    driver.get(link)
    time.sleep(1)

    # scraping product URL
    if other:
        prod[f'Other Interest {ind} URL'] = link
    else:
        prod['Product URL'] = link

    # scraping product ID
    try:
        ul = wait(driver, 2).until(EC.presence_of_element_located((By.XPATH, "//ul[@id='categoryActivityInfo']")))
        lis = wait(ul, 2).until(EC.presence_of_all_elements_located((By.TAG_NAME, "li")))
        for li in lis:
            if '品號' in li.text:
                ID = li.text.split('：')[-1].strip() 
                if other:
                    prod[f'Other Interest {ind} ID'] = ID
                else:
                    prod['Product ID'] = ID
                break
    except:
        pass

    # scraping product title
    try:
        title = wait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "p.fprdTitle"))).text
        if other:
            prod[f'Other Interest {ind} Title'] = title
        else:
            prod['Product Title'] = title
    except:
        pass
                
    # scraping product price
    try:
        price = wait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "li.special"))).text
        price = re.sub("[^0-9]", "", price)
        if other:
            prod[f'Other Interest {ind} Price'] = price
        else:
            prod['Product Price'] = price
    except:
        pass

    # scraping product description 
    try:    
        des = ''
        ul = wait(driver, 2).until(EC.presence_of_element_located((By.XPATH, "//ul[@id='categoryActivityInfo']")))
        lis = wait(ul, 2).until(EC.presence_of_all_elements_located((By.TAG_NAME, "li")))
        for li in lis:
            if '品號' not in li.text:
                des += li.text
                des += '\n'
                if other:
                    prod[f'Other Interest {ind} Description'] = des
                else:                
                    prod['Product Description'] = des   
    except:
        pass

    # scraping product delivery 
    try:
        ul = wait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "ul.prdPriceDetail")))
        lis = wait(ul, 2).until(EC.presence_of_all_elements_located((By.TAG_NAME, "li")))
        for li in lis:
            if '配送方式' in li.text:
                delivery = li.text.split(':')[-1].strip()
                if other:
                    prod[f'Other Interest {ind} Delivery'] = delivery
                else:                   
                    prod['Product Delivery'] = delivery
                break
    except:
        pass
          
    # scraping product return 
    try:
        div = wait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.vendordetailview.msgArea")))
        retrn = wait(div, 2).until(EC.presence_of_element_located((By.TAG_NAME, "ul"))).get_attribute('textContent').strip()
        if other:
            prod[f'Other Interest {ind} Return Info'] = retrn
        else: 
            prod['Return Info'] = retrn
    except:
        pass

    # scraping product category
    try:
        cat_div = wait(driver, 2).until(EC.presence_of_element_located((By.XPATH, "//div[@id='bt_2_layout_NAV']")))
        lis = wait(cat_div, 2).until(EC.presence_of_all_elements_located((By.TAG_NAME, "li")))
        cat = ''
        for li in lis:
            cat += li.text + ' \ '
        if other:
            prod[f'Other Interest {ind} Category'] = cat[:-2]
        else: 
            prod['Product Category'] = cat[:-2]
    except:
        pass

    # scraping product image link
    try:
        img = wait(driver, 2).until(EC.presence_of_element_located((By.XPATH, "//img[@name='l_img' and @class='jqzoom']")))
        url = img.get_attribute("src")
        if url[:6].lower() == 'https:':
            if other:
                prod[f'Other Interest {ind} Product Image'] = url
            else:
                prod['Product Image'] = url
    except:
        pass

    # scraping store name
    try:
        ul = wait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "ul.prdPriceDetail")))
        lis = wait(ul, 2).until(EC.presence_of_all_elements_located((By.TAG_NAME, "li")))
        for li in lis:
            if '品牌名稱' in li.text:
                store = li.text.split(':')[-1].strip()
                if other:
                    prod[f'Other Interest {ind} Store Name'] = store
                else:
                    prod['Store Name'] = store
                break         
    except:
        pass            
            
    # scraping product rating
    try:
        score = wait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "span.productRatingScore"))).text
        if other:
            prod[f'Other Interest {ind} Product Rating'] = score
        else:
            prod['Product Rating'] = score
    except:
        pass            
            
    # scraping product total solds
    try:
        solds = wait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "p.productTotalSales"))).text
        solds = re.findall("[0-9\,]+", solds)[0]
        if other:
            prod[f'Other Interest {ind} Sold'] = solds
        else:
            prod['Sold'] = solds
    except:
        pass
        
def scrape_prods(driver, prod_links, int_prods, output1):

    keys = ["Product ID",	"Product URL",	"Product Title",	"Product Price",	"Product Origin",	"Product Category",	"Product Description",	"Product Delivery",	"Product Rating",	"Product Image",	"Product Comments",	"Return Info",	"Store Name",	"Store Rating", "Sold"]

    print('-'*100)
    print('Scraping links ...')
    print('-'*100)
    nlinks = len(prod_links)
    data = pd.DataFrame()
    for i, link in enumerate(prod_links):   
        try:
            prod = {}
            for key in keys:
                prod[key] = ''
            get_prod_details(prod, driver, link, 0)
            print(f'Link {i+1}/{nlinks} is scraped successfully!')
        except:
            print(f'Error in scraping link {i+1}/{nlinks}, skipping ...') 
        if link in int_prods:
            nint = len(int_prods[link])
            for j, url in enumerate(int_prods[link]):
                try:
                    get_prod_details(prod, driver, url, j+1)
                    print(f'  Other interest {j+1}/{nint} is scraped successfully!')
                except:
                    print(f'Error in scraping link {i+1}/{nlinks}, skipping ...')

        # checking if the produc data has been scraped successfully
        if prod['Product ID'] != '' and prod['Product Title'] != '' and prod['Product Price'] != '':
            # output scraped data
            data = data.append([prod.copy()])

        if np.mod(i+1, 100) == 0:
            #print('Outputting scraped data ...')
            data.to_csv(output1, encoding='utf-8-sig', index=False)

    #print('Outputting scraped data ...')
    data.to_csv(output1, encoding='utf-8-sig', index=False)
                   
def initialize_output():

    stamp = datetime.now().strftime("%d_%m_%Y_%H_%M")
    path = os.getcwd() + '\\scraped_data\\' + stamp
    if not os.path.exists(path):
        os.makedirs(path)

    file1 = f'MOMO_{stamp}.csv'
    file3 = "temp.csv"

    # Windws and Linux slashes
    if os.getcwd().find('/') != -1:
        output1 = path.replace('\\', '/') + "/" + file1
        output3 = path.replace('\\', '/') + "/" + file3
    else:
        output1 = path + "\\" + file1
        output3 = path + "\\" + file3
  
    with open(output3, 'w', newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file)
        writer.writerow(['Link'])

    return output1, output3

def main():

    start_time = time.time()
    freeze_support()
    links = read_inputs()
    output1, output3 = initialize_output()

    while True:
        try:
            try:
                driver = initialize_bot()
            except:
                print('Error: Failed to initialize the Chrome driver, please make sure that Chrome is updated to the latest version and the internet connection is working')
                input()
                sys.exit()

            prod_links, int_prods = process_links(driver, links, output3)
            scrape_prods(driver, prod_links, int_prods, output1)
            break
        except Exception as err: 
            print(f'Error: {err}')
            driver.quit()
            time.sleep(5)

    driver.quit()
    # removing the temp file
    if os.path.exists(output3):
        os.remove(output3) 
    print('-'*100)
    elapsed_time = round(((time.time() - start_time)/60), 2)
    input(f'Process is completed successfully in {elapsed_time} mins! Press any key to exit.')

if __name__ == '__main__':

    main()

