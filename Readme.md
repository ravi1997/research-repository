


# Re-initialize the app

```bash
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
```bash
flask run
```
http://127.0.0.1:5000/researchrepository


## Tailwind Utilities


```bash
npm install -D tailwindcss
npx tailwindcss init
```

Add node_modules to .gitignore
```bash
# TAILWIND
node_modules/
```

Edit Tailwind.config.js to look at /app/templates and /app/js

```js
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/templates/**/*.html",
    "./app/static/**/*.js"
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}

```
Create the Input.css for tailwind

```bash
mkdir app/static/src/
touch  app/static/src/input.css
```
edit input.css

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

Start watching the input.css and output the final file


```bash
npx tailwindcss -i ./app/static/src/input.css -o ./app/static/dist/css/output.css --watch
```

Run the app

```python
 python app.py

```

