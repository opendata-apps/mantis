from app import create_app, db
from app.database.full_text_search import FullTextSearch

app = create_app()

with app.app_context():
    FullTextSearch.create_materialized_view()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
