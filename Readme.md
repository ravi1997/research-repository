


# Re-initialize the app

```
flask empty-db
rm -r migrations
rm app/app.db
flask db init
flask db migrate
flask db upgrade
flask seed-db
```
default 


# Run
```
flask run
```


http://127.0.0.1:5000/researchrepository