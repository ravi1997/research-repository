from app.extension import db

class Author(db.Model):
    __tablename__ = "authors"  # Updated table name to be plural
    id = db.Column(db.Integer, primary_key=True)
    fullName = db.Column(db.String(75), nullable=False)
    abbreviatedName = db.Column(db.String(50), nullable=True)

    employee_id = db.Column(db.String(20),nullable=True)


    # Establish a many-to-many relationship with Article
    articles = db.relationship('ArticleAuthor', back_populates='author')

    def __repr__(self):
        return f"<Author(id={self.id}, fullName='{self.fullName}', abbreviatedName='{self.abbreviatedName}')>"


class Article(db.Model):
    __tablename__ = "articles"  # Updated table name to be plural
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    abstract = db.Column(db.String(1000),nullable=True)


    # Establish a many-to-many relationship with Author
    authors = db.relationship('ArticleAuthor', back_populates='article')

    def __repr__(self):
        return f"<Article(id={self.id}, title='{self.title}')>"


class ArticleAuthor(db.Model):
    __tablename__ = 'article_authors'
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'), primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('authors.id'), primary_key=True)

    article = db.relationship('Article', back_populates='authors')
    author = db.relationship('Author', back_populates='articles')
