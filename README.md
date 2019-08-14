# Yandex-service-imports
Yandex second task. Realization of imports service

## Install and run project
### Preinstallations
Firstly, be sure of updating apt-get package lists:
```
$ sudo apt-get update
```
And check your python version (should be 3.6):
```
$ python3 -V
```
This project uses PostgreSQL (v 10.10 or later) so install it by:
```
$ sudo apt-get install postgresql
$ sudo apt-get install postgresql-server-dev-all
```
> Note: If you have problem with downloading, please visit [official PostgreSQL page](https://www.postgresql.org/download/)

Then create your own postgres user and database for project. Firstly get an interactive login shell for user postgres (main PostgreSQL user):
```
$ sudo -u postgres -i
```
then run 
```
$ psql
```
which open PostgreSQL interactive terminal. Thereafter create our PostgreSQL user with createdb privileges (for tests) and our database:
```sql
create user your_username with password ‘your_password’ createdb;
create database your_database_name owner your_username;
```
> Note: You can change your_username, your_password and your_database_name by whatever you want (in my case it will be alex, alex, yandex).

Exit PostgreSQL interactive terminal and interactive login shell:
```
\q
$ exit
```
Now, install pip (standard package-management system for installing and managing Python packages):
```
$ sudo apt-get install python3-pip
```
And then install virtualenv (tool for isolate our projects’s external dependencies):
```
$ sudo pip3 install virtualenv
```
### Cloning, install and run project
For cloning project from github install git:
```
$ sudo apt-get install git
```
and clone project in any folder:
```
$ git clone https://github.com/BiggiPiggi/Yandex-service-imports
```
Go to the project folder, create virtual environment and activate it:
```
$ cd Yandex-service-imports
$ virtualenv venv
$ source venv/bin/activate
```
> Note: To exit from virtual environment write `(venv) $ deactivate`

Now install project extend dependencies:
```
(venv) $ pip3 install -r requirements.txt
```
Then open Yandex/settings.py file and change settings in “DATABASES” block to yours, which you specified above (name, user, etc). 
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'yandex',
        'USER': 'alex',
        'PASSWORD': 'alex',
        'HOST': '127.0.0.1',
        'PORT': '5432'
    }
}
```
Then add your server’s public ip to ALLOWED_HOSTS:
```python
ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'some.your.ip']
```
After that, let django to create required database tables. For that go to the main project folder (Yandex-service-imports) and type:
```
(venv) $ python3 manage.py makemigrations imports
(venv) $ python3 manage.py sqlmigrate imports 0001
(venv) $ python3 manage.py migrate
```
Now try to run project to check that all is good:
```
(venv) $ gunicorn -c gunicorn.conf.py Yandex.wsgi:application
```
If all is good in log/error.gunicorn.log you’ll see:
```
[2019-08-13 14:46:14 +0000] [11083] [INFO] Starting gunicorn 19.9.0
[2019-08-13 14:46:14 +0000] [11083] [INFO] Listening at: http://0.0.0.0:8080 (11083)
[2019-08-13 14:46:14 +0000] [11083] [INFO] Using worker: sync
[2019-08-13 14:46:14 +0000] [11086] [INFO] Booting worker with pid: 11086
[2019-08-13 14:46:14 +0000] [11088] [INFO] Booting worker with pid: 11088
[2019-08-13 14:46:14 +0000] [11089] [INFO] Booting worker with pid: 11089
```
Now our service available in browser on 8080 ports.

### Run tests
Now, run tests checking that internal logic works as we need (you must be in the main project folder: Yandex-service-imports):
```
(venv) $ python3 manage.py tests
```
If all is OK, you'll see something like this:
```
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
.Birth_Date - 0.151621
......Change - 0.538451
...Get - 0.145399
.....Add - 0.959776
......Percentile - 0.121545
..
----------------------------------------------------------------------
Ran 23 tests in 12.202s

OK
Destroying test database for alias 'default'...
```
### Install and configure supervisor
Lets install and configure supervisor to allow more control over our project (e.g. autostart and autorestart). Note that you must be not in virtual environment.
```
$ sudo apt-get install supervisor
```
Now create an executable bash script to run gunicorn. Firstly create text file with the following content and put it in any folder :
```bash
cd /home/user_name/path/to/project/Yandex-service-imports
source venv/bin/activate
exec gunicorn -c gunicorn.conf.py Yandex.wsgi:application
```
> Note: Provide full path to the main project folder in the first line.

Then make new created file executable:
```
$ chmod +x new_executable_filename
```
Next, we’ll configure supervisor. For that, change directory to **/etc/supervisor/conf.d**. Here create file **supervisord.conf** with the following content:
```
[inet_http_server]
port=0.0.0.0:8081

[supervisord]
logfile=/var/log/supervisor/supervisord.log
loglevel=debug

[program:imports]
command=/bin/bash /absolute/path/to/executable/file/create/above/executable_filename
autostart=true
autorestart=true
stderr_logfile=/var/log/supervisor/imports.err.log
stdout_logfile=/var/log/supervisor/imports.out.log
stopsignal=KILL
stopasgroup=true
killasgroup=true
startsecs=0

[supervisorctl]
serverurl=unix:///var/run/supervisor.sock
```
> Note: For more information about supervisor configuration, please, visit [supervisor official page](http://supervisord.org/configuration.html)

Now let start our project via supervisor:
```
$ sudo supervisorctl reread
$ sudo supervisorctl start imports
```
To check status of project write:
```
$ sudo supervisorctl status imports
```
And if all is well you will see 
```
imports                          RUNNING   pid 12081, uptime 0:02:11
```
> Note: If there is some problem with starting project via supervisor (e.g. ERROR no such process) try to reload supervisor: `sudo supervisorctl reload` and start again).
