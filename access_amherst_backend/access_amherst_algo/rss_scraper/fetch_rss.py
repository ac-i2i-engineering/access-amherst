import requests
import os
from datetime import datetime


def fetch_rss():
    url = 'https://thehub.amherst.edu/events.rss'
    response = requests.get(url)

    # Define the directory and file name
    directory = 'access_amherst_algo/rss_scraper/rss_files'
    file_name = os.path.join(
        directory,
        'hub_' +
        datetime.now().strftime('%Y_%m_%d_%H') +
        '.xml')

    # Save the content as an XML file
    with open(file_name, 'wb') as file:
        file.write(response.content)


if __name__ == '__main__':
    fetch_rss()
