from sqlalchemy.dialects.postgresql import TSVECTOR,JSONB
from sqlalchemy import DateTime, func, Enum as SQLAlchemyEnum
from app.extension import db
from sqlalchemy.orm import relationship

import uuid
def generate_uuid():
    return str(uuid.uuid4())


class Author(db.Model):
    __tablename__ = "authors"
    id = db.Column(db.Integer, primary_key=True)
    fullName = db.Column(db.Text, nullable=False)
    author_abbreviated = db.Column(db.Text, nullable=True)
    affiliations = db.Column(db.JSON, nullable=True)
    employee_id = db.Column(db.Text, nullable=True)
    # Full-Text Search (FTS) column
    fts_vector = db.Column(TSVECTOR)
    articles = db.relationship('ArticleAuthor', back_populates='author')

    def __repr__(self):
        return f"<Author(id={self.id}, fullName='{self.fullName}')>"

class Article(db.Model):
    __tablename__ = "articles"
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.Text, nullable=False)

    # Many-to-Many relationship with PublicationType
    publication_types = db.relationship(
        "PublicationType",
        secondary="article_publication_types",
        back_populates="articles"
    )
    fts_vector = db.Column(TSVECTOR)
    # Many-to-Many relationship with Keyword
    keywords = db.relationship(
        "Keyword",
        secondary="article_keywords",
        back_populates="articles"
    )
    
    # Many-to-Many relationship with Author through the ArticleAuthor association
    authors = db.relationship(
        'ArticleAuthor', 
        back_populates='article',
        order_by='ArticleAuthor.sequence_number'
    )
    
    title = db.Column(db.Text, nullable=False)
    abstract = db.Column(db.Text, nullable=True)
    place_of_publication = db.Column(db.Text, nullable=True)
    journal = db.Column(db.Text, nullable=True)
    journal_abrevated = db.Column(db.Text, nullable=True)
    publication_date = db.Column(db.Date, nullable=True)
    electronic_publication_date = db.Column(db.Date, nullable=True)
    pages = db.Column(db.Text, nullable=True)
    journal_volume = db.Column(db.Text, nullable=True)
    journal_issue = db.Column(db.Text, nullable=True)

    # Identifiers
    pubmed_id = db.Column(db.Text, nullable=True)
    pmc_id = db.Column(db.Text, nullable=True)
    pii = db.Column(db.Text, nullable=True)
    doi = db.Column(db.Text, nullable=True)
    print_issn = db.Column(db.Text, nullable=True)
    electronic_issn = db.Column(db.Text, nullable=True)
    linking_issn = db.Column(db.Text, nullable=True)
    nlm_journal_id = db.Column(db.Text, nullable=True)
    created_at = db.Column(DateTime, server_default=func.now())  # Corrected attribute name
    created_by = db.Column(db.Integer,nullable=True)

    updated_at = db.Column(DateTime,nullable=True)  # Corrected attribute name
    updated_by = db.Column(db.Integer,nullable=True)

    links = relationship("Link", back_populates="article")
    assets = relationship("Asset", back_populates="article")
    statistic = db.relationship('ArticleStatistic', back_populates='article', uselist=False, cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Article(id={self.id}, title='{self.title}')>"


class Link(db.Model):
    __tablename__ = 'links'
    id = db.Column(db.Integer, primary_key=True)
    link = db.Column(db.Text, nullable=False)
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'), nullable=True)
    article = relationship("Article", back_populates="links")

class Asset(db.Model):
    __tablename__ = 'assets'
    id = db.Column(db.Integer, primary_key=True)
    asset = db.Column(db.Text, nullable=False)
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'))
    asset_type = db.Column(db.Text, nullable=False)
    article = relationship("Article", back_populates="assets")

class ArticleAuthor(db.Model):
    __tablename__ = 'article_authors'
    
    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('authors.id'), nullable=False)
    sequence_number = db.Column(db.Integer, nullable=False)  # New field for sequence number
    author = relationship("Author", back_populates="articles")
    article = relationship("Article", back_populates="authors")


    def __repr__(self):
        return f"<ArticleAuthor(article_id={self.article_id}, author_id={self.author_id}, sequence_number={self.sequence_number}, author={self.author})>"


class PublicationType(db.Model):
    __tablename__ = 'publication_types'
    id = db.Column(db.Integer, primary_key=True)
    publication_type = db.Column(db.Text, nullable=False)
    # Many-to-Many relationship with Article
    articles = db.relationship(
        "Article",
        secondary="article_publication_types",
        back_populates="publication_types"
    )

class Keyword(db.Model):
    __tablename__ = 'keywords'
    id = db.Column(db.Integer, primary_key=True)
    keyword = db.Column(db.Text, nullable=False)
    uuid = db.Column(db.Text, nullable=False,server_default=str(uuid.uuid4()))
    fts_vector = db.Column(TSVECTOR)
    articles = db.relationship(
        "Article",
        secondary="article_keywords",
        back_populates="keywords"
    )

class ArticleKeyword(db.Model):
    __tablename__ = 'article_keywords'
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'), primary_key=True)
    keyword_id = db.Column(db.Integer, db.ForeignKey('keywords.id'), primary_key=True)

class ArticlePublicationType(db.Model):
    __tablename__ = 'article_publication_types'
    article_id = db.Column(
        db.Integer,
        db.ForeignKey('articles.id'),
        primary_key=True,
        autoincrement=False
    )
    publication_type_id = db.Column(
        db.Integer,
        db.ForeignKey('publication_types.id'),
        primary_key=True,
        autoincrement=False
    )

class ArticleStatistic(db.Model):
    __tablename__ = "articlestatistics"
    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'), nullable=False)
    viewed = db.Column(db.Integer,nullable=False,server_default='0')
    searched = db.Column(db.Integer,nullable=False,server_default='0')
    downloaded = db.Column(db.Integer,nullable=False,server_default='0')


    # Back-reference to the User model
    article = db.relationship('Article', back_populates='statistic')
    
    
class Duplicate(db.Model):
    __tablename__ = "duplicates"
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.Text, nullable=False)
    field = db.Column(db.Text, nullable=False)
    value = db.Column(db.Text, nullable=False)
    articles = db.Column(db.Text, nullable=False)
    created_at = db.Column(DateTime, server_default=func.now())  # Corrected attribute name




class DeletedArticle(db.Model):
    __tablename__ = "deleted_articles"
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.Text, nullable=False)
    article = db.Column(db.JSON,nullable=False)
    deleted_at = db.Column(DateTime, server_default=func.now())  # Corrected attribute name
