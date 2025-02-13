

from datetime import datetime
import json
from marshmallow import ValidationError
from app.models import User
from app.models.user import UserRole, UserRoles
from app.mylogger import*
from app.extension import db
import click
from flask import current_app as app

from app.schema import ArticleSchema
from app.utility import fileReader

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
	create_user_superadmin()
	create_user_Faculty()
	click.echo('Seeded the database.')


@click.command('test')
def test_command():
	try:
		filepath = 'doc/pubmed-35225509 - single.nbib'
	
		myjson = fileReader(filepath=filepath)

		schema = ArticleSchema(many=True)
		objects = schema.load(myjson)
		for object in objects:
			db.session.add(object)
		db.session.commit()
		print( json.dumps(myjson, indent=4))
	except ValidationError as e:
		print(json.dumps(e.messages, indent=4))


def drop_database():
	"""Drop and recreate database schema."""
	db.reflect()
	db.drop_all()
	db.create_all()
	click.echo('Database dropped and recreated.')


def create_user_superadmin():
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
				department= "RPC",
				designation="Programmer",
				date_expiry= datetime(2057, 2, 28),
				roles= [UserRoles(role=UserRole.SUPERADMIN)]
			)
			db.session.add(new_user)
			db.session.commit()
			
			app.logger.info("User Ravinder Singh Added.")
		else:
			app.logger.info("User Ravinder Singh already exists.")

	except Exception as e:
		error_logger(f"Error creating user: {str(e)}")
		db.session.rollback()
		raise

def create_user_Faculty():
	"""Create a sample user."""
	try:
		existing_user = User.query.filter_by(firstname="Vivek", employee_id="E1111111").first()
		if not existing_user:
			new_user = User(
				firstname='Vivek',
				middlename='',
				lastname='Gupta',
				employee_id="E1111111",
				email="vivek.gupta@gmail.com",
				mobile="9899378106",
				department= "RPC",
				designation="Professor",
				date_expiry= datetime(2057, 2, 28),
				roles= [UserRoles(role=UserRole.FACULTY),UserRoles(role=UserRole.LIBRARYMANAGER)]
			)
			db.session.add(new_user)
			db.session.commit()
			
			app.logger.info("User Vivek gupta Added.")
		else:
			app.logger.info("User Ravinder Singh already exists.")

	except Exception as e:
		error_logger(f"Error creating user: {str(e)}")
		db.session.rollback()
		raise

