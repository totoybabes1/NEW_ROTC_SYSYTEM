# ROTC# ROTC Management System

## Project Description
The ROTC (Reserve Officers' Training Corps) Management System is a web-based application designed to streamline the management of ROTC cadets, attendance tracking, training schedules, and performance evaluations. The system allows administrators to manage cadet records efficiently, generate reports, and ensure smooth communication between cadets and instructors.

## Features
- User authentication (Admin, Cadets, Instructors)
- Cadet profile management
- Attendance tracking
- Event schedule management
- Reports generation

---

## Getting Started
This guide will walk you through setting up a Django project for the ROTC Management System, including creating a virtual environment.

### 1. Install Python
Ensure you have Python installed (preferably Python 3.8+). You can download it from [python.org](https://www.python.org/downloads/).

Check if Python is installed:
```sh
python --version
```

### 2. Set Up a Virtual Environment
A virtual environment helps to manage dependencies for your Django project.

#### Create a Virtual Environment
Run the following command in your project directory:
```sh
python -m venv venv
```

#### Activate the Virtual Environment
- **Windows:**
  ```sh
  venv\Scripts\activate
  ```
- **Mac/Linux:**
  ```sh
  source venv/bin/activate
  ```

To deactivate the virtual environment, use:
```sh
deactivate
```

### 3. Install Django
Once the virtual environment is activated, install Django:
```sh
pip install django
```

Verify the installation:
```sh
django-admin --version
```

### 4. Create a Django Project
Run the following command to create your Django project:
```sh
django-admin startproject myproject . 
```

Navigate to the project directory:
```sh
cd myproject
```

### 5. Run the Development Server
To check if everything is set up correctly, run:
```sh
python manage.py runserver
```

You should see output indicating that the development server is running. Open your browser and go to `http://127.0.0.1:8000/`.

### 6. Create a Django App
Inside your Django project, create an app for managing ROTC records:
```sh
python manage.py startapp myapp
```

Add the app to `INSTALLED_APPS` in `rotc_management/settings.py`:
```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'myapp',
]
```

### 7. Apply Migrations
Run migrations to set up the database:
```sh
python manage.py migrate
```

### 8. Create a Superuser
To access the Django admin panel, create a superuser:
```sh
python manage.py createsuperuser
```
Follow the prompts to set up a username and password.

### 9. Run the Server Again
```sh
python manage.py runserver
```
Now, you can log in to the Django admin panel at `http://127.0.0.1:8000/admin/`.

---

## Next Steps
- Define models for Cadets, Instructors, Attendance, and Training Schedules.
- Create views and templates for user interaction.
- Implement authentication and user roles.
- Develop a dashboard for reporting and tracking cadet progress.

### Contributions
If you'd like to contribute, feel free to fork this repository and submit a pull request!

### License
This project is licensed under the MIT License.

