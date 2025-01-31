

from datetime import datetime
import json
from marshmallow import ValidationError
from sqlalchemy import func, or_, text
from app.models import User
from app.models.article import Article, ArticleAuthor, ArticleKeyword, Author, Keyword
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

@click.command('create-index')
def create_index_command():
    with db.engine.connect() as connection:
        connection.execute(text("CREATE INDEX IF NOT EXISTS article_fts_idx ON articles USING GIN(fts_vector);"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS author_fts_idx ON authors USING GIN(fts_vector);"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS keyword_fts_idx ON keywords USING GIN(fts_vector);"))
        connection.execute(text("""
            DROP TRIGGER IF EXISTS article_fts_update ON articles;
            DROP TRIGGER IF EXISTS author_fts_update ON authors;
            DROP TRIGGER IF EXISTS keyword_fts_update ON keywords;
            DROP FUNCTION IF EXISTS update_article_fts;
            DROP FUNCTION IF EXISTS update_author_fts;
            DROP FUNCTION IF EXISTS update_keyword_fts;
        """))
        connection.execute(text("""
			CREATE FUNCTION update_article_fts() RETURNS TRIGGER AS $$ 
			BEGIN
			NEW.fts_vector :=
				setweight(to_tsvector('english', COALESCE(NEW.title, '')), 'A') ||
				setweight(to_tsvector('english', COALESCE(NEW.abstract, '')), 'B') ||
				setweight(to_tsvector('english', COALESCE(NEW.journal, '')), 'C') ||
				setweight(to_tsvector('english', COALESCE(NEW.doi, '')), 'D');
			RETURN NEW;
			END
			$$ LANGUAGE plpgsql;
			"""))
        connection.execute(text("""        
			CREATE FUNCTION update_author_fts() RETURNS TRIGGER AS $$
			BEGIN
			NEW.fts_vector :=
				setweight(to_tsvector('english', COALESCE(NEW."fullName", '')), 'A') ||
				setweight(to_tsvector('english', COALESCE(NEW."author_abbreviated", '')), 'B');
			RETURN NEW;
			END
			$$ LANGUAGE plpgsql;
			"""))
        connection.execute(text("""        
			CREATE FUNCTION update_keyword_fts() RETURNS TRIGGER AS $$
			BEGIN
			NEW.fts_vector := to_tsvector('english', COALESCE(NEW.keyword, ''));
			RETURN NEW;
			END
			$$ LANGUAGE plpgsql;
			"""))
        
        connection.execute(text("""        
			CREATE TRIGGER article_fts_update BEFORE INSERT OR UPDATE
			ON articles FOR EACH ROW EXECUTE FUNCTION update_article_fts();

			CREATE TRIGGER author_fts_update BEFORE INSERT OR UPDATE
			ON authors FOR EACH ROW EXECUTE FUNCTION update_author_fts();

			CREATE TRIGGER keyword_fts_update BEFORE INSERT OR UPDATE
			ON keywords FOR EACH ROW EXECUTE FUNCTION update_keyword_fts();
			"""))
      
        connection.commit()


@click.command('test')
def test_command():
	search_query = 'Gupta, Vivek'

	results = (
		db.session.query(Article)
		.join(ArticleAuthor, Article.id == ArticleAuthor.article_id)
		.join(Author, ArticleAuthor.author_id == Author.id)
		.join(ArticleKeyword, Article.id == ArticleKeyword.article_id)
		.join(Keyword, ArticleKeyword.keyword_id == Keyword.id)
		.filter(
			or_(
				Article.fts_vector.op('@@')(func.plainto_tsquery('english', search_query)),
				Author.fts_vector.op('@@')(func.plainto_tsquery('english', search_query)),
				Keyword.fts_vector.op('@@')(func.plainto_tsquery('english', search_query))
			)
		)
		.order_by(Article.uuid)
		.all()
	)
	print(results)
	for article in results:
		print(article)


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

