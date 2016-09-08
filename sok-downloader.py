__author__ = 'Nicholas McKinney'

import requests
import logging
import json
import os
import argparse
from bs4 import BeautifulSoup

Defcon = "Defcon"
BSidesLV = "BSidesLV"
AllowedChoices = (Defcon, BSidesLV)
Conferences = {Defcon: 32, BSidesLV: 39}

PLAYLIST_URL = "https://www.sok-media.com/player?action=get_playlist&conf_id={conference}"
VIDEO_URL = "https://www.sok-media.com/player?session_id={video}&action=get_video"
BASE_URL = "https://www.sok-media.com"
LOGIN_URL = "https://www.sok-media.com/node?destination=node"

logger = logging.getLogger("SOK-Media-Downloader")
logger.setLevel("INFO")
stream_handler = logging.StreamHandler()
stream_handler.setLevel("INFO")
logger.addHandler(stream_handler)


class Content:
    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value):
        self._id = value

    @property
    def name(self):
        return self.name

    @name.setter
    def name(self, value):
        self.name = value


class Client:
    def __init__(self, username, password):
        self._username = username
        self._password = password
        self._session = requests.Session()

    def login(self):
        r = self._session.get(BASE_URL)
        if self.failed(r):
            logger.error("[*] Failed to access login page")
            raise Exception("Failed connection")
        soup = BeautifulSoup(r.content, 'html.parser')
        div = soup.find(id="page_container")
        inputs = div.find_all("input", type="hidden")
        payload = {
            "name" : self._username,
            "pass": self._password,
            "op": "Log+in"
        }
        for input in inputs:
            payload[input.attrs['name']] = input.attrs['value']
        r = requests.post(LOGIN_URL, data=payload, headers={'Content-Type': 'application/x-www-form-urlencoded'})
        if len(r.history):
            return requests.utils.dict_from_cookiejar(r.history[0].cookies)

    def get_video(self, video, directory, cookies=None):
        logger.info("[*] Downloading video: %s" % video.name)
        r = self._session.get(VIDEO_URL.format(video=video.id), cookies=cookies)
        if self.failed(r):
            logger.error("[*] Failed to get download URL: {title}".format(title=video.name))
            return
        content = json.loads(r.content)
        stream = self._session.get(content['url'], stream=True)
        if self.failed(stream):
            logger.error("[*] Failed to get stream for: {title}".format(title=video.name))
            return
        dl_path = os.path.join(directory, video.name.replace("/","")+'.mp4')
        if os.path.exists(dl_path):
            logger.warning("[*] Video %s already exists. Skipping..." % video.name)
            return
        with open(dl_path, 'wb') as f:
            for chunk in stream.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        logger.info("[*] Downloaded video: %s" % video.name)
        return dl_path

    def _make_vid(self, d):
        c = Content()
        c.id = d['sess_id']
        c.name = d['sess_data']['session_name']
        return c

    def get_playlist(self, conference, cookies=None):
        logger.info("[*] Getting playlist videos for {conference}".format(conference=conference.name))
        r = self._session.get(PLAYLIST_URL.format(conference=conference.id), cookies=cookies)
        if self.failed(r):
            logger.error("[*] Failed to get video playlist information for {conference}".format(conference=conference.name))
            return
        content = json.loads(r.content)
        videos = [self._make_vid(d) for d in content['data']]
        logger.info('[*] Retrieved %d videos from conference %s' % (len(videos), conference.name))
        return videos

    def failed(self, resp):
        return True if resp.status_code != 200 else False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('conference', choices=AllowedChoices)
    parser.add_argument('outpath')
    parser.add_argument('username')
    parser.add_argument('password')
    args = parser.parse_args()
    c = Content()
    c.id = Conferences[args.conference]
    c.name = args.conference
    cli = Client(username=args.username, password=args.password)
    cookies = cli.login()
    videos = cli.get_playlist(c, cookies=cookies)
    for video in videos:
        cli.get_video(video, args.outpath, cookies=cookies)

if __name__ == '__main__':
    main()
