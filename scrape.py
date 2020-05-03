import hashlib
import os
import time
import csv

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options

batch = int(os.getenv('BATCH', 0))
if batch != 0:
    print("fetching %d messages" % batch)

csv_file = open('results.csv', 'w', encoding='utf-8', newline='')
fieldnames = ['user_name', 'user_handle', 'message_date', 'replies', 'retweets', 'likes', 'content', 'hash']

writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
writer.writeheader()

chrome_options = Options()
# chrome_options.add_argument("--headless")

driver = webdriver.Chrome(
    executable_path=os.path.abspath("chromedriver.exe"),
    options=chrome_options
)

# Construct the search url. Note that ?f=live ensures ordering from the latest
driver.get("https://twitter.com/search?f=live&q=(%23opisis)%20until%3A2020-12-31%20since%3A2018-01-01&src=typed_query")

driver.implicitly_wait(5)

count = 0

while True:
    # Wait to load page
    time.sleep(0.5)
    try:
        tweet = driver.find_element_by_xpath('//article[1]')
    except NoSuchElementException:
        break

    body = tweet.find_element_by_xpath("div/div[2]/div[2]")

    # Meta message information
    header = body.find_element_by_xpath("div[1]/div[1]/div[1]/div[1]")
    user_data = header.find_element_by_xpath("div[1]/a[1]/div[1]")
    user_name = user_data.find_element_by_xpath("div[1]").text.replace('\n', ' ')
    user_handle = user_data.find_element_by_xpath("div[2]").text
    message_date = header.find_element_by_xpath("//time[1]").get_attribute('datetime')

    # Statistics
    stats = body.find_element_by_xpath("div[2]/div[last()]")
    replies = stats.find_element_by_xpath("div[1]").text
    retweets = stats.find_element_by_xpath("div[2]").text
    likes = stats.find_element_by_xpath("div[3]").text

    # Content
    content = body.find_element_by_xpath("div[2]/div[1]").text.replace('\n', ' ')

    # Remove element (this should autoreload the DOM so the next message becomes the first)
    driver.execute_script("""
    var element = arguments[0];
    element.parentNode.removeChild(element);
    """, tweet)

    data = {'user_name': user_name, 'user_handle': user_handle, 'message_date': message_date,
            'replies': replies if replies != '' else '0', 'retweets': retweets if retweets != '' else '0',
            'likes': likes if likes != '' else '0', 'content': content,
            'hash': hash(frozenset({"user_handle": user_handle, "content": content}))}
    writer.writerow(data)

    print(data)
    count = count + 1

    if batch != 0 and count == batch:
        break

driver.close()

print("processed %d messages" % count)
