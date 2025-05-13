from flask import Flask, render_template, redirect, request, url_for, flash , abort 
from flask_sqlalchemy import SQLAlchemy
import os
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user 
from flask_bcrypt import Bcrypt
from functools import wraps
from werkzeug.utils import secure_filename
from datetime import datetime
from flask_restful import Api, Resource
from flask_migrate import Migrate
from flask import jsonify, request
from flask_cors import CORS





from sqlalchemy import ForeignKey, Table, Column, Integer, String, Boolean

basedir = os.path.abspath(os.path.dirname(__file__))

app=Flask(__name__)


app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + \
    os.path.join(basedir, "app.db")
app.config["SQLALCHEMY_TRACK_MODIFICATION"] = False
app.config["SECRET_KEY"] = "Your secret key"
db = SQLAlchemy(app)
login_manager = LoginManager(app)
migrate = Migrate(app, db)

CORS(app) 

bcrypt = Bcrypt(app)
login_manager = LoginManager()


login_manager.init_app(app)


login_manager.login_view = "login"


class User(db.Model, UserMixin):


    _tablename_ = "user"


    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password_hash = db.Column(db.String(100), nullable=False)
    mobile = db.Column(db.String(15), nullable=False)
    role = db.Column(db.String(50), nullable=False, default="user")
    

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")


    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role.lower() == 'admin'



pet_breed = Table('pet_breed', db.Model.metadata,
    Column('pet_id', Integer, ForeignKey('pet.id', ondelete='CASCADE'), primary_key=True),
    Column('breed_id', Integer, ForeignKey('breeds.id', ondelete='CASCADE'), primary_key=True)
)

class Pet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    is_available = db.Column(db.Boolean, default=True)
    image = db.Column(db.String, nullable=True)
    type = db.Column(db.String(50))

    breeds = db.relationship('Breed', secondary='pet_breed', backref='pet_breeds')


class Species(db.Model):
    __tablename__ = 'species'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)

    breeds = db.relationship('Breed', backref='species_relation', lazy=True)

class Breed(db.Model):
    __tablename__ = 'breeds'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)

    species_id = db.Column(db.Integer, db.ForeignKey('species.id'), nullable=False)

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    pet_id = db.Column(db.Integer, db.ForeignKey('pet.id'))
    pet = db.relationship('Pet')

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref='orders')
    pets = db.relationship('Pet', secondary='order_pet', backref='orders')
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Pending')  

order_pet = db.Table('order_pet',
    db.Column('order_id', db.Integer, db.ForeignKey('order.id')),
    db.Column('pet_id', db.Integer, db.ForeignKey('pet.id'))
)




class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)

    def _repr_(self):
        return f"Message from {self.name} - {self.email}"

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        subject = request.form['subject']
        message = request.form['message']

        new_message = ContactMessage(name=name, email=email, subject=subject, message=message)
        db.session.add(new_message)
        db.session.commit()

        return redirect(url_for('home'))  

    return render_template('contactus.html') 


@app.route('/api/messages', methods=['GET'])
def api_get_messages():
    messages = ContactMessage.query.order_by(ContactMessage.sent_at.desc()).all()
    data = [
        {
            'id': msg.id,
            'name': msg.name,
            'email': msg.email,
            'subject': msg.subject,
            'message': msg.message,
            'sent_at': msg.sent_at.isoformat()
        }
        for msg in messages
    ]
    return jsonify(data), 200

@app.route('/api/messages', methods=['POST'])
def api_post_message():
    data = request.get_json()
    try:
        new_msg = ContactMessage(
            name=data['name'],
            email=data['email'],
            subject=data['subject'],
            message=data['message']
        )
        db.session.add(new_msg)
        db.session.commit()
        return jsonify({'message': 'Message saved successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/messages')
def view_messages():
    all_messages = ContactMessage.query.order_by(ContactMessage.sent_at.desc()).all()
    return render_template('view_messages.html', all_messages=all_messages)
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))



with app.app_context():
    db.create_all()

    admin_email = "admin@gmail.com"
    if not User.query.filter_by(email=admin_email).first(): 
        admin_user = User(name="Admin", email=admin_email, mobile="1234567890", role="admin")
        admin_user.set_password("admin123")  
        db.session.add(admin_user)
        db.session.commit()
        print(f"Admin user created: {admin_email} | Password: admin123")

@app.route("/home")
@login_required
def home():
    return  render_template("index.html")

@app.route("/")
def dashboard():
    return render_template("dashboard1.html")

