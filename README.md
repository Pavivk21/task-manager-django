# Task Manager Django

![Made with Django](https://img.shields.io/badge/Made%20with-Django-092E20?style=for-the-badge&logo=django&logoColor=white)

> A modern, responsive Django web application to efficiently manage personal or collaborative tasks. Built with PostgreSQL, Django Auth, and Bootstrap for clean UI.




## Features

-  User Registration & Authentication
-  Create / Update / Delete Tasks
-  Task Filtering (All, Completed, Pending, Today, This Week)
-  Calendar Date Picker
-  Task Reminders
-  Summary Dashboard with Charts (using Chart.js)
-  Profile Page with Stats
-  Responsive UI with Bootstrap
-  SQLite by default / Optional PostgreSQL support

---

## Technologies Used

- Python 3.x
- Django 4.x
- PostgreSQL or SQLite
- HTML, CSS, Bootstrap 5
- Chart.js for analytics

---

##  Getting Started

###  Clone this repository
```bash
git clone https://github.com/Pavivk21/task-manager-django.git
cd task-manager-django
```

###  Set up virtual environment
```bash
python3 -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
```

###  Install dependencies
```bash
pip install -r requirements.txt
```

###  Apply migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

###  Run the server
```bash
python manage.py runserver
```

Visit: `http://127.0.0.1:9000/`

---

## Project Structure

```
task_manager_project/
├── taskmanager/           # Main settings
├── tasks/                 # App for task management
│   ├── templates/tasks/   # HTML Templates
│   ├── static/            # CSS/JS if added
├── manage.py
├── requirements.txt
└── README.md
```

---

## Author

**Pavithra Vijaykumar**  
GitHub: [@Pavivk21](https://github.com/Pavivk21)

---

## License

This project is open-source and free to use under the MIT License.
