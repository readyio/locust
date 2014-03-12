#Load-testing the API

This load-testing suite is based on [Locust](http://locust.io) and
[locust-swarm](https://github.com/ryankanno/locust-swarm). I've made some
modifications to locust-swarm to better support a more flexible workflow; see
the git commit log for more info. In this document, I'll describe the
capabilities of this load testing suite and give examples of how to use it.

##Basic structure

With these scripts, you can easily bring up a "swarm" of EC2 machines, each
running an instance of Locust. (One is configured as a "master" and the others
as "slaves".) The files in `kandu/bootstrap` are uploaded to each of the
machines after they're created; `kandu/bootstrap/bootstrap.sh` gets run by the
root user. Any other files in `kandu/bootstrap` will be copied into a temporary
directory on the remote server--in particular, the same directory where the
locust process will later run.

Once the machines are created and bootstrapped, you can run a locust file on
them using the `run` command (see below). Any locust file you've included in
the bootstrap directory can be run in this way.

Once the master and slave locust processes are running, you'll be able to
access the HTTP interface of the master machine by going to port 8089 in a web
browser. You can start the load testing process from there, specifying the
number of users and spawn rate, and watch as the results arrive in real-time.

##Included locust files

There are three locust files already included in this distribution, which I
wrote to approximate three different kinds of load on the API. They are as
follows:

* `signups.py`: simulates a scenario in which many users sign up for Kandu. In particular, this locust file exercises the `/meta/register` endpoint (the most CPU-intensive part of the API).
* `viral_load.py`: simulates a scenario in which one (or several) kandus "go viral"--i.e., a lot of GETs to URLs of particular kandus, plus heavy load on POSTs relating to the playing process (`/plays`, `/flags`, etc).
* `typical_load.py`: my approximation of "typical load" on Kandu--a combination of registrations, saving kandus, playing kandus, fetching assets, etc.

You can easily use these locust files as templates to create your own
scenarios. Just create the locust file and include it in the `bootstrap`
directory when you're creating a new locust swarm. Here's [more information
about writing locust files](http://docs.locust.io/en/latest/quickstart.html).

##Running a load test

This suite is a fork of
[locust-swarm](https://github.com/ryankanno/locust-swarm), and most of the
instructions that apply to the base project also apply to this fork. I added a
few features (the "run" and "killall" command), which I'll discuss in context
below.

Before you begin, customize the `locust-swarm.cfg` file to suit your needs; see
the locust-swarm documentation for details. You'll need to have an
`access_key_id` and `secret_access_key` that have permission on AWS to create
new EC2 instances. The `aws_key_name` field refers to the name of the Key Pair
in the EC2 interface, while the `key_filename` field should contain a path to
the actual private key for that pair. (You probably downloaded this from the
EC2 management console when creating the keypair--it's a file ending in
`.pem`.)

Running a load test consists of four steps: (1) bringing the stack "up"; (2)
running locust; (3) killing the locust process and restarting with a new locust
file/host (rinse and repeat); (4) bringing the stack "down." We'll review each
of these steps in detail below!

(1) Bring the master up. Do this with the following command:

	$ python locust-swarm/swarm.py up master -c ./locust-swarm.cfg -d kandu/bootstrap

Wait until the master has been created and bootstrapped (this could take several
minutes). When complete, bring up the slaves, like so:

	$ python locust-swarm/swarm.py up slaves -c ./locust-swarm.cfg -d kandu/bootstrap -s <num>

... replacing `<num>` with the number of machines you want to create. (If
unspecified, this will default to 5.) This will also take a few minutes. (The
slave machines are created/bootstrapped simultaneously, so it shouldn't take
any longer than it took to bring up the master.)

Congratulations, you have a locust swarm! But nothing's running on the machines yet. Let's proceed to step 2.

(2) Run locust on the master. Here's the command:

	$ python locust-swarm/swarm.py run master \
	  -c ./locust-swarm.cfg -d kandu/bootstrap \
	  -H <host> -f <locust file>

Replace `<host>` above with the URL of the stack you want to load test (e.g.,
the URL of the load balancer of the web stack) and `<locust file>` with the
locust file you want to run. (The locust file will need to have been included
in the bootstrapping process; see "Included locust files" above.)

Do the same thing on the slave machines:

	$ python locust-swarm/swarm.py run slaves \
	  -c ./locust-swarm.cfg -d kandu/bootstrap \
	  -H <host> -f <locust file>

... making the same replacements.

You should now be able to go to `http://<hostname of master machine>:8089` in a
web browser and start a load test. (You may need to check the EC2 management
console to find out the master's hostname.)

(3) If you want to change the host you're load testing, or the locust file
you're load testing with, first you need to kill the currently running locust
process. Run this command to kill locust on the master:

	$ python locust-swarm/swarm.py killall master -c ./locust-swarm.cfg

... and this command to do the same on the slaves:

	$ python locust-swarm/swarm.py killall slaves -c ./locust-swarm.cfg

Once you've done this, you can execute the commands in step (2) to run locust
again with a new host or locust file.

(4) Once you're done load testing, you should bring the load testing stack down
(to avoid unnecessary EC2 fees!). Bring the master down like this:

	$ python locust-swarm/swarm.py down master -c ./locust-swarm.cfg

... and the slaves like this:

	$ python locust-swarm/swarm.py down slaves -c ./locust-swarm.cfg

##Caveats and notes

* Don't try to bring up more than one stack in an EC2 region. The locust-swarm tool doesn't create unique names for each stack, so it could potentially get confused about what machine you mean by "master."

* I found that t1.micro instances were more than sufficient for both master and slave locust machines, even when running hundreds (500+) of simultaneous users. But depending on the structure of your locust files, you may want to keep an eye on CPU usage on the slave machines. Otherwise, you might think the API stack is slow, when in fact the bottleneck is the swarm!

* You may want to fiddle with the `min_wait` and `max_wait` parameters in the locust files. When doing load tests before bringing up the first production web stack, I intentionally gave these parameters generous values, potentially at the cost of not really pushing the web stack and far as it can go.

