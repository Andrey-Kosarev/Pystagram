import requests
import json
import re
import os
import datetime


class InstagramMediaFile:
    def __init__(self, object_type, resolutions, links, author):
        self.author = author
        self.type = object_type  # Picture or Video
        self.resolutions = resolutions  # Tuple (x, y), if many list [(x, y), (x, y),(x, y)]
        self.__download_links = dict(zip(resolutions, links))

    def info(self):
        print(f"File type : {self.type}")
        print(f"Available resolutions : {self.resolutions}")
        print(self.__download_links)

    def download(self, path, resolution=None):
        # Скачивает файл на hd, принимает аргументами путь и разрешение. Если разрешение не задано, качает в максимальном
        if resolution == None:
            resolution = max(self.__download_links.keys())
        download_link = self.__download_links[resolution]

        if not os.path.exists(path):
            os.mkdir(path)

        ext = ''
        if self.type == "GraphVideo":
            ext = 'mp4'
        elif self.type == 'GraphImage':
            ext = "jpg"

        files_in_dir = len(os.listdir(path))
        file_name = f"\{self.author}-{datetime.date.today()}({files_in_dir + 1}).{ext}"
        full_path = path + file_name

        with open(path + file_name, 'wb') as output_file:
            output_file.write(requests.get(download_link).content)


class InstagramPost():
    def __init__(self, post_link, author):
        self.link = post_link
        self.author = author
        self.json = requests.get(self.link + "/?__a=1").json()['graphql'][
            'shortcode_media']  # параметр а вместо хтмл возвращает джсон
        self.type = self.json["__typename"]
        self.count_objects = self.__item_count()
        self.media_files = self.__populate_object_list()

    def __populate_object_list(self):
        if self.type == 'GraphImage':
            resolutions = []
            links = []
            for item in self.json['display_resources']:
                links.append(item['src'])
                resolutions.append((item['config_width'], item['config_height']))
            return [InstagramMediaFile(object_type=self.type, resolutions=resolutions, links=links, author=self.author)]

        elif self.type == 'GraphSidecar':
            files = []
            edges = self.json['edge_sidecar_to_children']['edges']
            for i in edges:
                obj_type = i['node']['__typename']
                info = i['node']["display_resources"]
                resolutions = []
                links = []

                if obj_type == "GraphImage":
                    for data in info:
                        links.append(data['src'])
                        resolutions.append((data['config_width'], data['config_height']))

                elif obj_type == "GraphVideo":
                    links.append(i['node']['video_url'])
                    resolutions.append((0, 0))

                files.append(
                    InstagramMediaFile(object_type=obj_type, resolutions=resolutions, links=links, author=self.author))
            return files

        elif self.type == "GraphVideo":
            files = []
            files.append(InstagramMediaFile(object_type=self.type, resolutions=[(0, 0)], links=[self.json['video_url']],
                                            author=self.author))
            return files

    def __item_count(self):
        if self.type == 'GraphImage':
            return 1
        elif self.type == 'GraphSidecar':
            return len(self.json['edge_sidecar_to_children']['edges'])


class InstagramProfile:
    def __init__(self, link):
        self.link = link
        self._html = requests.get(link).text
        self.profile_owner = re.findall(r'(title".+?)• Instagram', self._html)[0][16:]
        self.posts = self.__all_posts()

        # ...
        # If profile is closed, raise Exception

    def __all_posts(self):
        shortcodes = re.findall(r"(shortcode.+?),", self._html)
        posts = []

        for i in shortcodes:
            i = i.replace('shortcode":"', '').replace('"', '')
            post_link = r'https://www.instagram.com/p/' + i
            try:
                posts.append(InstagramPost(post_link, self.profile_owner))
            except json.decoder.JSONDecodeError:
                pass
        return posts

    def download_all(self):
        pass