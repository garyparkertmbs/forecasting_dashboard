create a local postgres database using PG admin
    name = alex, 
    user = alex, 
    password = password 

then, create virtual environment 
    python -m venv env 

then, activate virtual environment 
    ./env/Scripts/activate 

then, install required libraries
    pip install -r requirments.txt 

then, apply all migrations
    python manage.py migrate 

then, run the project
    python manage.py runserver
