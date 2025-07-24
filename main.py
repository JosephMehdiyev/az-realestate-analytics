from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from bs4 import BeautifulSoup
import time

options = Options()
driver = webdriver.Firefox(options = options)
url = "https://bina.az/items/5320029"
driver.get(url)
time.sleep(1)
html = driver.page_source
soup = BeautifulSoup(html, "html.parser")

price_element = soup.find("span", class_="price-val")
price = price_element.text.strip() if price_element else "N/A"

adress_element = soup.find("div", class_="product-map__left__address")
adress= adress_element.text.strip() if adress_element else "N/A"

product_views_element = soup.find("span", class_ = "product-statistics__i-text")
product_views = product_views_element.text.strip() if product_views_element else "N/A"


search_properties = ["Kateqoriya", "Sahə", "Çıxarış", "Təmir", "Mərtəbə", "Otaq sayı", "İpoteka"]

product_properties = soup.find_all("label", class_="product-properties__i-name")
for x  in product_properties:
    for y in search_properties:
        if y in x.text:
            parent = x.find_parent("div")
            if parent:
                price_square_element = parent.find("span", class_="product-properties__i-value")
                price_square = price_square_element.text.strip() if price_square_element else "N/A"
                print(f"{y}: {price_square}")

print(f"Price: {price}")
print(f"Adress: {adress}")
print(f"Views: {product_views}")



driver.quit()