@app.route("/dashboard")
@login_required
def dashboard1():
    return render_template("dashboard.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password) and user.role == role:
            login_user(user)

            flash(f"Logged in as {role}: {email}", "success")

            if role == "admin":
                return redirect(url_for('admin_profile'))
            else:
                return redirect(url_for('user_profile'))
        else:
            flash("Invalid credentials or role mismatch.", "danger")
    
    return render_template('login.html')

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully!", "info")
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        mobile = request.form.get("mobile")

        if password != confirm_password:
            flash("Passwords do not match!", "danger")
            return redirect(url_for("register"))

        if User.query.filter_by(email=email).first():
            flash("Email already exists!", "danger")
            return redirect(url_for("register"))

        new_user = User(name=name, email=email, mobile=mobile)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/user_profile")
@login_required
def user_profile():
    if current_user.role == "admin":  
        return redirect(url_for('admin_profile'))
    else:
        return render_template("user_profile.html", user=current_user)

@app.route("/admin_profile")
@login_required
def admin_profile():
    return render_template("admin_profile.html", user=current_user)

def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if current_user.role != 'admin':
            flash("Access denied!", "danger")
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    return wrapper

@app.route('/add_pet', methods=['GET', 'POST'])
@login_required
@admin_required
def add_pet():
    if request.method == 'POST':
        name = request.form.get('name')
        gender = request.form.get('gender')
        breed_id = request.form.get('breed')
        age = request.form.get('age')
        image = request.form.get('image')
        pet_type = request.form.get('type')

        breed = Breed.query.get(int(breed_id))

        species_name = breed.species_relation.name.lower()
        category = "dog" if "dog" in species_name else "cat"

        new_pet = Pet(
            name=name,
            gender=gender,
            age=int(age),
            image=image,
            type=pet_type
        )
        new_pet.breeds.append(breed)

        db.session.add(new_pet)
        db.session.commit()

        flash(f'{name} has been added successfully!', 'success')
        return redirect(url_for('admin_dashboard'))

    breeds = Breed.query.all()
    return render_template('registerpet.html', breeds=breeds)

@app.route('/addbreed', methods=['GET', 'POST'])
@login_required
@admin_required
def addbreed():
    if request.method == 'POST':
        name = request.form.get('name')
        species_name = request.form.get('species_name')

        if not name or not species_name:
            flash('Both breed name and species name are required.', 'warning')
            return redirect(url_for('addbreed'))

        
        species = Species.query.filter_by(name=species_name).first()
        if not species:
            species = Species(name=species_name)
            db.session.add(species)
            db.session.commit()

       
        new_breed = Breed(name=name, species_id=species.id)
        db.session.add(new_breed)
        db.session.commit()

        flash(f"Breed '{name}' added successfully under species '{species_name}'!", 'success')
        return redirect(url_for('addbreed'))

    
    breeds = Breed.query.all()
    return render_template('addbreed.html', breeds=breeds)

@app.route('/update_breed/<int:breed_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def update_breed(breed_id):
    breed = Breed.query.get_or_404(breed_id)

    if request.method == 'POST':
        new_name = request.form.get('name')
        new_species_name = request.form.get('species_name')

        if not new_name or not new_species_name:
            flash('Breed name and species are required.', 'warning')
            return redirect(url_for('update_breed', breed_id=breed_id))

        species = Species.query.filter_by(name=new_species_name).first()
        if not species:
            species = Species(name=new_species_name)
            db.session.add(species)
            db.session.commit()

        breed.name = new_name
        breed.species = species
        db.session.commit()

        flash('Breed updated successfully!', 'success')
        return redirect(url_for('addbreed'))

    return render_template('update_breed.html', breed=breed)


@app.route('/delete_breed/<int:breed_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def delete_breed(breed_id):
    breed = Breed.query.get_or_404(breed_id)

    if request.method == 'POST':
        try:
            
            for pet in breed.pet_breeds:
                pet.breeds.remove(breed)

            db.session.commit()

            db.session.delete(breed)
            db.session.commit()

            flash(f'Breed "{breed.name}" deleted successfully!', 'success')
            return redirect(url_for('addbreed'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error deleting breed: {str(e)}", 'error')
            return redirect(url_for('addbreed'))

    return render_template('delete_breed.html', breed=breed)


@app.route('/breed_pet_list/<int:breed_id>')
@login_required
@admin_required
def breed_pet_list(breed_id):
    breed = Breed.query.get_or_404(breed_id)

    pets = Pet.query\
        .join(Pet.breeds)\
        .filter(Breed.id == breed_id)\
        .all()

    return render_template('breed_pet_list.html', breed=breed, pets=pets)

@app.route('/admin_dashboard')
@login_required
@admin_required
def admin_dashboard():
    pets = Pet.query.all()
    return render_template('home.html', pets=pets)

about_info = {
    "application_name": "FluffyTails",
    "description": "FluffyTails is dedicated to providing a simple and compassionate platform for pet adoption. Our goal is to connect loving families with pets in need of a home. We understand the special bond between pets and their owners, and we strive to make the adoption process as easy, secure, and joyful as possible.",
    "mission": "At FluffyTails, our mission is to give every pet a chance at a loving and caring home. We aim to educate, support, and empower both pet adopters and shelter organizations. Through our platform, we foster a community of animal lovers who work together to make a difference in the lives of abandoned and neglected animals.",
    "vision": "Our vision is to create a world where every pet has a family, and every family has the tools to care for their pets. We envision a future where pet adoption is the preferred choice for pet ownership, and where animal welfare is prioritized globally. We aim to build a society where the value of compassion and empathy for animals is ingrained in everyday life.",
    "goals": [
        "Increase the number of successful pet adoptions across the world by partnering with trusted animal shelters and adoption centers.",
        "Raise awareness about the importance of adopting pets from shelters rather than buying from breeders or pet stores.",
        "Provide free educational resources for potential pet owners on the responsibilities of owning and caring for a pet.",
        "Support animal shelters by donating a portion of proceeds from every adoption and offering resources to improve shelter conditions.",
        "Create a safe and welcoming environment for pet adopters, where they can learn about the pets, ask questions, and make informed decisions.",
        "Use technology to track pets' adoption progress and ensure that they settle into their new homes with ease."
    ],
    "values": {
        "compassion": "We believe in treating every animal with kindness and respect, ensuring their well-being is always a priority.",
        "community": "We value the power of community. By working together with shelters, rescue groups, and pet owners, we can make a larger impact.",
        "transparency": "We are committed to providing clear and honest information to pet adopters so they can make informed decisions about the animals they welcome into their homes.",
        "sustainability": "We strive to make a positive impact on the environment through sustainable practices in all aspects of our operations."
    },
    "impact": {
        "adopted_pets": 3500,
        "shelters_supported": 50,
        "volunteer_hours": 12000,
        "donations": "$100,000"
    },
    "contact": {
        "email": "fluffytails@example.com",
        "phone": "123-456-7890",
        "address": "123 Pet Lane, Animal City, PA, 12345",
        "social_media": {
            "facebook": "https://facebook.com/fluffytails",
            "twitter": "https://twitter.com/fluffytails",
            "instagram": "https://instagram.com/fluffytails"
        }
    },
    "testimonials": [
        {"name": "John Doe", "message": "Adopting my dog from FluffyTails was a life-changing experience! The team was so helpful and informative. I’m grateful every day."},
        {"name": "Jane Smith", "message": "FluffyTails made the adoption process easy and stress-free. I highly recommend it to anyone looking to adopt a pet."},
        {"name": "Sammy Green", "message": "A fantastic experience from start to finish. The support team helped me find the perfect dog for my family."}
    ],
    "partnerships": [
        {"name": "Happy Paws Shelter", "description": "A local shelter committed to finding homes for abandoned animals. They provide training and rehabilitation for pets."},
        {"name": "Safe Haven Animal Rescue", "description": "A non-profit organization dedicated to rescuing and rehoming animals in need. They focus on providing lifelong care and support to pets."}
    ]
}
@app.route("/aboutus", methods=['GET'])
def aboutus():
    about_info = {
        "application_name": "FluffyTails",
        "description": "FluffyTails is your trusted companion in pet adoption, care, and rescue. We connect loving families with pets in need of a home, while promoting safe, reliable, and compassionate animal care services.",
        "mission": "Our mission is to ensure every pet finds a loving home and to support pet owners with easy access to trusted services like grooming, training, and vet care.",
        "vision": "We envision a world where every pet is treated with love and dignity. Through our intuitive platform, we empower individuals and families to adopt responsibly and care for their furry companions confidently.",
        "goals": [
            "Expand our adoption network and partner with more shelters across the country.",
            "Provide affordable and high-quality pet care services including grooming, vet-on-call, and pet insurance.",
            "Educate the community on responsible pet ownership and promote animal welfare through outreach and events.",
            "Ensure transparency and trust with verified reviews, reservation protection, and 24/7 customer support."
        ],
        "contact": {
            "email": "fluffytails@gmail.com",
            "phone": "9876543210"
        }
    }
    return jsonify(about_info)


@app.route("/aboutus2")
def aboutus2():
    return render_template("aboutus2.html")

@app.route("/adoptingpets")
def adoptingpets():
    return render_template("adoptingpets.html")

@app.route('/cats')
def cats():
    cats = Pet.query.filter_by(type='Cat').all()
    return render_template('cat.html', pets=cats)


@app.route("/catKittenAdoption")
def catKittenAdoption():
    return render_template("catKittenAdoption.html")

@app.route("/dogPuppiesAdoption")
def dogPuppiesAdoption():
    return render_template("dogPuppiesAdoption.html")

@app.route('/dogs')
def dogs():
    pets = Pet.query.filter_by(type='Dog', is_available=True).all()
    return render_template('dog.html', pets=pets)

@app.route("/behaviordog")
def behaviordog():
    return render_template("behavior_dog.html")


@app.route("/behaviorcat")
def behaviorcat():
    return render_template("behavior_cat.html")


@app.route("/learn2.html")
def learn2():
    return render_template("learnmore2.html")

@app.route("/learn3.html")
def learn3():
    return render_template("learnmore3.html")

@app.route("/foundation")
def foundation():
    return render_template("Foundation.html")


@app.route('/add_to_cart/<int:pet_id>', methods=['POST'])
@login_required
def add_to_cart(pet_id):
    pet = Pet.query.get_or_404(pet_id)
    
    
    existing_item = Cart.query.filter_by(user_id=current_user.id, pet_id=pet_id).first()
    if existing_item:
        flash('This pet is already in your cart!', 'warning')
        return redirect(url_for('dogs'))

    new_cart_item = Cart(user_id=current_user.id, pet_id=pet.id)
    db.session.add(new_cart_item)
    db.session.commit()
    
    flash(f'{pet.name} added to your cart!', 'success')
    return redirect(url_for('dogs'))

@app.route('/cart')
@login_required
def cart():
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    return render_template('cart.html', cart_items=cart_items)


@app.route('/remove_from_cart/<int:cart_id>', methods=['POST'])
@login_required
def remove_from_cart(cart_id):
    item = Cart.query.get_or_404(cart_id)

    if item.user_id != current_user.id:
        flash("You can't remove this item!", 'danger')
        return redirect(url_for('cart'))

    db.session.delete(item)
    db.session.commit()
    flash('Item removed from cart.', 'success')
    return redirect(url_for('cart'))





@app.route('/adopt_all_pets', methods=['POST'])
@login_required
def adopt_all_pets():
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()

    if not cart_items:
        flash("Your cart is empty!", "warning")
        return redirect(url_for('cart'))

    pet_ids = [item.pet_id for item in cart_items if item.pet and item.pet.is_available]
    pets = Pet.query.filter(Pet.id.in_(pet_ids)).all()

    if pets:
        new_order = Order(user_id=current_user.id)
        new_order.pets = pets
        db.session.add(new_order)

        for pet in pets:
            pet.is_available = False  

        for item in cart_items:
            db.session.delete(item)

        db.session.commit()
        flash("Adoption order submitted successfully! Awaiting approval.", "success")
    else:
        flash("Some pets are no longer available.", "danger")

    return redirect(url_for('orders'))

@app.route('/orders')
@login_required
def orders():
    if current_user.is_admin:
        orders = Order.query.order_by(Order.order_date.desc()).all()
    else:
        orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.order_date.desc()).all()

        for order in orders:
            if order.status == 'Accepted':
                flash(f"Great news! Your order #{order.id} has been accepted! 🐾", "success")
            elif order.status == 'Rejected':
                flash(f"Sorry! Your order #{order.id} was rejected. 😢", "danger")

    return render_template('orders.html', orders=orders)

@app.route('/order/<int:order_id>/accept')
@login_required
def accept_order(order_id):
    if current_user.role != 'admin':
        abort(403)

    order = Order.query.get_or_404(order_id)
    order.status = 'Accepted'
    db.session.commit()
    flash(f"Order #{order.id} has been accepted.", "success")
    return redirect(url_for('orders'))


@app.route('/order/<int:order_id>/reject')
@login_required
def reject_order(order_id):
    if current_user.role != 'admin':
        abort(403)

    order = Order.query.get_or_404(order_id)
    order.status = 'Rejected'
    db.session.commit()
    flash(f"Order #{order.id} has been rejected.", "warning")
    return redirect(url_for('orders'))

API_TOKEN = 'your_secret_token'

@app.route('/api/orders', methods=['GET'])
def api_get_orders():
    auth_header = request.headers.get('Authorization')
    if auth_header != f"Bearer {API_TOKEN}":
        return jsonify({'error': 'Unauthorized'}), 401

    # Simulate admin access for this trusted token:
    orders = Order.query.order_by(Order.order_date.desc()).all()

    return jsonify([
        {
            "id": order.id,
            "user": order.user.name,
            "status": order.status,
            "date": order.order_date.strftime('%Y-%m-%d %H:%M'),
            "pets": [pet.name for pet in order.pets]
        } for order in orders
    ])

@app.route('/api/orders/<int:order_id>/status', methods=['POST'])
@login_required
def api_update_order_status(order_id):
    if not current_user.is_admin:
        abort(403)

    data = request.get_json()
    new_status = data.get('status')

    if new_status not in ['Accepted', 'Rejected']:
        return jsonify({'error': 'Invalid status'}), 400

    order = Order.query.get_or_404(order_id)
    order.status = new_status
    db.session.commit()

    return jsonify({'message': f'Order {order_id} updated to {new_status}'}), 200

if __name__ == '_main_':
    app.run(debug=True)