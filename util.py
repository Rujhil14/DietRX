from flask import url_for, abort
from dietrx import app
from math import ceil
from difflib import SequenceMatcher
from .models import *


def food_details(x, food):
    x['NCBI Taxonomy ID'] = {'data': str(food.food_id).split(':')[-1],
                             'extlink': 'https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id=' + str(food.food_id).split(':')[-1]}
    x['Food Name'] = {'data': food.display_name,
                        'link': url_for('get_food', food_id=food.food_id)}
    x['Food Category'] = {'data': food.food_category}

    return x

def chemical_details(x, chemical):
    x['PubChem ID'] = {'data': chemical.pubchem_id,
                       'extlink': 'https://pubchem.ncbi.nlm.nih.gov/compound/'+str(chemical.pubchem_id)}
    x['Common Name'] = {'data': chemical.common_name,
                        'link': url_for('get_chemical', pubchem_id=chemical.pubchem_id)}
    x['Functional Group'] = {'data': chemical.functional_group}
    
    return x

def gene_details(x, gene):
    x['Entrez Gene ID'] = {'data': gene.gene_id,
                           'extlink': 'https://www.ncbi.nlm.nih.gov/gene/'+str(gene.gene_id)}
    x['Gene Name'] = {'data': gene.gene_name,
                        'link': url_for('get_gene', gene_id=gene.gene_id)}
    x['Gene Symbol'] = {'data': gene.gene_symbol}

    return x

def disease_details(x, disease):
    if disease.disease_id[0] == 'M':
        x['Disease ID'] = {'data': str(disease.disease_id).split(':')[-1],
                           'extlink': 'https://meshb.nlm.nih.gov/record/ui?ui='+str(disease.disease_id).split(':')[-1]}
    else:
        x['Disease ID'] = {'data': str(disease.disease_id).split(':')[-1],
                           'extlink': 'https://www.omim.org/entry/'+str(disease.disease_id).split(':')[-1]}

    x['Disease Name']= {'data': disease.disease_name,
                      'link': url_for('get_disease', disease_id=disease.disease_id)}
    x['Disease Category']= {'data': disease.disease_category}

    return x

def food_disease(request, subcategory, food_id=None, disease_id=None):
    q = Food_disease.query

    if(food_id):
        q = q.filter_by(food_id=food_id)
    elif(disease_id):
        q = q.filter_by(disease_id=disease_id)

    results = q.order_by('weight DESC').all()

    temp = []
    for res in results:
        x = {}
        positive_associations = 0 if (res.positive_pmid == '') else len(
            res.positive_pmid.split('|'))
        negative_associations = 0 if (res.negative_pmid == '') else len(
            res.negative_pmid.split('|'))
        via_chemicals = 0 if res.pubchem_id == '' else len(
            res.pubchem_id.split('|'))
        disease = res.disease
        food = res.food
        if subcategory == 'food':
            x = food_details(x, food)
        elif subcategory == 'disease':
            x = disease_details(x, disease)
        
        x['(<span style="color: green">Positive</span>, <span style="color: red">Negative</span>, Chemical) Associations'] = {'data': disease.disease_name,
                'fdassociation': True,
                'positive': positive_associations,
                'negative': negative_associations,
                'chemical': via_chemicals
                }

        x['Details']= {'popup': url_for('get_associations', type='food_disease', food_id=food.food_id, disease_id=disease.disease_id)}
        
        x['mapping'] = {v: k for v, k in enumerate(list(x.keys()))}
        temp.append(x)

    results = temp
    column_names = list(temp[0]['mapping'].values())

    return (results, column_names)



def food_chemical(request, subcategory, food_id=None, pubchem_id=None):
    q = Food_chemical.query

    if(food_id):
        q = q.filter_by(food_id=food_id)
    elif(pubchem_id):
        q = q.filter_by(pubchem_id=pubchem_id)

    results = q.all()

    temp=[]
    for res in results:
        x = {}
        association = Food_chemical.query.filter_by(
            pubchem_id=res.pubchem_id, food_id=res.food_id).first()
        chemical = association.chemical
        food = association.food
        if subcategory == 'chemical':
            x = chemical_details(x, chemical)
        elif subcategory == 'food':
            x = food_details(x, food)

        x['Content'] = {'data': association.content}
        x['Source'] = {'data': association.references}

        x['mapping'] = {v: k for v, k in enumerate(list(x.keys()))}
        temp.append(x)

    results = temp
    column_names = list(temp[0]['mapping'].values())

    return (results, column_names)



