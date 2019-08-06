import argparse
from datetime import datetime
import logging
import os


import dateutil.parser
import jinja2
import markdown
from slugify import slugify
import yaml

####################
# Global Constants
####################

VERSION = "0.1.0"
CONTENT_SEPARATOR = '=========='
GENERATOR = 'redmercury '+ VERSION +' (https://github.com/jrigden/redmercury)'


####################
# Setup
####################

site_path = ''
file_loader = jinja2.FileSystemLoader('templates')
env = jinja2.Environment(loader=file_loader)

parser = argparse.ArgumentParser(description='A static site generator for blogs and podcasts. v' + VERSION)
parser.add_argument("-v", "--verbose",  help="increase verbosity", action="store_true")
parser.add_argument("-i", "--initialize", help="initialize site", action="store_true")
#parser.add_argument("-r", "--render", help="render site", action="store_true")
parser.add_argument('path', help="path to site")
args = parser.parse_args()




##############################
# Path Functions
##############################
def get_config_path():
    return os.path.join(site_path, "config.yaml")

def get_content_path():
    return os.path.join(site_path, "content")

def get_footer_path():
    return os.path.join(site_path, "footer.html")

def get_header_path():
    return os.path.join(site_path, "header.html")

def get_post_ending_path():
    return os.path.join(site_path, "post_ending.html")

def get_output_path():
    return os.path.join(site_path, "output")

##############################
# Load Site Functions
##############################

def read_config():
    with open(get_config_path()) as f:
        data = yaml.safe_load(f)
    return data

def read_footer():
    reader = open(get_footer_path(), "r")
    footer = reader.read()
    reader.close
    return footer

def read_header():
    reader = open(get_header_path(), "r")
    header = reader.read()
    reader.close
    return header

def read_post_ending():
    reader = open(get_post_ending_path(), "r")
    ending = reader.read()
    reader.close
    return ending


##############################
# Read Post Functions
##############################

def get_post_paths():
    paths = []
    for each in os.listdir(get_content_path()):
        if each.endswith(".md"):
            post_path = os.path.join(get_content_path(), each)
            paths.append(post_path)
    return paths

def load_post(file_path):
    post = {}
    with open(file_path) as f:  
        raw_data = f.read()
    split_data = raw_data.split(CONTENT_SEPARATOR)
    meta = yaml.safe_load(split_data[0])
    meta['slug'] = slugify(meta['title'])
    meta['datetime'] = dateutil.parser.parse(meta['date'])
    meta['pubDate'] = meta['datetime'].strftime("%a, %d %b %Y %H:%M:%S") + " GMT"
    post['body'] = markdown.markdown(split_data[1])
    post['meta'] = meta
    return post

def get_posts():
    posts = []
    for file_path in get_post_paths():
        post = load_post(file_path)
        posts.append(post)
    posts = sorted(posts, key = lambda i: i['meta']['datetime'], reverse=True)
    return posts


##############################
# Render Functions
##############################

def render_site():
    site = read_config()
    site['footer'] = read_footer()
    site['header'] = read_header()
    site['post_ending'] = read_post_ending()
    posts = get_posts()
    render_front_page(site, posts)
    render_site_map(site, posts)
    render_rss(site, posts)
    for post in posts:
        render_post(site, post)

def render_front_page(site, posts):
    file_path = os.path.join(get_output_path(), "index.html")
    template = env.get_template('frontpage.html')
    output = template.render(site=site, posts=posts)
    with open(file_path, 'w') as f:
        f.write(output)

def render_post(site, post):
    dir = os.path.join(get_output_path(), post['meta']['slug'])
    if not os.path.exists(dir):
        os.mkdir(dir)
    post_path = os.path.join(dir, "index.html")
    template = env.get_template('post.html')
    output = template.render(site=site, post=post)
    with open(post_path, 'w') as f:
        f.write(output)

def render_rss(site, posts):
    rss = {}
    rss['lastBuildDate'] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S") + " +0000"
    rss['pubDate'] = posts[0]['meta']['datetime'].strftime("%a, %d %b %Y %H:%M:%S") + " +0000"
    rss['generator'] = GENERATOR

    file_path = os.path.join(get_output_path(), "rss.xml")
    template = env.get_template('rss.xml')
    output = template.render(site=site, posts=posts, rss=rss)
    with open(file_path, 'w') as f:
        f.write(output)

def render_site_map(site, posts):
    file_path = os.path.join(get_output_path(), "sitemap.xml")
    template = env.get_template('sitemap.xml')
    output = template.render(site=site, posts=posts)
    with open(file_path, 'w') as f:
        f.write(output)




##############################
# Initialize New Site Functions
##############################

def make_config_file():
    logging.info('      Creating config file')
    config_template = {
        "author": "",
        "baseURL": "",
        "title": ""
    }
    with open(get_config_path(), 'w') as f:
        f.write(yaml.dump(config_template))

def make_site_directories():
    os.mkdir(get_content_path())
    logging.info('      Creating content directory')

    os.mkdir(get_output_path())
    logging.info('      Creating output directory')


def make_empty_files():
    logging.info('      Creating empty files')
    with open(get_header_path(), 'w') as f:
        f.write("")
    with open(get_footer_path(), 'w') as f:
        f.write("")

def make_robots_txt():
    body = """# www.robotstxt.org/

# Allow crawling of all content
User-agent: *
Disallow:    """
    robots_path = os.path.join(get_output_path(), "robots.txt")
    with open(robots_path, 'w') as f:
        f.write(body)


def initialize_new_site():
    make_config_file()
    make_site_directories()
    make_robots_txt()
    make_empty_files()


##############################
# Main
##############################

if __name__ == "__main__":
    if args.verbose:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO
    logging.basicConfig(format='%(message)s', level=log_level)

    site_path = args.path

    if args.initialize:
        logging.info('Initializing new site: ' + site_path)

        if os.path.exists(args.path):
            logging.info('  Directory already exits')

        else:
            logging.info('  Creating site directory')
            os.makedirs(site_path)

        if os.listdir(site_path):
            logging.info('  Directory already contains files')
            logging.info('  Initialization caneled')
            exit()
        
        initialize_new_site()
        exit()
    else:
        logging.info('Rendering site: ' + site_path)
        render_site()

        



