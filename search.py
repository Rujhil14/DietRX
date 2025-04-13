from dietrx import app


def add_to_index(index, model, id):
    payload = {}
    for field in model.__searchable__:
        payload[field] = getattr(model, field)
    app.elasticsearch.index(index=index, doc_type=index, id=getattr(model, id),
                                    body=payload)

def remove_from_index(index, model, id):
    app.elasticsearch.delete(index=index, doc_type=index, id=getattr(model, id))