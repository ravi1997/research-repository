from flask import jsonify,current_app as app, request
from sqlalchemy import func,text
from app.extension import db
from . import search_bp
import re
from app.mylogger import error_logger

# Logging utility
def log_error(msg):
    error_logger.error(f"[ERROR] {msg}")

def log_info(msg):
    app.logger.info(f"[INFO] {msg}")

@search_bp.route("/")
def index(session):
    log_info("Accessed the index route for search.")
    return "This is the research repository search route"

def sanitizer(search_query):
    characters_to_replace = r"[^a-zA-Z0-9]"
    myqueries = re.sub(characters_to_replace, " ", search_query).strip()  # Replace non-alphanumeric with space
    myqueries = re.sub(r"\s+", " ", myqueries)  # Replace multiple spaces with a single space
    return myqueries


def get_article_uuids(search_query, author_list=[],journal_list=[],entry=0,limit=10,start_date='',end_date=''):
 
    santized_authors = [sanitizer(author).replace(" ", " & ") for author in author_list]
    # santized_journals = [sanitizer(journal).replace(" ", " & ") for journal in journal_list]
    author_query = ' & '.join(santized_authors)
    # journal_query = ' | '.join(santized_journals)
    

    # Sanitize and format search query
    myqueries = sanitizer(search_query)  # Replace multiple spaces with a single space
    myqueries = myqueries[:100]
    and_myqueries = myqueries.replace(" ", " & ")  # Replace single space with " & "

    # Base query
    
    sub_query_and = """
        SELECT a.uuid, ts_rank(a.fts_vector, to_tsquery(:and_query)) AS rank
        FROM articles a
        WHERE a.fts_vector @@ to_tsquery(:and_query)
    """
    
    
    

    # Parameters dictionary
    query_params = {
        "and_query": and_myqueries,
        "offset":entry,
        "limit":limit
    }

    # Dynamically add filters only if they are not empty
    if author_query:
        sub_query_and = text(str(sub_query_and) + " AND a.fts_vector @@ to_tsquery(:author_query)")
        query_params["author_query"] = author_query

    if journal_list != []:
        j_list = [journal.strip() for journal in journal_list[0].split('|')]
        app.logger.info(j_list)
        
        journal_filter_query = " AND a.journal IN :journal_list"
        sub_query_and = text(str(sub_query_and) + journal_filter_query)
        query_params["journal_list"] =  tuple(j_list)
        

    # if keyword_query:
    #     sub_query_and = text(str(sub_query_and) + " AND a.fts_vector @@ to_tsquery(:keyword_query)")
    #     sub_query_or = text(str(sub_query_or) + " AND a.fts_vector @@ to_tsquery(:keyword_query)")
    #     query_params["keyword_query"] = keyword_query

    if start_date:
        sub_query_and = text(str(sub_query_and) + " AND a.publication_date >= to_date(:start_date, 'YYYY-MM-DD')")
        query_params["start_date"] = start_date

    if end_date:
        sub_query_and = text(str(sub_query_and) + " AND a.publication_date <= to_date(:end_date, 'YYYY-MM-DD')")
        query_params["end_date"] = end_date


    query = text(str(sub_query_and)
        +
        """
        ORDER BY rank DESC 
    """)

    query = text(str(query) + "OFFSET :offset LIMIT :limit;")

    try:
        log_info(f"query_params : {query_params}")
        raw_query = str(query)

        for key, value in query_params.items():
            raw_query = raw_query.replace(f":{key}", f"'{value}'")

        log_info(f"query : {raw_query}")
        result = db.session.execute(query, query_params)
        rows = result.fetchall()

        # Extract UUIDs from the results
        uuids = [row[0] for row in rows]  # row[0] is the 'uuid' column
        return uuids

    except Exception as e:
        print(f"Error executing query: {e}")
        return []
    finally:
        db.session.close()

def get_unique_authors(search_query):
    # Sanitize and format search query
    myqueries = sanitizer(search_query)  # Replace multiple spaces with a single space
    myqueries = myqueries[:100]
    and_myqueries = myqueries.replace(" ", " & ")  # Replace single space with " & "

    # Base query
    query = text("""
        SELECT au."fullName", COUNT(a.id) AS article_count
        FROM authors au
        JOIN article_authors aa ON au.id = aa.author_id
        JOIN articles a ON aa.article_id = a.id
        WHERE (
            a.fts_vector @@ to_tsquery(:and_query)
        )
        GROUP BY au."fullName"
        ORDER BY article_count DESC;
    """)

    query_params = {
        "and_query": and_myqueries,
    }

    try:
        result = db.session.execute(query, query_params)
        rows = result.fetchall()

        # Return a list of dictionaries with author names and article counts
        authors = [{"name": row[0], "article_count": row[1]} for row in rows]
        return authors

    except Exception as e:
        print(f"Error executing query: {e}")
        return []

    finally:
        db.session.remove()  # Properly remove session in Flask-SQLAlchemy
    
# def get_unique_keywords(search_query):
#     myqueries = sanitizer(search_query)  # Replace multiple spaces with a single space
#     myqueries = myqueries[:100]
#     and_myqueries = myqueries.replace(" ", " & ")  # Replace single space with " & "
#     or_myqueries = myqueries.replace(" ", " | ")  # Replace single space with " | "

#     # Base query
#     query = text("""
#         SELECT k."keyword", COUNT(DISTINCT a.id) AS article_count
#         FROM keywords k
#         JOIN article_keywords ak ON k.id = ak.keyword_id
#         JOIN articles a ON ak.article_id = a.id
#         WHERE (
#             a.fts_vector @@ to_tsquery(:and_query)
#             OR a.fts_vector @@ to_tsquery(:or_query)
#         )
#         GROUP BY k."keyword"
#         ORDER BY article_count DESC;
#     """)

