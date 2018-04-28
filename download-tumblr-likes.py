import pytumblr
import argparse
import urllib3
import os
import colorama

def generate_likes(client):
  MAX_AVALIBLE_LIKES_LIMIT = 1000
  nr_available_likes = min(client.likes()["liked_count"], MAX_AVALIBLE_LIKES_LIMIT)
  total_likes_gathered = 0
  while total_likes_gathered < nr_available_likes:
    likes = client.likes(offset = total_likes_gathered)["liked_posts"]
    total_likes_gathered += len(likes)
    for like in likes:
      yield like

def generate_photo_urls(photo_likes):
  for like in photo_likes:
    photos = like["photos"]
    for photo in photos:
      url = photo["original_size"]["url"]
      yield url

def download_file(url, path):
  CHUNK_SIZE = 65536
  http = urllib3.PoolManager()
  response = http.request('GET', url, preload_content=False)
  with open(path, 'wb') as out:
    while True:
      data = response.read(CHUNK_SIZE)
      if not data:
        break
      out.write(data)
  response.release_conn()

def save_photo_likes(client, folder):
  colorama.init()
  ERASE_LINE = "\033[K"

  photo_likes = filter(lambda like: like['type'] == 'photo', generate_likes(client))
  count = 1
  for url in generate_photo_urls(photo_likes):
    filename = url.split('/')[-1]
    pathname = "{}\\{}".format(folder, filename)
    if (os.path.isfile(pathname)):
      print("{}Photo #{} already exists: {}".format(ERASE_LINE, count + 1, filename), end="\r")
    else:
      print("{}Downloading photo #{}: {}".format(ERASE_LINE, count + 1, filename), end="\r")
      download_file(url, pathname)
    count += 1
  return (count, photo_likes)

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("folder", help="folder to save liked photos")
  parser.add_argument("consumer_key", help="consumer key for the Tumblr blog")
  parser.add_argument("consumer_secret", help="consumer secret for the Tumblr blog")
  parser.add_argument("oauth_token", help="oauth token for the Tumblr blog")
  parser.add_argument("oauth_token_secret", help="oauth token secret for the Tumblr blog")
  args = parser.parse_args()

  client = pytumblr.TumblrRestClient(
    args.consumer_key,
    args.consumer_secret,
    args.oauth_token,
    args.oauth_token_secret
  )

  urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
  #while save_photo_likes(client, args.folder) > 0:
  save_photo_likes(client, args.folder)

if __name__ == "__main__":
  main()