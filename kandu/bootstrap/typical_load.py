from locust import HttpLocust, TaskSet, task
import time
import uuid
import hashlib
import base64, uuid
import random

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
    self.all_kandus()
    self.random_kandu()
    self.users()
    self.random_user()
    self.get_categories()
    self.signed_policies()
    self.test_authentication()
    self.meta_ping()

  @task(1)
  def register(self):
    resp = self.client.post(
      "/meta/register", {"handle": gen_handle(), "password": "nymphs abuzz"})
    self.user = resp.json()['user']
    self.tok = resp.json()['access_token']['token']
    
  @task(3)
  def users(self):
    resp = self.client.get("/users?_access_token=" + self.tok,
        name="/users?_access_token=[token]")
    self.users = resp.json()['objects']

  @task(3)
  def users_anonymous(self):
    resp = self.client.get("/users")

  @task(1)
  def random_user(self):
    try:
      user = random.choice(self.users)
    except:
      return
    self.client.get(user['url'], name="/users/[random]")
  
  @task(5)
  def all_kandus(self):
    self.kandus = []
    url = "/kandus?_sort=-created_at&_exclude=app_data"
    for i in range(5):
      resp = self.client.get(url,
          name="/kandus?_sort=-created_at&_exclude=app_data [paging]")
      resp_obj = resp.json()
      objs = resp_obj['objects']
      if len(objs) > 0:
        self.kandus.extend(objs)
        url = resp_obj['paging']['next']
      else:
        break

  @task(5)
  def my_kandus(self):
    self.client.get("/kandus?_exclude=app_data&user.href=" + self.user['url'],
        name="/kandus?user.href=[user_url]")

  @task(2)
  def random_kandu(self):
    try:
      kandu = random.choice(self.kandus)
    except IndexError:
      return
    self.client.get(kandu['url'], name="/kandus/[random]")

  @task(1)
  def create_kandu(self):
    d = {'name': 'test kandu', 'app_data': 'TESTING', 'user': self.user['url'],
      '_access_token': self.tok}
    d.update(kandu_data_sig(d))
    self.client.post("/kandus", data=d)

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
  def play_random_kandu(self):
    try:
      kandu = random.choice(self.kandus)
    except IndexError:
      return
    data = {'kandu': kandu['url'], 'user': self.user['url'],
        '_access_token': self.tok}
    self.client.post("/plays", data=data)

  @task(5)
  def fetch_assets(self):
    self.client.get(
        "/assets?updated_at$gte=2000-01-01T00:00:00&_sort=-created_at")

  @task(1)
  def flag_random_kandu_authenticated(self):
    try:
      kandu = random.choice(self.kandus)
    except IndexError:
      return
    data = {'kandu': kandu['url'], 'user': self.user['url'],
        '_access_token': self.tok}
    with self.client.post("/flags", data=data, catch_response=True) as response:
      if response.status_code == 409:
        response.success()

  @task(1)
  def flag_random_kandu_anonymous(self):
    try:
      kandu = random.choice(self.kandus)
    except IndexError:
      return
    data = {'kandu': kandu['url']}
    with self.client.post("/flags", data=data, name="/flags [anon]",
        catch_response=True) as response:
      if response.status_code == 400:
        print response.json()

  @task(2)
  def get_categories(self):
    self.client.get("/categories")

  @task(1)
  def signed_policies(self):
    self.client.get("/signed_policies?ext=png&count=2")

  @task(1)
  def test_authentication(self):
    self.client.get("/meta/test_authentication?_access_token=" + self.tok,
        name="/meta/test_authentication?_access_token=[token]")

  @task(5)
  def meta_ping(self):
    self.client.get("/meta/ping")

class APIUser(HttpLocust):
  task_set = UserBehavior
  min_wait = 5000
  max_wait = 9000

