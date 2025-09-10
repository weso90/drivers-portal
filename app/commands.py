import click
from flask import current_app as app
from app import db
from app.models import User


#utworzenie konta administratora za pomocą komendy:
    #flask create-admin nazwa-administratora hasło-administratora
    
@app.cli.command("create-admin")
@click.argument("username")
@click.argument("password")
def create_admin(username, password):
    """Tworzy nowego administratora."""
    if User.query.filter_by(username=username).first():
        print(f"Użytkownik {username} już istnieje.")
        return
    
    admin = User(username=username, role='admin')
    admin.set_password(password)
    db.session.add(admin)
    db.session.commit()
    print(f"Administrator {username} został pomyślnie utworzony.")
