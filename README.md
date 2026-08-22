# Trekking Management Application

A web-based Trekking Management Application developed using Flask, Jinja2, Bootstrap, and SQLite. The application provides role-based functionality for Admins, Trek Staff, and Trekkers to manage treks, staff assignments, bookings, and trekking history.

## Technologies Used

* **Backend:** Flask
* **Frontend:** HTML, CSS, Jinja2, Bootstrap
* **Database:** SQLite
* **ORM:** Flask-SQLAlchemy
* **Authentication:** Flask-Login
* **Password Security:** Werkzeug password hashing

## User Roles

### Admin

* Manage treks
* Create, edit, and delete eligible treks
* Approve and blacklist trek staff
* Assign staff to treks
* View users, staff, treks, and bookings
* Search users, staff, and treks
* Blacklist users and staff
* View booking and trekking history

### Trek Staff

* Register and log in
* Access the dashboard after Admin approval
* View assigned treks
* Update available slots and trek status
* View registered participants
* Mark treks as started or completed

### Trekker

* Register and log in
* View approved and open treks
* Search and filter treks
* Book treks
* Cancel bookings
* View booking status
* View trekking history
* Edit profile

## Key Features

* Role-based authentication and authorization
* Admin approval for Trek Staff
* Staff assignment to treks
* Prevention of overbooking
* Prevention of duplicate active bookings
* Booking cancellation with slot restoration
* Complete booking history preservation
* Trek status management
* Search and filtering of treks
* Search of users, staff, and treks by name or ID
* Protection against unauthorized staff management
* Treks with existing booking history cannot be deleted

## Database

The application uses **SQLite** and creates the database programmatically using SQLAlchemy.

The main entities are:

* Users
* Staff Profiles
* Treks
* Bookings

No manual database creation is required.

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd <project-folder>
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the application

```bash
python app.py
```

The SQLite database is created automatically when the application is initialized.

### 4. Open the application

Open the local Flask URL shown in the terminal, typically:

```text
http://127.0.0.1:5000
```

## Default Admin

The application creates a default Admin account programmatically when the application is initialized.

The default Admin credentials are configured inside the application's initialization code.

## Academic Project

This project was developed as part of the **IITM BS Degree – Modern Application Development I (MAD-1)** project.

The application follows the specified requirements of Flask, Jinja2, HTML/CSS, Bootstrap, and SQLite.
