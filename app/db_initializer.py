

from app.models import User
from app.extension import db
import click
from flask import current_app as app

@click.command('empty-db')
def empty_db_command():
	"""Drop and recreate the database."""
	drop_database()
	click.echo('Deleted and Recreated the empty database. '
			   'Run --- '
			   'flask db init, '
			   'flask db migrate, '
			   'flask db upgrade')


@click.command('seed-db')
def seed_db_command():
	"""Seed the database with initial data."""
	create_user_guest()
	click.echo('Seeded the database.')


def drop_database():
	"""Drop and recreate database schema."""
	db.reflect()
	db.drop_all()
	db.create_all()
	click.echo('Database dropped and recreated.')

def create_user_guest():
	"""Create a sample user."""
	try:
		existing_user = User.query.filter_by(firstname="RAVINDER", employee_id="E9999999").first()
		if not existing_user:
			new_user = User(
				firstname='RAVINDER',
				middlename='',
				lastname='SINGH',
				employee_id="E9999999",
				email="ravi199777@gmail.com",
				mobile="9899378106",
			)
			db.session.add(new_user)
			db.session.commit()
			
			app.logger.info("User Ravinder Singh Added.")
		else:
			app.logger.info("User Ravinder Singh already exists.")


		existing_user = User.query.filter_by(firstname="GUEST", employee_id="E0000000").first()
		if not existing_user:
			new_user = User(
				firstname='GUEST',
				middlename='',
				lastname='',
				employee_id="E0000000",
				email="guest123@mail.com",
				mobile="9999999999",
			)
			db.session.add(new_user)
			db.session.commit()
			
			app.logger.info("User Guest Added.")
		else:
			app.logger.info("User Guest already exists.")



	except Exception as e:
		app.logger.error(f"Error creating user: {str(e)}")
		db.session.rollback()
		raise