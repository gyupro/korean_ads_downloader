from bs4 import BeautifulSoup
import urllib
from urllib.request import urlopen
import os

import argparse
from threading import Thread
from queue import Queue
from get_cpu_count import available_cpu_count
from progress import print_progress
import sys

parser = argparse.ArgumentParser()
parser.add_argument('-s','--save-path', type=str, default="kobaco/", help='save path for the captured image')
parser.add_argument('-v','--video-path', type=str, default="dst/", help='save path for the videos')
parser.add_argument('-r','--root-url', type=str, default='https://aisac.kobaco.co.kr', help='root url')
opt = parser.parse_args()

# 한국방송광고진흥공사, kobaco
root_url = opt.root_url

class DownloadWorker(Thread):
    def __init__(self, queue):
        Thread.__init__(self)
        self.queue = queue
    def run(self):
        while True:
            link = self.queue.get()
            try:
                download_link(link)
            finally:
                self.queue.task_done()

def download_link(link):
    """
    :param link: URL link which contains html page of 12 videos.
    """
    html_page = urlopen(link)
    soup = BeautifulSoup(html_page, 'html.parser')
    for div in soup.findAll('div', {'class': 'adv-video'}):
        new_str = str(div).replace('<div class="adv-video" style="background-image: url(', '').replace('adimg/image',
                                                                                                       'advideo/video').replace(
            """1_0');"></div>""", '')
        site_url = root_url + new_str.replace("'", '')

        file_name = os.path.basename(site_url[:-1])
        os.makedirs(opt.video_path, exist_ok=True)
        download_path = os.path.join(opt.video_path, file_name+'.mp4')
        if not os.path.exists(download_path):
            urllib.request.urlretrieve(site_url, download_path)

class CheckQueue(Thread):
    def __init__(self, queue):
        """
        Progress bar that indicates how much time left to be finished
        """

        Thread.__init__(self)
        self.queue = queue
        self.q_size = -1000
    def run(self):
        import time
        while True:
            time.sleep(1)
            if self.q_size != self.queue.qsize():
                self.q_size = self.queue.qsize()
                print_progress(0, self.q_size, 'Progress', 'Complete', 1, 50)






if __name__ == '__main__':

    queue = Queue()
    print("Available CPU Count ... {}".format(available_cpu_count()))

    # create workers up to available counts
    for i in range(available_cpu_count()):
        worker = DownloadWorker(queue)
        worker.start()

    check_queue = CheckQueue(queue)
    check_queue.daemon = True
    check_queue.start()

    # page URL
    url = 'https://aisac.kobaco.co.kr/site/main/advideo/list_all_top?cp=___&pageSize=12&sortOrder=ADV_LIKE&sortDirection=DESC&listType=list&startDate=2017-01-01&endDate=2021-05-18'

    # one pages contains 12 ads, 1742 pages are available at 20th may 2021.
    for i in range(1742):
        link = url.replace('___', str(i))
        queue.put(link)

    # wailt until all queue is empty.
    queue.join()
    print("---- Task Done ----")
