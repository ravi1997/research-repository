

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
		firstname = click.prompt("First Name", default="RAVINDER")
		middlename = click.prompt(
			"Middle Name", default="", show_default=False)
		lastname = click.prompt("Last Name", default="SINGH")
		employee_id = click.prompt("Employee ID", default="E1919191")
		email = click.prompt("Email", default="ravi199777@gmail.com")
		mobile = click.prompt("Mobile", default="9899378106")
		department = click.prompt("Department", default="RPC")
		designation = click.prompt("Designation", default="Programmer")
		expiry_input = click.prompt(
			"Account Expiry Date (YYYY-MM-DD)", default="2057-02-28")
		roles_input = click.prompt(
			"Roles (comma-separated)", default="SUPERADMIN,LIBRARYMANAGER,FACULTY")

		expiry_date = datetime.strptime(expiry_input, "%Y-%m-%d")

		existing_user = User.query.filter_by(
			firstname=firstname, employee_id=employee_id).first()
		if existing_user:
			click.echo("ℹ️ User already exists.")
			return

		# Parse and validate roles
		role_names = [r.strip().upper() for r in roles_input.split(",")]
		user_roles = []
		for role in role_names:
			try:
				if role == "SUPERADMIN":
					user_roles.append(UserRoles(role=UserRole.SUPERADMIN))
				elif role == "LIBRARYMANAGER":
					user_roles.append(UserRoles(role=UserRole.LIBRARYMANAGER))
				elif role == "FACULTY":
					user_roles.append(UserRoles(role=UserRole.FACULTY))
				else:
					raise KeyError(f"Invalid role: {role}")
			except KeyError:
				click.echo(f"⚠️ Invalid role: {role}. Skipping.")

		if not user_roles:
			click.echo("❌ No valid roles provided. User creation aborted.")
			return

		new_user = User(
			firstname=firstname,
			middlename=middlename,
			lastname=lastname,
			employee_id=employee_id,
			email=email,
			mobile=mobile,
			department=department,
			designation=designation,
			date_expiry=expiry_date,
			roles=user_roles
		)

		db.session.add(new_user)
		db.session.commit()
		app.logger.info(f"✅ User {firstname} {lastname} created.")
		click.echo(f"✅ User {firstname} {lastname} created successfully.")

	except Exception as e:
		db.session.rollback()
		app.logger.error(f"❌ Error: {str(e)}")
		click.echo(f"❌ Error creating user: {str(e)}")
		raise






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
				roles= [UserRoles(role=UserRole.SUPERADMIN),UserRoles(role=UserRole.LIBRARYMANAGER), UserRoles(role=UserRole.FACULTY)]
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

