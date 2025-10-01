# Getting Started - Development


## For development
### Set up groups and folders
```
sudo make dev-install
```


### SSL Certificate
To ensure security when entering your credentials you will need a certificate. One of the easiest ways to get one for local developemnt is to use mkcert, or for public urls use let's encrypt. 

Then store them in 

```
/etc/dbcalm/ssl/fullchain-cert.pem
/etc/dbcalm/ssl/private-key.pem
```

### Run the API
As there are 2 parts that need watching (a cmd server) 


```
make dev
```


### Add Users

To add new users run ./dbcalm-users.py
