# WeVolunteer

---

# Developer Setup

Since these directions are mainly for my own reference, they will be MacOS centric.
`$ROOT` refers to the project root directory.

#### 1. Clone the repo and checkout the `master` branch
#### 2. Set up python and install dependencies
The Python versioning and dependencies are managed by [mise-en-place](https://mise.jdx.dev/) and [uv](https://www.google.com/search?client=safari&rls=en&q=uv&ie=UTF-8&oe=UTF-8). It is recommended to install and configure both, but not necessary. It is possible to locate the dependencies from the `uv.lock` and install with `pip`, since there aren't very many.
<br>When you have mise and uv set up, install Python and the dependencies with
```bash
uv python install 3.13.2 # Uses uv to install a prebuilt Python
mise sync python --uv    # Tells mise to use the uv-provided Python
mise install             # Installs tools specified in $ROOT/.mise.toml
cd ..                    # Leave the directory
cd $ROOT                 # and re-enter to invoke mise's auto venv activation
uv sync                  # Use uv to create the venv and install the Python dependencies specified in
                         #   pyproject.toml and uv.lock
```

#### 3. Create `.env` dev file
This project manages environment variables with `.env` files, which are not tracked by git.
<br>Add a new file titled `.env.dev` in `$ROOT` with the following contents:
```
SECRET_KEY = '<insecure development key>'
DEBUG = 'True'
DJANGO_ALLOWED_HOSTS="*"
DJANGO_CSRF_TRUSTED_ORIGINS='http://localhost:8000'

DATABASE_NAME = 'WeVolunteer'
DATABASE_USER = 'WeVolunteer'
DATABASE_PASSWORD = 'WeVolunteer'
DATABASE_HOST = 'localhost'
DATABASE_PORT = '5432'
```

#### 4. Install Postgres and configure database
You can install Postgres by installing the application [here](https://postgresapp.com/).
<br>Make sure the developer tools are added to your path, they are usually located in `/Applications/Postgres.app/Contents/Versions/16/bin`.
```
# ~/.bashrc or ~/.zshrc
export PATH="/Applications/Postgres.app/Contents/Versions/16/bin:$PATH"
```

<br>Create the developer db user and instance with
```
createuser --superuser --pwprompt <password> WeVolunteer 
createdb --owner WeVolunteer WeVolunteer
```
`cd` into the directory with `manage.py` and run database migrations with
```
python manage.py migrate
```

#### 5. Download Bootstrap and Bootstrap Icons
Download the compiled Boostrap files located [here](https://getbootstrap.com/docs/5.3/getting-started/download/), and the Bootstrap Icons [here](https://icons.getbootstrap.com/#install).
Make new directories for the Bootstrap files with
```
mkdir $ROOT/WeVolunteer/static/boostrap
mkdir $ROOT/WeVolunteer/static/bootstrap/icons
```
Move the `css` and `js` directories from the Bootstrap dist folder into `$ROOT/WeVolunteer/static/boostrap`.
<br>Unzip the Bootstrap Icons folder and move its contents to `$ROOT/WeVolunteer/static/bootstrap/icons`.
<br><br>In lieu of downloading Bootstrap, it is also acceptable to use [CDN](https://getbootstrap.com/docs/5.3/getting-started/introduction/). Replace the `stylesheet` links in the `base_header.html` template with references links to CDN instead of local static paths.

#### 6. Download Datastar
Download the Datastar bundle [here](https://data-star.dev/bundler) by clicking the "All" button to include all modules, then the "Bundle" button.
Make a new directory for the Datastar bundle with
```
mkdir $ROOT/WeVolunteer/static/datastar
```
Move the contents of the unzipped Datastar download folder into `$ROOT/WeVolunteer/static/datastar`.

#### 7. Try it out!
Run
```
python manage.py runserver
```
Navigate to http://127.0.0.1:8000 to view the application!