#     query_params = {
#         "and_query": and_myqueries,
#         "or_query": or_myqueries
#     }

#     try:
#         result = db.session.execute(query, query_params)
#         rows = result.fetchall()

#         # Return a list of dictionaries with author names and article counts
#         keywords = [{"name": row[0], "article_count": row[1]} for row in rows]

#         return keywords

#     except Exception as e:
#         print(f"Error executing query: {e}")
#         return []

#     finally:
#         db.session.remove()  # Properly remove session in Flask-SQLAlchemy



def get_unique_journals(search_query):
    myqueries = sanitizer(search_query)  # Replace multiple spaces with a single space
    myqueries = myqueries[:100]
    and_myqueries = myqueries.replace(" ", " & ")  # Replace single space with " & "

    # Base query
    query = text("""
        SELECT DISTINCT a.journal, COUNT(DISTINCT a.id) AS journal_count
        FROM articles a
        WHERE (
            a.fts_vector @@ to_tsquery(:and_query)
        )
        GROUP BY a.journal
        ORDER BY journal_count DESC;
        ;
    """)

    query_params = {
        "and_query": and_myqueries,
    }

    try:
        result = db.session.execute(query, query_params)
        rows = result.fetchall()

        # Return a list of dictionaries with author names and article counts
        journals = [{"name": row[0], "article_count": row[1]} for row in rows]

        return journals

    except Exception as e:
        print(f"Error executing query: {e}")
        return []

    finally:
        db.session.remove()  # Properly remove session in Flask-SQLAlchemy


@search_bp.route('/authors')
def get_authors():
	search_params = request.args.to_dict(flat=False)  # Allows multiple values for the same key
	myquery = search_params.get('query', [""])[0]
	return jsonify(get_unique_authors(myquery))


# @search_bp.route('/keywords')
# def get_keywords():
# 	search_params = request.args.to_dict(flat=False)  # Allows multiple values for the same key
# 	myquery = search_params.get('query', [""])[0]
# 	return jsonify(get_unique_keywords(myquery))


@search_bp.route('/journals')
def get_journals():
	search_params = request.args.to_dict(flat=False)  # Allows multiple values for the same key
	myquery = search_params.get('query', [""])[0]
	return jsonify(get_unique_journals(myquery))

@search_bp.route("/search", methods=['GET'])
def search_articles():
    try:
        log_info(f"/n =====================    ROUTE = /search_route  FUNCTION = search_articles ======================")
        search_params = request.args.to_dict(flat=False)  # Allows multiple values for the same key
        log_info(f"search_route search_params : {search_params}. Fetching results...")
        myquery = search_params.get('query', [""])[0]
        log_info(f"search_route  - myquery : {myquery}. Fetching results...")
        offset = request.args.get('offset', 0, type=int)
        limit = request.args.get('limit', 10, type=int)
        filter_authors = []
        filter_journals = []
        # filter_keywords = []
        filter_start_date = ''
        filter_end_date = ''


        if offset < 0 or limit <= 0:
            return jsonify({"error": "Offset must be non-negative and Limit must be greater than 0"}), 400

        log_info(f"Applying filters")

        filter_json = {}
        # Apply filters for authors

        if 'authors' in search_params:
            filter_json["authors"] = search_params['authors']
            filter_authors = search_params['authors']
    
        # Apply filters for keywords
        # if 'keywords' in search_params:
        #     filter_json["keywords"] = search_params['keywords']
        #     filter_keywords = search_params['keywords']

        # Apply filters for publication date
        if 'start_date' in search_params:
            if search_params['start_date'] and search_params['start_date']!="":
                filter_json["start_date"] = search_params['start_date']
                filter_start_date = search_params['start_date'][0]
    
        if 'end_date' in search_params:
            if search_params['end_date'] and search_params['end_date']!="":
                filter_json["end_date"] = search_params['end_date']
                filter_end_date = search_params['end_date'][0]
    
        # Apply filters for journals
        if 'journals' in search_params:
            filter_json["journals"] = search_params['journals']	# Apply filters for authors
            filter_journals = search_params['journals']


        articles_json = get_article_uuids(myquery,filter_authors,filter_journals,0,100000,filter_start_date,filter_end_date)

        log_info(f"search_route Completed.. now adding to articles_json : {len(articles_json)}")

        
        if articles_json == []:
            return jsonify({
                "message": "Offset exceeds the total number of results.",
                "total_articles": 0,
                "offset": offset,
                "limit": limit,
                "articles": [],
                "filters" : filter_json
            }), 200
        
        filtered_articles = articles_json
        total_articles = len(filtered_articles)
        log_info(f"ready to return")
        log_info(f"total_articles : {total_articles}")
        log_info(f"offset : {offset}")
        log_info(f"limit : {limit}")
        
        # Count total articles before pagination
        if offset >= total_articles:
            return jsonify({
                "message": "Offset exceeds the total number of results.",
                "total_articles": total_articles,
                "offset": offset,
                "limit": limit,
                "articles": [],
                "filters" : filter_json
            }), 200

        response = {
            "message": "Search successful.",
            "total_articles": total_articles,
            "offset": offset,
            "limit": limit,
            "articles": filtered_articles[offset:offset+limit],
            "filters" : filter_json
        }

        log_info(f"search is returning")


        return jsonify(response), 200
    except Exception as e:  # Catches any exception
        log_info(f"An error occurred: {e}", exc_info=True)
        return jsonify({"message" : "something went wrong"}),500