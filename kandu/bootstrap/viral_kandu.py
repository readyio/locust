from locust import HttpLocust, TaskSet, task
import time
import base64, uuid, hashlib, random

def gen_handle():
  return base64.b32encode(uuid.uuid4().get_bytes())[:-6].lower()

def kandu_data_sig(request):
  return {
    '_kandu_app_data_signature': hashlib.md5(request['app_data'] + \
        request['_access_token']).hexdigest()
  }

class UserBehavior(TaskSet):
  def on_start(self):
    self.register()
    self.create_kandu()
    self.get_kandus()
    self.like_random_kandu()
    self.play_random_kandu_anon()
    self.flag_random_kandu_anon()

  @task(2)
  def like_random_kandu(self):
    try:
      kandu = random.choice(self.kandus)
    except IndexError:
      return
    data = {'kandu': kandu['url'], 'user': self.user['url'],
        '_access_token': self.tok}
    with self.client.post("/likes", data=data, catch_response=True) as response:
      if response.status_code == 409:
        response.success()

  @task(2)
  def get_kandus(self):
    self.kandus = []
    resp = self.client.get("/kandus?_sort=-created_at&_exclude=app_data")
    resp_obj = resp.json()
    self.kandus = resp_obj['objects']

  @task(1)
  def create_kandu(self):
    d = {'name': 'test kandu', 'app_data': 'TESTING', 'user': self.user['url'],
      '_access_token': self.tok}
    d.update(kandu_data_sig(d))
    self.client.post("/kandus", data=d)

  @task(20)
  def random_kandu(self):
    try:
      kandu = random.choice(self.kandus)
    except IndexError:
      return
    self.client.get(kandu['url'], name="/kandus/[random]")

  @task(15)
  def play_random_kandu_anon(self):
    try:
      kandu = random.choice(self.kandus)
    except IndexError:
      return
    data = {'kandu': kandu['url']}
    self.client.post("/plays", data=data)

  @task(1)
  def flag_random_kandu_anon(self):
    try:
      kandu = random.choice(self.kandus)
    except IndexError:
      return
    data = {'kandu': kandu['url']}
    with self.client.post("/flags", data=data, name="/flags [anon]",
        catch_response=True) as response:
      if response.status_code == 400:
        print response.json()

  @task(1)
  def register(self):
    resp = self.client.post(
      "/meta/register", {"handle": gen_handle(), "password": "nymphs abuzz"})
    self.user = resp.json()['user']
    self.tok = resp.json()['access_token']['token']

  @task(1)
  def meta_ping(self):
    self.client.get("/meta/ping")

class APIUser(HttpLocust):
  task_set = UserBehavior
  min_wait = 5000
  max_wait = 9000
