from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from bs4 import BeautifulSoup
import psycopg2
import time
from datetime import datetime

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="bina-az",
    user="postgres",
    password=""
)
cursor = conn.cursor()


options = Options()
driver = webdriver.Firefox(options = options)
url = "https://bina.az/items/5316793"
driver.get(url)
time.sleep(1)
html = driver.page_source
soup = BeautifulSoup(html, "html.parser")

filtered_data = {}

price_element = soup.find("span", class_="price-val")
price = price_element.text.strip() if price_element else "N/A"
filtered_data["price"] = int(price.replace(' ', '')) 

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
                if y == "Sahə":
                    price_value = float(price_value.split()[0])
                filtered_data[y] = price_value
filtered_data["building_type"] = filtered_data.pop("Kateqoriya")
filtered_data["floor_number"] = filtered_data.pop("Mərtəbə")
filtered_data["area"] = filtered_data.pop("Sahə")
filtered_data["total_room"] = filtered_data.pop("Otaq sayı")
filtered_data["has_certificate"] = filtered_data.pop("Çıxarış")
filtered_data["is_renovated"] = filtered_data.pop("Təmir")
filtered_data["azn_area"] = filtered_data["price"] / filtered_data["area"]
filtered_data["created_at"] = datetime.now()

columns = ', '.join(filtered_data.keys())
placeholders = ', '.join(['%s'] * len(filtered_data))
values = list(filtered_data.values())

query = f"INSERT INTO buildings ({columns}) VALUES ({placeholders})"

cursor.execute(query, values)
conn.commit()

driver.quit()

