# Cherry Michelle's Cakes & Pastries — Custom Ordering System

## 🎂 Setup on PythonAnywhere

### Step 1: Upload the project
Upload this folder to PythonAnywhere via the Files tab (or use git).

### Step 2: Create a virtual environment
In a PythonAnywhere Bash console:
```bash
mkvirtualenv --python=python3.10 cakery_env
pip install -r requirements.txt
```

### Step 3: Set up the database
```bash
cd /home/yourusername/cakery_project
python manage.py migrate
python manage.py createsuperuser
```

### Step 4: Collect static files
```bash
python manage.py collectstatic
```

### Step 5: Configure Web App on PythonAnywhere
1. Go to the **Web** tab → Add new web app → Manual configuration → Python 3.10
2. Set **Source code**: `/home/yourusername/cakery_project`
3. Set **Virtualenv**: `/home/yourusername/.virtualenvs/cakery_env`
4. Edit **WSGI file** — replace contents with:

```python
import os
import sys
path = '/home/yourusername/cakery_project'
if path not in sys.path:
    sys.path.insert(0, path)
os.environ['DJANGO_SETTINGS_MODULE'] = 'cakery.settings'
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

5. **Static files** mapping:
   - URL: `/static/` → Directory: `/home/yourusername/cakery_project/staticfiles`
   - URL: `/media/` → Directory: `/home/yourusername/cakery_project/media`

### Step 6: Update settings.py for production
```python
DEBUG = False
SECRET_KEY = 'your-new-random-secret-key-here'
ALLOWED_HOSTS = ['yourusername.pythonanywhere.com']
```

### Step 7: Reload the web app
Click **Reload** on the Web tab. Visit `yourusername.pythonanywhere.com`!

---
## 🔑 Default Login
After running `createsuperuser`, use those credentials to log in at `/login/`

## 📱 Features
- Dashboard with live stats
- Order management (full CRUD)
- Customer database
- Cake menu management  
- Production scheduling
- Payment tracking
- Staff management
- Django admin panel at `/admin/`
