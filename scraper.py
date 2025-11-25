from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup
import psycopg2
import time
from datetime import datetime

def extract_number(s):
    filtered = ''.join(c for c in s if c.isdigit() or c == ' ')
    return int(filtered.replace(' ', ''))

def get_urls(driver, url_set) -> set:
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    url_raw = soup.find_all("a", class_="sc-cb70b292-7 iVgtqF")
    for x in url_raw:
        url_set.add("https://bina.az" + x["href"])
    print(f"There are total {len(url_set)} links")
    return url_set

#connect to database
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="bina-az",
    user="main",
    password="" #password is not added here :)
)
cursor = conn.cursor()

profile = webdriver.FirefoxProfile()

# Disable images for reducing lag
profile.set_preference("permissions.default.image", 2)
profile.set_preference("dom.ipc.plugins.enabled.libflashplayer.so", "false")
profile.update_preferences()
options = Options()
options.profile = profile
options.page_load_strategy = 'eager'
driver = webdriver.Firefox(options=options)

url = "https://bina.az/items/all"
driver.get(url)
time.sleep(2)

url_list = set()
MAX_WAIT_TIME = 30 # make sure this is big enough so it wont stop unexpectedly because of latency reasons
SCROLL_PAUSE_TIME = 0.8 

counter = 0
last_count = 0
# Get scroll height

while True:
    counter += 1
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight - 650);")

    try:
        WebDriverWait(driver, MAX_WAIT_TIME).until(
            lambda d: len(get_urls(driver, url_list)) > last_count
        )
    except:
        print(f"No new URLs after scrolling {counter} times. Stopping.")
        break

    current_urls = get_urls(driver, url_list)
    if len(current_urls) > last_count:
        url_list.update(current_urls)
        last_count = len(url_list)
    time.sleep(SCROLL_PAUSE_TIME)


url_list_list = list(url_list)

for url in url_list_list:
    cursor.execute("SELECT 1 FROM estates WHERE website_id = %s", (url.removeprefix("https://bina.az/items/"),)) # comma is because it needs to be a tuple for some reason
    if cursor.fetchone():
        print(f"Skipping {url} - already in DB.")
        continue
    else:
        try:
            driver.get(url)
            time.sleep(1)
            html = driver.page_source
            soup = BeautifulSoup(html, "html.parser")
            # our future row data
            filtered_data = {}

            price_element = soup.find("span", class_="price-val")
            price = price_element.text.strip() if price_element else "N/A"
            filtered_data["price"] =  extract_number(price)

            rent_type_element = soup.find("span", class_="price-per")
            rent_type = rent_type_element.text.strip() if rent_type_element else "N/A"
            filtered_data["rent_type"] = rent_type

            address_element = soup.find("div", class_="product-map__left__address")
            address= address_element.text.strip() if address_element else "N/A"
            filtered_data["location"] = address

            product_views_element = soup.find("span", class_ = "product-statistics__i-text")
            product_views = product_views_element.text.strip() if product_views_element else "N/A"
            product_views = float(product_views.split()[2])
            filtered_data["views"] = int(product_views)

            product_ID_element = soup.find("div", class_="product-actions__id")
            product_ID = product_ID_element.text.strip() if product_ID_element else "N/A"
            filtered_data["website_id"] = int(float(product_ID.split()[2]))

            is_agent_element = soup.find("div", class_ ="product-owner__info-region")
            is_agentt = is_agent_element.text.strip() if is_agent_element else "N/A"
            if is_agentt == "mülkiyyətçi":
                is_agentt = False
            else:
                is_agentt = True
            filtered_data["is_agent_listed"] = is_agentt

            selling_type_element = soup.find("a", class_ = "product-breadcrumbs__i-link")
            selling_type = selling_type_element.text.strip() if selling_type_element else "N/A"
            filtered_data["selling_type"] = selling_type


            agency_name_element = soup.find("div", class_= "product-shop__owner-name")
            agency_name = agency_name_element.text.strip() if agency_name_element else "N/A"
            filtered_data["agency_name"] = agency_name

            search_properties = ["Sahə", "Mərtəbə", "Otaq sayı",  "İpoteka","Təmir", "Çıxarış", "Kateqoriya",]

            product_properties = soup.find_all("label", class_="product-properties__i-name")
            for x  in product_properties:
                for y in search_properties:
                    if y in x.text:
                        parent = x.find_parent("div")
                        if parent:
                            value_element = parent.find("span", class_="product-properties__i-value")
                            price_value = value_element.text.strip() if value_element else "N/A"
                            if y == "Təmir" or y == "İpoteka" or y == "Çıxarış":
                                if price_value == "var":
                                    price_value = True
                                else:
                                    price_value = False
                            elif y == "Sahə":
                                price_value = float(price_value.split()[0])
                            filtered_data[y] = price_value
            filtered_data["building_type"] = filtered_data.pop("Kateqoriya", None)
            filtered_data["floor_number"] = filtered_data.pop("Mərtəbə", None)
            filtered_data["area"] = filtered_data.pop("Sahə", None)
            filtered_data["total_room"] = filtered_data.pop("Otaq sayı", None)
            filtered_data["has_certificate"] = filtered_data.pop("Çıxarış", None)
            filtered_data["is_renovated"] = filtered_data.pop("Təmir", None)
            filtered_data["azn_area"] = filtered_data["price"] /filtered_data["area"]
            filtered_data["ipoteka"] = filtered_data.pop("İpoteka", None)
            filtered_data["created_at"] = datetime.now()

            # sent the data to the database
            columns = ', '.join(filtered_data.keys())
            placeholders = ', '.join(['%s'] * len(filtered_data))
            values = list(filtered_data.values())
            query = f"INSERT INTO estates ({columns}) VALUES ({placeholders})"
            cursor.execute(query, values)
            conn.commit()
        except  Exception as e:
            print(f"Error processing {url}: {e}")
            conn.rollback()
            continue

driver.quit()

