import typer
from app.database import create_db_and_tables, get_cli_session, drop_all
from app.models.user import *
from fastapi import Depends
from sqlmodel import select
from sqlalchemy.exc import IntegrityError
from app.models.user import User
from app.utilities.security import encrypt_password

# typer is the library we use for the cli. Because there was only one typer command, it treats it as the default command, so we can run it without any arguments and it will execute the initialize function. If we had multiple commands, we would need to specify which one to run.
cli = typer.Typer()

@cli.callback()
def main():
    """Empty command."""
    return None

@cli.command()
def initialize():
    with get_cli_session() as db:
        drop_all() 
        create_db_and_tables() 
        
        bob = UserBase(username='bob', email='bob@mail.com', password=encrypt_password("bobpass"))
        bob_db = User.model_validate(bob)

        db.add(bob_db)
        db.commit()        
        print("Database Initialized")
    

if __name__ == "__main__":
    cli()