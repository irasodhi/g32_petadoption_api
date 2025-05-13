# 🐶 Pet Adoption Platform

A full-stack web application for adopting pets, built with *Django* for the frontend/backend and a *Flask-based REST API* for handling data operations and user authentication with JWT.

---

## 🌟 Project Overview

This project allows users to:
- Browse available pets
- Register and log in securely (using JWT)
- Add new pets for adoption
- Adopt a pet and view adoption details

The backend logic and data are managed through a Flask API, while Django handles page rendering, form submissions, and user interface.

---

## 🛠 Tech Stack

| Frontend            | Django + HTML + Bootstrap |
| Backend             | Flask (REST API)                      |
| Authentication| JWT (JSON Web Token)        |      
| Database           | SQLite (or configurable)      |
| Language           | Python                                          |

---

## 🚀 Features

- 🔐 *User Authentication* 
- 🐾 *Pet Registration* with name, breed, and species
- 📋 *Pet Listings* displayed as responsive cards
- 🛒 *Adoption Cart & Orders* system 
- 📡 *API Integration* using requests to fetch/post between Django and Flask

---

## 🔧 Setup Instructions
Follow these steps to set up the Pet Adoption Platform on your local machine.

### 
1. Clone the Repository
https://github.com/irasodhi/g32_petadoption_api

2. Create and Activate Virtual Environment
python -m venv env
source env/bin/activate        # Linux/Mac
env\Scripts\activate               # Windows
3. Install Dependencies
pip install -r requirements.txt
4. Run Flask API Server
cd flask_api
python app.py
5. Run Django Frontend
cd django_frontend
python manage.py runserver
 6. Access the Application
•	Visit: http://localhost:8000/
•	Browse pets, register users, and interact with the Flask-powered API