def disease_chemical(request, subcategory, disease_id=None, pubchem_id=None):
    q = Chemical_disease.query

    if(disease_id):
        q = q.filter_by(disease_id=disease_id)
    elif(pubchem_id):
        q = q.filter_by(pubchem_id=pubchem_id)

    results = q.all()

    temp = []
    for res in results:
        via_genes = res.via_genes.split('|')
        temp.append({'association': res,
                     'via_genes': via_genes,
                     'count': len(via_genes)
                     })

    results = sorted(temp, key=lambda x: x['count'], reverse=True)

    temp = []
    for res in results:
        x = {}
        association = res['association']
        if(len(res['via_genes']) == 1 and res['via_genes'][0] == ''):
            res['via_genes'] = 0
        else:
            res['via_genes'] = len(res['via_genes'])
        chemical = association.chemical
        disease = association.disease
        if subcategory == 'chemical':
            x = chemical_details(x, chemical)
        elif subcategory == 'disease':
            x = disease_details(x, disease)

        x['Type'] = {'data': association.type_relation}
        x['Via Genes'] = {'data': res['via_genes']}
        x['Source'] = {
            'data': 'CTD' if association.type_relation else 'Inferred'}
        x['Details'] = {'popup': url_for('get_associations', type='chemical_disease',
                                         pubchem_id=chemical.pubchem_id, disease_id=disease.disease_id)}

        x['mapping'] = {v: k for v, k in enumerate(list(x.keys()))}
        temp.append(x)

    results = temp
    column_names = list(temp[0]['mapping'].values())

    return (results, column_names)
    

def chemical_gene(request, subcategory, gene_id=None, pubchem_id=None):
    q = Chemical_gene.query
    if(pubchem_id):
        q = q.filter_by(pubchem_id=pubchem_id)
    elif(gene_id):
        q = q.filter_by(gene_id=gene_id)

    results = q.all()

    temp = []
    for res in results:
        via_diseases = [] if (res.via_diseases == '') else res.via_diseases.split('|')
        temp.append({'association': res,
                     'via_diseases': via_diseases,
                     'count': len(via_diseases)
                     })

    results = sorted(temp, key=lambda x: x['count'], reverse=True)

    temp = []

    for res in results:
        x = {}
        association = res['association']

        if(len(res['via_diseases']) == 1 and res['via_diseases'][0] == ''):
            res['via_diseases'] = 0
        else:
            res['via_diseases'] = len(res['via_diseases'])
        gene = association.gene
        chemical = association.chemical
        if subcategory == 'gene':
            x = gene_details(x, gene)
        elif subcategory == 'chemical':
            x = chemical_details(x, chemical)

        x['Via Diseases'] = {'data': res['via_diseases']}
        x['Details'] = {'popup': url_for('get_associations', type='chemical_gene',
                                         pubchem_id=chemical.pubchem_id, gene_id=gene.gene_id)}

        x['mapping'] = {v: k for v, k in enumerate(list(x.keys()))}
        temp.append(x)

    results = temp
    column_names = list(temp[0]['mapping'].values())

    return (results, column_names)


def food_gene(request, subcategory, gene_id=None, food_id=None):
    q = Food_gene.query
    if(food_id):
        q = q.filter_by(food_id=food_id)
    elif(gene_id):
        q = q.filter_by(gene_id=gene_id)

    results = q.all()

    temp = []
    for res in results:
        disease_ids = [] if (res.via_diseases == '') else res.via_diseases.split('|')
        pubchem_ids = [] if (res.via_chemicals == '') else res.via_chemicals.split('|')
        temp.append({'association': res,
                     'via_diseases': disease_ids,
                     'via_chemicals': pubchem_ids,
                     'count': len(disease_ids) + len(pubchem_ids)})

    results = sorted(temp, key=lambda x: x['count'], reverse=True)

    temp = []

    for res in results:
        x = {}
        association = res['association']
        gene = association.gene
        food = association.food
        if subcategory == 'gene':
            x = gene_details(x, gene)
        elif subcategory == 'food':
            x = food_details(x, food)

        x['Via Diseases'] = {'data': len(res['via_diseases'])}
        x['Via Chemicals'] = {'data': len(res['via_chemicals'])}
        x['Details'] = {'popup': url_for(
            'get_associations', type='food_gene', food_id=food.food_id, gene_id=gene.gene_id)}

        x['mapping'] = {v: k for v, k in enumerate(list(x.keys()))}
        temp.append(x)

    results = temp
    column_names = list(temp[0]['mapping'].values())

    return (results, column_names)


