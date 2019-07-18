####################
# redmercury - A static site generator for podcasts (https://github.com/jrigden/redmercury)
#
# The MIT License (MIT)
# Copyright 2019 Jason Rigden (jasonrigden@jasonrigden.com)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
# OR OTHER DEALINGS IN THE SOFTWARE.
# ####################


from datetime import datetime
import dateutil.parser
import jinja2
import hashlib
import locale
import markdown
import mutagen
import os
from shutil import copyfile
import slugify
import sys
from urllib.parse import urlparse
import yaml

####################
# Usefule Bookmarks:
# https://github.com/jrigden/redmercury
# https://help.apple.com/itc/podcasts_connect/#/itcb54353390
# https://cyber.harvard.edu/rss/rss.html
####################

####################
# Global Constants
####################

CONTENT_SEPARATOR = '=========='
VERSION = 'v0.1.0'
GENERATOR = 'redmercury '+ VERSION +' (https://github.com/jrigden/redmercury)'


####################
# Global Variables
####################

Episodes = []
Pages = []
Site = {}
Target = None

####################
# Misc Initializations
####################

file_loader = jinja2.FileSystemLoader('templates')
env = jinja2.Environment(loader=file_loader)

####################
# Path Helpers
####################

def get_asset_path():
    path = os.path.abspath(__file__)
    path = os.path.dirname(path)
    return os.path.join(path, "assets")


def get_audio_path():
    return os.path.join(Target, "audio")

def get_config_path():
    return os.path.join(Target, "config.yaml")

def get_content_path():
    return os.path.join(Target, "content")

def get_MP3_path(base_name):
    return os.path.join(get_audio_path(), base_name + ".mp3")

def get_output_path():
    return os.path.join(Target, "output")

####################
# New Site Functions
####################

def make_dirs():
    if not os.path.exists(get_audio_path()):
        os.mkdir(get_audio_path())
    else:
        print("Audio directory already exists")

    if not os.path.exists(get_content_path()):
        os.mkdir(get_content_path())
    else:
        print("Content directory already exists")

    if not os.path.exists(get_output_path()):
        os.mkdir(get_output_path())
    else:
        print("Output directory already exists")

def make_config_template():
    config_template = {
        "BaseAudioURL": "",
        "BaseURL": "",
        "Copyright": "",
        "CoverArtURL": "",
        "Description": "",
        "Categories": [
            {
                "Name": "",
                "Parent": ""
            },
        ],
        "Explicit": "",
        "OwnerEmail": "",
        "OwnerName": "",
        "NavLinks": [
            {
                "Name": "",
                "URL": ""
            }
        ],
        "SocialLinks": [
            {
                "Name": "",
                "URL": ""
            }
        ],
        "SubscribeLinks": [
            {
                "Name": "",
                "URL": ""
            }
        ],
        "StatsPrefix": "",
        "SubTitle": "",
        "Title": ""
    }
    config_template_path = os.path.join(Target, "config.yaml")
    if os.path.exists(get_config_path()):
        print('Config file already exists')
        return
    with open(get_config_path(), 'w') as f:
        f.write(yaml.dump(config_template))

####################
# Processing Functions
####################

def get_episode_and_season_number(base_name):
    data = base_name.split("_")[1]
    [season, episode_number] = data.split("E")
    season_number = season.split("S")[1]
    season_number = str(int(season_number))
    episode_number = str(int(episode_number))
    return season_number, episode_number


def get_episode_stats_URL(file_name):
    episode_url = Site['BaseAudioURL'] + '/' + file_name
    if not Site['StatsPrefix']:
        return episode_url
    parsed_url = urlparse(episode_url)
    url_frament = parsed_url[1] + parsed_url[2]
    stats_URL = Site['StatsPrefix'] + url_frament
    return stats_URL

####################
# Rendering Functions
####################

def render_assets():
    css_asset_path = os.path.join(get_asset_path(), 'redmercury.css')
    js_asset_path = os.path.join(get_asset_path(), 'redmercury.js')
    robots_asset_path = os.path.join(get_asset_path(), 'robots.txt')

    css_name = 'redmercury-' + VERSION + '.css'
    js_name = 'redmercury-' + VERSION + '.js'

    css_path = os.path.join(get_output_path(), css_name)
    js_path = os.path.join(get_output_path(), js_name)
    robots_path = os.path.join(get_output_path(), 'robots.txt')

    if not os.path.exists(css_path):
        copyfile(css_asset_path, css_path)
    if not os.path.exists(js_path):
        copyfile(js_asset_path, js_path)
    if not os.path.exists(robots_path):
        copyfile(robots_asset_path, robots_path)



def render_episode(episode):
    episode_dir_path = os.path.join(get_output_path(), episode['Meta']['Slug'])
    if not os.path.exists(episode_dir_path):
        os.mkdir(episode_dir_path)
    page_path = os.path.join(episode_dir_path, "index.html")
    template = env.get_template('content.html')
    output = template.render(site=Site, content=episode)
    with open(page_path, 'w') as f:
        f.write(output)

def render_episodes():
    for episode in Episodes:
        render_episode(episode)
        render_ID3_tags(episode)

def render_ID3_tags(episode):
    mp3_path = get_MP3_path(episode['Meta']['BaseName'])
    audio = mutagen.easyid3.EasyID3(mp3_path)
    audio["album"] = "Season " + episode['Meta']['Season']
    audio["artist"] = Site['Title']
    audio["copyright"] = Site['Copyright']
    audio["date"] = episode['Meta']['Date']
    audio["discnumber"] = episode['Meta']['Season']
    audio["genre"] = "Podcast"
    audio["title"] = episode['Meta']['Title']
    audio["tracknumber"] = episode['Meta']['Episode']
    audio["website"] = Site['BaseURL'] +'/'+ episode['Meta']['Slug']
    audio.save()
    end = datetime.now().timestamp()


