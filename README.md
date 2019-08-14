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
which open PostgreSQL interactive terminal. Thereafter create our PostgreSQL user with createdb privileges (for tests):
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
