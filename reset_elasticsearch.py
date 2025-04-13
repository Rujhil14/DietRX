from dietrx import *
from dietrx.models import *


app.elasticsearch.indices.delete(index='food', ignore=[400, 404])
app.elasticsearch.indices.delete(index='disease', ignore=[400, 404])
app.elasticsearch.indices.delete(index='gene', ignore=[400, 404])


Food.reindex("food_id")
Disease.reindex("disease_id")
Gene.reindex("gene_id")

app.elasticsearch.indices.delete(index='chemical', ignore=[400, 404])

Chemical.reindex("pubchem_id")
