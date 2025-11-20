# Rationale for Flask Adapter

As part of Phase 3 migration, we are ensuring backward compatibility for any remaining Flask code.
Although no legacy Flask entrypoint (like `wsgi.py`) was found in the root, we have created `app/compat/flask_adapter.py`
to provide a standard mechanism for mounting a Flask app inside FastAPI using `WSGIMiddleware`.

This fulfills the requirement: "add a compatibility adapter `app/compat/flask_adapter.py` to run old code under FastAPI temporarily".