def render_front_page():
    file_path = os.path.join(get_output_path(), "index.html")
    template = env.get_template('frontpage.html')
    output = template.render(site=Site, episodes=Episodes)
    with open(file_path, 'w') as f:
        f.write(output)

def render_pages():
    for page in Pages:
        render_page(page)
    
def render_page(page):
    page_dir_path = os.path.join(get_output_path(), page['Meta']['Slug'])
    if not os.path.exists(page_dir_path):
        os.mkdir(page_dir_path)
    page_path = os.path.join(page_dir_path, "index.html")
    template = env.get_template('content.html')
    output = template.render(site=Site, content=page)
    with open(page_path, 'w') as f:
        f.write(output)

def render_rss():
    rss = {}
    rss['lastBuildDate'] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S") + " +0000"
    rss['pubDate'] = Episodes[0]['Meta']['pubDate']
    rss['generator'] = GENERATOR

    file_path = os.path.join(get_output_path(), "rss.xml")
    template = env.get_template('rss.xml')
    output = template.render(site=Site, episodes=Episodes, rss=rss)
    with open(file_path, 'w') as f:
        f.write(output)

def render_site():
    render_assets()
    render_episodes()
    render_front_page()
    render_pages()
    render_rss()
    render_site_map()

def render_site_map():
    locs = Pages + Episodes
    file_path = os.path.join(get_output_path(), "sitemap.xml")
    template = env.get_template('sitemap.xml')
    output = template.render(site=Site, locs=locs)
    with open(file_path, 'w') as f:
        f.write(output)


####################
# Loading Functions
####################

def load_config():
    with open(get_config_path()) as f:
        data = yaml.safe_load(f)
    data['VERSION'] = VERSION
    return data

def load_episode(file_name):
    meta = {}
    with open(os.path.join(get_content_path(), file_name)) as f:  
        raw_data = f.read()
    split_data = raw_data.split(CONTENT_SEPARATOR)
    meta = yaml.safe_load(split_data[0])
    meta['BaseName'] = file_name.split(".md")[0]
    meta['Slug'] = slugify.slugify(meta['Title'])

    meta['Enclosure'] = load_enclosure(meta['BaseName'])
    
    created = dateutil.parser.parse(meta['Date'])
    meta['pubDate'] = created.strftime("%a, %d %b %Y %H:%M:%S") + " +0000"
    meta['Timestamp'] = created.timestamp()
    meta['lastmod'] = created.strftime("%Y-%m-%d")


    meta['Season'], meta['Episode'] = get_episode_and_season_number(meta['BaseName'])

    episode = {}
    episode['Meta'] = meta
    episode['Summary'] = markdown.markdown(split_data[1])
    episode['Body'] = markdown.markdown(split_data[2])

    return episode

def load_enclosure(base_name):
    audio_data = {}
    mp3_path = get_MP3_path(base_name)
    if not os.path.exists(mp3_path):
        print('ERROR: MP3 missing for ' + base_name)
        exit()
    audio_data['FileName'] = base_name + ".mp3"
    audio_data['URL'] = Site['BaseAudioURL'] + '/' + audio_data['FileName']
    audio_data['StatsURL'] = get_episode_stats_URL(audio_data['FileName'])
    audio_data['Length'] = os.path.getsize(mp3_path)
    audio_file = mutagen.File(mp3_path)
    audio_data['Duration'] = int(audio_file.info.length)
    return audio_data


def load_episodes():
    episodes = []
    file_names = get_episode_file_names()
    for file_name in file_names:
        episode = load_episode(file_name)
        episodes.append(episode)
    return sort_episodes(episodes)

def load_page(file_name):
    meta = {}
    with open(os.path.join(get_content_path(), file_name)) as f:  
        raw_data = f.read()
    split_data = raw_data.split(CONTENT_SEPARATOR)
    meta = yaml.safe_load(split_data[0])
    meta['BaseName'] = file_name.split(".md")[0]
    meta['Slug'] = slugify.slugify(meta['Title'])    
    created = dateutil.parser.parse(meta['Date'])
    meta['pubDate'] = created.strftime("%a, %d %b %Y %H:%M:%S") + " +0000"
    meta['lastmod'] = created.strftime("%Y-%m-%d")
    meta['Timestamp'] = created.timestamp()

    page = {}
    page['Meta'] = meta
    page['Summary'] = markdown.markdown(split_data[1])
    page['Body'] = markdown.markdown(split_data[2])

    return page

def load_pages():
    pages = []
    file_names = get_page_file_names()
    for file_name in file_names:
        page = load_page(file_name)
        pages.append(page)
    return pages



####################
# Misc Functions
####################


def sort_episodes(episodes):
    episodes = sorted(episodes, key = lambda i: i['Meta']['Timestamp'], reverse=True) 
    return episodes

def get_episode_file_names():
    episodes = []
    for each in os.listdir(get_content_path()):
        if each.endswith(".md"):
            if not each.startswith("Page"):
                episodes.append(each)
    return episodes

def get_page_file_names():
    pages = []
    for each in os.listdir(get_content_path()):
        if each.endswith(".md"):
            if each.startswith("Page"):
                pages.append(each)
    return pages



####################
# __main__
####################

if __name__ == "__main__":
    try:
        mode = sys.argv[1]
        Target = sys.argv[2]
    except IndexError:
        print("ERROR: Insufficient Arguments")
    if mode == "-i":
        make_dirs()
        make_config_template()
        exit()
    if mode == "-w":
        Site = load_config()
        Episodes = load_episodes()
        Pages = load_pages()
        render_site()