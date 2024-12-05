


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


Git Workflow

vivek 
```bash
git branch -a
git remote show origin
git checkout main # Latest code from server
git pull

git branch -D vg1 # Detach / delete preexisting local branch desktop
git push origin --delete vg1 # Detach / delete preexisting REMOTE branch desktop

git branch vg1 # Recreate a local  branch
git checkout vg1 # Start working with t lcoal branch
git branch -a # List all branches and remotes
# Make changes to code

git status
git add .
git commit  -m "Changed dark mode settings - Tailwind use slectpor strategy and sun icon on footer. Classes on BODY tag and base styles"
git status
# Push local branch code to remote
git push -u origin vg1 
# merge desktop with main on GitHub
# Delete remote  desktop on GitHub


```

