from locust import HttpLocust, TaskSet, task
import time
import base64, uuid

def gen_handle():
  return base64.b32encode(uuid.uuid4().get_bytes())[:-6].lower()

class UserBehavior(TaskSet):
  def on_start(self):
    self.register()

  @task(10)
  def register(self):
    resp = self.client.post(
      "/meta/register", {"handle": gen_handle(), "password": "nymphs abuzz"})
    self.user = resp.json()['user']
    self.tok = resp.json()['access_token']['token']

  @task(1)
  def test_authentication(self):
    self.client.get("/meta/test_authentication?_access_token=" + self.tok,
        name="/meta/test_authentication?_access_token=[token]")

  @task(1)
  def meta_ping(self):
    self.client.get("/meta/ping")

  @task(1)
  def users_anonymous(self):
    resp = self.client.get("/users")

class APIUser(HttpLocust):
  task_set = UserBehavior
  min_wait = 5000
  max_wait = 9000

