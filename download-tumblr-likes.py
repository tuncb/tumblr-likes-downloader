import pytumblr
import argparse
import urllib3
import os
import colorama

ERASE_LINE = "\033[K"

def gather_likes(client):
  MAX_AVALIBLE_LIKES_LIMIT = 1000
  nr_available_likes = min(client.likes()["liked_count"], MAX_AVALIBLE_LIKES_LIMIT)
  total_likes_gathered = 0
  all_likes = []

  likes = client.likes(offset = total_likes_gathered)["liked_posts"]
  while len(likes) > 0 and total_likes_gathered < nr_available_likes:
    total_likes_gathered += len(likes)
    all_likes.extend(likes)
    print("{}Gathered #{} likes".format(ERASE_LINE, len(all_likes)), end="\r")
    likes = client.likes(offset = total_likes_gathered)["liked_posts"]

  print("")
  return all_likes

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
  likes = gather_likes(client)
  if len(likes) == 0:
    print("No likes could be gathered")
    return []

  photo_likes = filter(lambda like: like['type'] == 'photo', likes)
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
  print("")
  return likes

def unlike(client, likes, restore_filename):
  with open(restore_filename, "a") as text_file:
    count = 1
    for like in likes:
      id, reblog_key = (like["id"], like["reblog_key"])
      print("{} {}".format(id, reblog_key), file=text_file)
      client.unlike(id, reblog_key)
      print("{}Unliked #{}".format(ERASE_LINE, count), end="\r")
      count += 1
  
  print("")
  return likes

def like(client, restore_filename):
  with open(restore_filename, "r") as text_file:
    lines = text_file.readline
  
  count = 1
  for line in lines:
    id, reblog_key = line.split(" ")
    client.like(id, reblog_key)
    print("{}Liked #{}".format(ERASE_LINE, count), end="\r")
    count += 1

  print("")


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("folder", help="folder to save liked photos")
  parser.add_argument("consumer_key", help="consumer key for the Tumblr blog")
  parser.add_argument("consumer_secret", help="consumer secret for the Tumblr blog")
  parser.add_argument("oauth_token", help="oauth token for the Tumblr blog")
  parser.add_argument("oauth_token_secret", help="oauth token secret for the Tumblr blog")
  parser.add_argument("--unlike", help="unlikes processed likes, saves restore information to unliked.txt", action="store_true")
  parser.add_argument("--like", help="likes unliked posts stored in unliked.txt", action="store_true")
  args = parser.parse_args()

  colorama.init()
  urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

  client = pytumblr.TumblrRestClient(
    args.consumer_key,
    args.consumer_secret,
    args.oauth_token,
    args.oauth_token_secret
  )

  if args.like:
    like(client, "{}\\unliked.txt".format(args.folder))
    return

  likes = save_photo_likes(client, args.folder)
  if (args.unlike):
    unlike(client, likes, "{}\\unliked.txt".format(args.folder))

if __name__ == "__main__":
  main()