def disease_gene(request, subcategory, gene_id=None, disease_id=None):

    q = Disease_gene.query
    if(disease_id):
        q = q.filter_by(disease_id=disease_id)
    elif(gene_id):
        q = q.filter_by(gene_id=gene_id)

    results = q.all()

    temp = []
    for res in results:
        via_chemicals = [] if (res.via_chemicals == '') else res.via_chemicals.split('|')
        temp.append({'association': res,
                     'via_chemicals': via_chemicals,
                     'count': len(via_chemicals)})
    results = sorted(temp, key=lambda x: x['count'], reverse=True)

    temp = []

    for res in results:
        x = {}
        association = res['association']
        disease = association.disease
        gene = association.gene
        if(len(res['via_chemicals']) == 1 and res['via_chemicals'][0] == ''):
            res['via_chemicals'] = 0
        else:
            res['via_chemicals'] = len(res['via_chemicals'])
        if subcategory == 'gene':
            x = gene_details(x, gene)
        elif subcategory == 'disease':
            x = disease_details(x, disease)

        x['Via Chemicals'] = {'data': res['via_chemicals']}
        x['Source'] = {'data': association.reference or 'Inferred'}
        x['Details'] = {'popup': url_for('get_associations', type='disease_gene',
                                         gene_id=gene.gene_id, disease_id=disease.disease_id)}

        x['mapping'] = {v: k for v, k in enumerate(list(x.keys()))}
        temp.append(x)

    results = temp
    column_names = list(temp[0]['mapping'].values())

    return (results, column_names)


def search_elastic(index, query, fields, page, per_page):
    body = {'query': {'multi_match':
                      {
                          'query': str(query),
                          'fields': fields
                      }
                      },
            'from': (page - 1) * per_page,
            'size': per_page
            }
    return app.elasticsearch.search(index=index, doc_type=index, body=body)


def autocomplete_search(index, field, query, separator=False):
    query = query.lower()
    body = {'query':
            {
                'wildcard': {str(field): str(query) + '*'}
            }
            }

    results = app.elasticsearch.search(index=index, doc_type=index, body=body)
    if separator:
        results = [x['_source'][str(field)].lower()
                   for x in results['hits']['hits']]
        temp = []
        for x in results:
            temp = temp + x.split(separator)
        results = []
        for x in temp:
            if(x.startswith(query)):
                results.append(x)
    else:
        results = [x['_source'][str(field)].lower()
                   for x in results['hits']['hits']]
        temp = []
        for res in results:
            if(res.startswith(query)):
                temp.append(res)
        results = temp
    return list(set(results))


class Pagination(object):

    def __init__(self, page, per_page, results, request, view):
        self.page = page
        self.per_page = per_page
        self.total_count = len(results)

        self.pages = int(ceil(self.total_count / float(self.per_page)))
        self.has_prev = self.page > 1
        self.has_next = self.page < self.pages

        if(self.page <= 0 or self.page > self.pages):
            abort(404)

        self.items = results[(page - 1) * per_page:page * per_page + 1]

        mod_Q = {argf: argv for argf, argv in request.args.items()
                 if argf != 'page'}

        self.first_url = url_for(view, page=1, **mod_Q) \
            if (page != 1) else None
        self.next_url = url_for(view, page=self.page + 1, **mod_Q) \
            if self.has_next else None
        self.prev_url = url_for(view, page=self.page - 1, **mod_Q) \
            if self.has_prev else None
        self.last_url = url_for(view, page=self.pages, **mod_Q) \
            if (page != self.pages) else None
