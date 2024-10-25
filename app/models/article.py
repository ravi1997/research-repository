from app.extension import db
from sqlalchemy.orm import relationship,validates
from sqlalchemy import DateTime

class Author(db.Model):
    __tablename__ = "authors"  # Updated table name to be plural
    id = db.Column(db.Integer, primary_key=True)
    fullName = db.Column(db.String(75), nullable=False)
    author_abbreviated = db.Column(db.String(50), nullable=True)
    affiliations = db.Column(db.String(200), nullable=True)
    
    sequence_number =  db.Column(db.Integer, nullable=False)
        
    employee_id = db.Column(db.String(20),nullable=True)


    # Establish a many-to-many relationship with Article
    articles = db.relationship('ArticleAuthor', back_populates='author')

    def __repr__(self):
        return f"<Author(id={self.id}, fullName='{self.fullName}', abbreviatedName='{self.abbreviatedName}')>"

class Article(db.Model):
    __tablename__ = "articles"  # Updated table name to be plural
    id = db.Column(db.Integer, primary_key=True)
    
    uuid =  db.Column(db.String(100), nullable=False)
    
    publication_types = relationship("PublicationType", back_populates="articles")
    keywords = relationship("Keywords", back_populates="articles")
        
    # Establish a many-to-many relationship with Author
    authors = db.relationship('ArticleAuthor', back_populates='article')
    
    title = db.Column(db.String(100), nullable=False)
    abstract = db.Column(db.String(1000),nullable=True)

    place_of_publication = db.Column(db.String(100),nullable=True)
    journal = db.Column(db.String(100),nullable=True)
    journal_abrevated = db.Column(db.String(100),nullable=True)

    publication_date = db.Column(DateTime,nullable=True)
    electronic_publication_date = db.Column(DateTime,nullable=True)

    pages = db.Column(db.String(10), nullable=True)
    journal_volume = db.Column(db.String(10), nullable=False)
    journal_issue = db.Column(db.String(10), nullable=True)

    # identifiers
    pubmed_id = db.Column(db.String(100), nullable=True)
    pmc_id = db.Column(db.String(100), nullable=True)
    pii = db.Column(db.String(100), nullable=True)
    doi = db.Column(db.String(100), nullable=True)
    print_issn = db.Column(db.String(100), nullable=True)
    electronic_issn = db.Column(db.String(100), nullable=True)
    linking_issn = db.Column(db.String(100), nullable=True)
    nlm_journal_id = db.Column(db.String(100), nullable=True)

    links = relationship("Link", back_populates="article")
    assets = relationship("Asset", back_populates="article")


    def __repr__(self):
        return f"<Article(id={self.id}, title='{self.title}')>"

class Link(db.Model):
    __tablename__ = 'links'
    id = db.Column(db.Integer, primary_key=True)
    link = db.Column(db.String(30), nullable=False)  # Use enum directly
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'), primary_key=True)
    
    article = relationship("Article",  back_populates="links")  # Backref to User




class Asset(db.Model):
    __tablename__ = 'assets'
    id = db.Column(db.Integer, primary_key=True)
    asset = db.Column(db.String(30), nullable=False)  # Use enum directly
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'), primary_key=True)
    asset_type = db.Column(db.String(30), nullable=False) 
    article = relationship("Article",  back_populates="assets")  # Backref to User



class ArticleAuthor(db.Model):
    __tablename__ = 'article_authors'
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'), primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('authors.id'), primary_key=True)

    article = db.relationship('Article', back_populates='authors')
    author = db.relationship('Author', back_populates='articles')


class PublicationType(db.Model):
    __tablename__ = 'publication_types'
    id = db.Column(db.Integer, primary_key=True)
    publication_type = db.Column(db.String(30), primary_key=True)  # Use enum directly
    
    articles = relationship("Article",  back_populates="publication_types")  # Backref to User


class Keyword(db.Model):
    __tablename__ = 'keywords'
    id = db.Column(db.Integer, primary_key=True)
    publication_type = db.Column(db.String(75), primary_key=True)  # Use enum directly
    
    articles = relationship("Article",  back_populates="keywords")  # Backref to User
    


class ArticleKeyword(db.Model):
    __tablename__ = 'article_keywords'
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'))
    keyword_id = db.Column(db.Integer, db.ForeignKey('keywords.id'))

    article = relationship("Article", back_populates="keywords")  # Backref to User
    keyword = relationship("Keyword", back_populates="articles")



class ArticlePublicationType(db.Model):
    __tablename__ = 'article_publication_types'
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'))
    publication_type_id = db.Column(db.Integer, db.ForeignKey('publication_types.id'))

    article = relationship("Article", back_populates="publication_types")  # Backref to User
    publication_type = relationship("PublicationType", back_populates="articles")
