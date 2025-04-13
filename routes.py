from dietrx import app, fgname2id
from flask import request, render_template, url_for, redirect, abort, Response, jsonify
#I added
from openbabel import pybel
#from pybel import readstring
from .models import *
import json
from .util import *
from .forms import ChemicalSearchForm
from subprocess import check_call
#from pybel import readfile
import numpy as np

from datetime import date

NUM_PER_PAGE = 20
NUM_PER_PAGE_CHEM = 100

stats = dict(
	fd_assoc=280328,
	fd_foods=2337,
	fc_foods=2337,
	fcats=25,
	fd_pmids=39348,
	precision=0.87,
	recall=0.8,
	f1=0.84,
	chems=6992,
)


@app.route('/dietrx/', methods=['GET'])
@app.route('/dietrx/index', methods=['GET'])
def index():
	chemical_search_form = ChemicalSearchForm()
	food_of_the_day = Food.query.limit(100).all()[date.today().day]
	return render_template('search/search.html',
                        chemical_search_form=chemical_search_form,
                        stats=stats,
						food=food_of_the_day)


@app.route('/dietrx/search', methods=['GET'])
def search():
	table = request.args.get('table')
	query = request.args.get('query')

	page = request.args.get('page', 1, type=int)
	template = ''
	if(table == 'food'):
		results = search_elastic(
			table, query, Food.__searchboost__, page, NUM_PER_PAGE)
		template = 'food/search_results.html'
	elif(table == 'disease'):
		results = search_elastic(
			table, query, Disease.__searchable__, page, NUM_PER_PAGE)
		template = 'disease/search_results.html'
	elif(table == 'gene'):
		results = search_elastic(
			table, query, Gene.__searchboost__, page, NUM_PER_PAGE)
		template = 'gene/search_results.html'
	elif(table == 'chemical'):
		results = search_elastic(
			table, query, Chemical.__searchboost__, page, NUM_PER_PAGE)
		template = 'chemical/search_results.html'
	else:
		abort(404)

	page_data = Pagination(
		page, NUM_PER_PAGE, [0]*results['hits']['total'], request, 'search')

	return render_template(template,
                        results=results,
                        next_url=page_data.next_url,
                        last_url=page_data.last_url,
                        prev_url=page_data.prev_url,
                        first_url=page_data.first_url,
                        has_next=page_data.has_next,
                        has_prev=page_data.has_prev,
                        page_number=page_data.page,
                        total_pages=page_data.pages)


def find_similar(smiles):
	""" Runs a shell command to find similar molecules given
	a query molecule """

	# Run shell command to find similar molecules and get results
	check_call(['babel', 'allmol.fs', 'temp/results.sdf',
             '-s' + smiles, '-at0.4'],
            cwd='dietrx/static')

	results = pybel.readfile('sdf', 'dietrx/static/temp/results.sdf')

	# Get molecule objects from results
	mol_ids = [mol.data['pubchem_id'] for mol in results]

	return mol_ids


def process_search_query(formdata):

	# Make a query dictionary
	search_by_smiles = False

	# Common identifiers / ids.
	results = Chemical.query.filter()
	for field in ['common_name', 'iupac_name', 'pubchem_id']:
		key = formdata.get(field) or ''
		key = key.strip()

		if key:
			results = results.filter(getattr(Chemical, field).ilike(key))

	# Functional group
	if formdata.get('functional_group'):
		try:
			fgid = fgname2id[formdata.get('functional_group').lower().strip()]
		except KeyError:
			fgid = len(fgname2id) + 1

		results = results.filter(Chemical.functional_group_idx.contains(fgid))

	# Molecular properties.
	for field in ['molecular_weight', 'hba_count', 'hbd_count', 'num_rings',
               'num_rotatablebonds', 'number_of_aromatic_bonds', 'alogp']:
		if formdata.get(field):
			field_query = formdata.get(field).strip()

			if ':' in field_query:
				low, high = field_query.split(':')

				results = results.filter((getattr(Chemical, field) >= float(low)) & (
					getattr(Chemical, field) <= float(high)))
			else:
				results = results.filter_by(**{field: float(field_query)})

	# Filter data further based on similarity coefficient
	if formdata.get('smiles'):
		smiles = formdata.get('smiles').strip()
		mol_ids = find_similar(smiles)
		results = results.filter(Chemical.pubchem_id.in_(mol_ids))
		search_by_smiles = True

	return results, search_by_smiles


@app.route('/dietrx/chemical_search', methods=['GET'])
def chemical_search():
	results, search_by_smiles = process_search_query(
		request.args)

	fields = ['PubChem ID', 'Common Name', 'Functional Group(s)', 'Details']
	if search_by_smiles:
		fields.append('Similarity')
		query_fp = pybel.readstring("smi", request.args.get('smiles')).calcfp()

	res = list()
	for r in results:
		values = [r.pubchem_id, r.common_name or r.iupac_name, r.functional_group]

		if search_by_smiles:
			fp = readstring("smi", r.smiles).calcfp()
			sim = np.round(query_fp | fp, 2)
			values.append(sim)

		values.append(url_for('get_chemical', pubchem_id=r.pubchem_id))
		res.append(values)

	return render_template('chemical/chemical_search_results.html',
                        fields=fields,
                        results=res,
                        search_by_smiles=search_by_smiles,
                        request=request)


@app.route('/dietrx/chemical_advanced_search', methods=['GET'])
def chemical_advanced_search():
	chemical_search_form = ChemicalSearchForm()
	return render_template('chemical/chemical_advanced_search.html',
                        chemical_search_form=chemical_search_form,
                        advanced_search=True)


@app.route('/dietrx/autocomplete', methods=['GET'])
def autocomplete():
	query = request.args.get('query')
	table = str(request.args.get('table'))

	results = []
	if(table == 'food'):
		for column in ['display_name', 'food_category', 'common_names']:
			if(column in Food.__separators__):
				results = results + \
					autocomplete_search(table, column, query, Food.__separators__[column])
			else:
				results = results + autocomplete_search(table, column, query)
	elif(table == 'disease'):
		for column in ['disease_name', 'disease_category']:
			if(column in Disease.__separators__):
				results = results + \
					autocomplete_search(table, column, query, Disease.__separators__[column])
			else:
				results = results + autocomplete_search(table, column, query)
	elif(table == 'gene'):
		for column in Gene.__searchable__:
			if(column in Gene.__separators__):
				results = results + \
					autocomplete_search(table, column, query, Gene.__separators__[column])
			else:
				results = results + autocomplete_search(table, column, query)
	elif(table == 'chemical'):
		for column in Chemical.__autocomplete__:
			if(column in Chemical.__separators__):
				results = results + \
					autocomplete_search(table, column, query, Chemical.__separators__[column])
			else:
				results = results + autocomplete_search(table, column, query)
	else:
		abort(404)

	results = list(set(results))
	return jsonify(json.dumps(results))


@app.route('/dietrx/get_associations', methods=['GET'])
def get_associations():

	type_association = request.args.get('type')

	if(type_association == 'food_disease'):
		if (not request.args.get('food_id')) or (not request.args.get('disease_id')):
			return redirect(url_for('index'))

		food_id = request.args.get('food_id')
		disease_id = request.args.get('disease_id')

		food = Food.query.filter_by(food_id=food_id).first()
		disease = Disease.query.filter_by(disease_id=disease_id).first()

		if (food is None) or (disease is None):
			abort(404)

		association = Food_disease.query.filter_by(
			disease_id=disease_id, food_id=food_id).first()
		p = association.positive_pmid.split('|')
		n = association.negative_pmid.split('|')
		pubchem_ids = association.pubchem_id.split('|')

		result = {'disease': disease,
                    'food': food,
                    'positive_associations': References.query.filter(References.pmid.in_(p)).all(),
                    'negative_associations': References.query.filter(References.pmid.in_(n)).all(),
                    'via_chemicals': Chemical.query.filter(Chemical.pubchem_id.in_(pubchem_ids)).all()}

		return render_template('common/food_disease_associations_popup.html', result=result)

	elif(type_association == 'food_gene'):
		if (not request.args.get('food_id')) or (not request.args.get('gene_id')):
			return redirect(url_for('index'))

		food_id = request.args.get('food_id')
		gene_id = request.args.get('gene_id')

		food = Food.query.filter_by(food_id=food_id).first()
		gene = Gene.query.filter_by(gene_id=gene_id).first()

		if (food is None) or (gene is None):
			abort(404)

		association = Food_gene.query.filter_by(
			gene_id=gene_id, food_id=food_id).first()
		via_diseases = association.via_diseases.split('|')
		via_chemicals = association.via_chemicals.split('|')

		result = {'gene': gene,
                    'food': food,
                    'via_chemicals': Chemical.query.filter(Chemical.pubchem_id.in_(via_chemicals)).all(),
                    'via_diseases': Disease.query.filter(Disease.disease_id.in_(via_diseases)).all(),
            }

		return render_template('common/food_gene_associations_popup.html', result=result)

	elif(type_association == 'chemical_disease'):

		if (not request.args.get('pubchem_id')) or (not request.args.get('disease_id')):
			return redirect(url_for('index'))

		pubchem_id = request.args.get('pubchem_id')
		disease_id = request.args.get('disease_id')

		chemical = Chemical.query.filter_by(pubchem_id=pubchem_id).first()
		disease = Disease.query.filter_by(disease_id=disease_id).first()

		if (disease is None) or (chemical is None):
			abort(404)

		association = Chemical_disease.query.filter_by(
			disease_id=disease_id, pubchem_id=pubchem_id).first()
		via_genes = association.via_genes.split('|')

		result = {'disease': disease,
                    'chemical': chemical,
                    'via_genes': Gene.query.filter(Gene.gene_id.in_(via_genes)).all()
            }

		return render_template('common/chemical_disease_associations_popup.html', result=result)

	elif(type_association == 'disease_gene'):

		if (not request.args.get('gene_id')) or (not request.args.get('disease_id')):
			return redirect(url_for('index'))

		gene_id = request.args.get('gene_id')
		disease_id = request.args.get('disease_id')

		gene = Gene.query.filter_by(gene_id=gene_id).first()
		disease = Disease.query.filter_by(disease_id=disease_id).first()

		if (disease is None) or (gene is None):
			abort(404)

		association = Disease_gene.query.filter_by(
			disease_id=disease_id, gene_id=gene_id).first()
		via_chemicals = association.via_chemicals.split('|')

		result = {'disease': disease,
                    'gene': gene,
                    'association': association,
                    'via_chemicals': Chemical.query.filter(Chemical.pubchem_id.in_(via_chemicals)).all()
            }

		return render_template('common/disease_gene_associations_popup.html', result=result)

	elif(type_association == 'chemical_gene'):

		if (not request.args.get('gene_id')) or (not request.args.get('pubchem_id')):
			return redirect(url_for('index'))

		gene_id = request.args.get('gene_id')
		pubchem_id = request.args.get('pubchem_id')

		gene = Gene.query.filter_by(gene_id=gene_id).first()
		chemical = Chemical.query.filter_by(pubchem_id=pubchem_id).first()

		if (chemical is None) or (gene is None):
			abort(404)

		association = Chemical_gene.query.filter_by(
			pubchem_id=pubchem_id, gene_id=gene_id).first()
		via_diseases = association.via_diseases.split('|')

		result = {'chemical': chemical,
				  'gene': gene,
				  'association': association,
				  'via_diseases': Disease.query.filter(Disease.disease_id.in_(via_diseases)).all()
            }

		return render_template('common/chemical_gene_associations_popup.html', result=result)

	else:
		abort(404)


@app.route('/dietrx/get_food', methods=['GET'])
def get_food():
	if not request.args.get('food_id'):
		return redirect(url_for('index'))

	food_id = request.args.get('food_id')
	food = Food.query.filter_by(food_id=food_id).first()
	page = request.args.get('page', 1, type=int)

	if (food is not None):
		subcategory_that_exist = []
		if(len(food.food_disease) != 0):
			subcategory_that_exist.append('disease')
		if(len(food.food_gene) != 0):
			subcategory_that_exist.append('gene')
		if(len(food.food_chemical) != 0):
			subcategory_that_exist.append('chemical')
		if(len(subcategory_that_exist) == 0):
			return render_template('food/food_null_page.html', food=food)

		subcategory = request.args.get('subcategory', subcategory_that_exist[0])
		if(subcategory == 'disease'):
			results, column_names = food_disease(
				request, subcategory, food_id=food_id, disease_id=None)

		elif(subcategory == 'gene'):
			results, column_names = food_gene(
				request, subcategory, food_id=food_id, gene_id=None)

		elif(subcategory == 'chemical'):
			results, column_names = food_chemical(
				request, subcategory, food_id=food_id, pubchem_id=None)

		else:
			abort(404)

		return render_template('food/food_page.html',
                         subcategory=subcategory,
                         subcategory_that_exist=subcategory_that_exist,
                         food=food,
                         results=results,
                         column_names=column_names)
	else:
		abort(404)


@app.route('/dietrx/get_disease', methods=['GET'])
def get_disease():
	if not request.args.get('disease_id'):
		return redirect(url_for('index'))

	disease_id = request.args.get('disease_id')
	disease = Disease.query.filter_by(disease_id=disease_id).first()

	page = request.args.get('page', 1, type=int)

	if(disease is not None):
		subcategory_that_exist = []
		if(len(disease.food_disease) != 0):
			subcategory_that_exist.append('food')
		if(len(disease.disease_gene) != 0):
			subcategory_that_exist.append('gene')
		if(len(disease.chemical_disease) != 0):
			subcategory_that_exist.append('chemical')
		subcategory = request.args.get('subcategory', subcategory_that_exist[0])

		if(subcategory == 'food'):
			results, column_names = food_disease(
				request, subcategory, food_id=None, disease_id=disease_id)

		elif(subcategory == 'gene'):

			results, column_names = disease_gene(
				request, subcategory, disease_id=disease_id, gene_id=None)

		elif(subcategory == 'chemical'):

			results, column_names = disease_chemical(
				request, subcategory, disease_id=disease_id, pubchem_id=None)

		else:
			abort(404)

		return render_template('disease/disease_page.html',
                         subcategory=subcategory,
                         subcategory_that_exist=subcategory_that_exist,
                         disease=disease,
                         results=results,
                         column_names=column_names)
	else:
		abort(404)


@app.route('/dietrx/get_chemical', methods=['GET'])
def get_chemical():
	if not request.args.get('pubchem_id'):
		return redirect(url_for('index'))

	pubchem_id = request.args.get('pubchem_id')
	chemical = Chemical.query.filter_by(pubchem_id=pubchem_id).first()

	page = request.args.get('page', 1, type=int)

	if (chemical is not None):

		subcategory_that_exist = []
		if(len(chemical.food_chemical) != 0):
			subcategory_that_exist.append('food')
		if(len(chemical.chemical_disease) != 0):
			subcategory_that_exist.append('disease')
		if(len(chemical.chemical_gene) != 0):
			subcategory_that_exist.append('gene')
		subcategory = request.args.get('subcategory', subcategory_that_exist[0])

		if(subcategory == 'food'):
			results, column_names = food_chemical(
				request, subcategory, food_id=None, pubchem_id=pubchem_id)

		elif(subcategory == 'disease'):

			results, column_names = disease_chemical(
				request, subcategory, disease_id=None, pubchem_id=pubchem_id)
		elif(subcategory == 'gene'):

			results, column_names = chemical_gene(
				request, subcategory, gene_id=None, pubchem_id=pubchem_id)

		else:
			abort(404)
		return render_template('chemical/chemical_page.html',
                         subcategory=subcategory,
                         subcategory_that_exist=subcategory_that_exist,
                         chemical=chemical,
                         results=results,
                         column_names=column_names)
	else:
		abort(404)


@app.route('/dietrx/get_gene', methods=['GET'])
def get_gene():
	if not request.args.get('gene_id'):
		return redirect(url_for('index'))

	gene_id = request.args.get('gene_id')
	gene = Gene.query.filter_by(gene_id=gene_id).first()

	page = request.args.get('page', 1, type=int)

	if (gene is not None):

		subcategory_that_exist = []
		if(len(gene.food_gene) != 0):
			subcategory_that_exist.append('food')
		if(len(gene.disease_gene) != 0):
			subcategory_that_exist.append('disease')
		if(len(gene.chemical_gene) != 0):
			subcategory_that_exist.append('chemical')
		subcategory = request.args.get('subcategory', subcategory_that_exist[0])

		if(subcategory == 'food'):
			results, column_names = food_gene(
				request, subcategory, food_id=None, gene_id=gene_id)

		elif(subcategory == 'disease'):
			results, column_names = disease_gene(
				request, subcategory, disease_id=None, gene_id=gene_id)

		elif(subcategory == 'chemical'):
			results, column_names = chemical_gene(
				request, subcategory, gene_id=gene_id, pubchem_id=None)

		else:
			abort(404)
		return render_template('gene/gene_page.html',
                         subcategory=subcategory,
                         subcategory_that_exist=subcategory_that_exist,
                         gene=gene,
                         results=results,
                         column_names=column_names)
	else:
		abort(404)

	return


@app.route('/dietrx/view_all', methods=['GET'])
def view_all():
	entity_type = request.args.get('type')

	if entity_type == 'food':
		res = Food.query.all()
		fields = [
			['NCBI TAX ID', 'tax_id'],
			['Food Category', 'food_category'],
			['Scientific Name', 'scientific_name'],
			['Common Names', 'common_names'],
			['Explore', 'food_id']
		]
		results = [[getattr(r, field) or 'None' for _, field in fields] for r in res]
		for r in results:
			r[-1] = url_for('get_food', food_id=r[-1])
		sortidx = 2
	elif entity_type == 'disease':
		res = Disease.query.all()
		fields = [
			['Disease ID', 'disease_id'],
			['Disease Category', 'disease_category'],
			['Disease Name', 'disease_name'],
			['Disease Synonyms', 'disease_synonyms'],
			['Explore', 'disease_id'],
		]
		results = [[getattr(r, field) or 'None' for _, field in fields] for r in res]
		for r in results:
			r[-1] = url_for('get_disease', disease_id=r[-1])
		sortidx = 2
	elif entity_type == 'chemical':
		res = Chemical.query.all()
		fields = [
			['PubChem ID', 'pubchem_id'],
			['Common Name', 'common_name'],
			['Functional Group(s)', 'functional_group'],
			['SMILES', 'smiles'],
			['Explore', 'pubchem_id'],
		]
		results = [[getattr(r, field) for _, field in fields] for r in res]
		for r in results:
			r[-1] = url_for('get_chemical', pubchem_id=r[-1])
		sortidx = 1
	elif entity_type == 'gene':
		res = Gene.query.all()
		fields = [
			['Entrez Gene ID', 'gene_id'],
			['Gene Symbol', 'gene_symbol'],
			['Gene Name', 'gene_name'],
			['Gene Other Symbol', 'other_symbols'],
			['Gene Synonyms', 'synonyms'],
			['Explore', 'gene_id'],
		]
		results = [[getattr(r, field) or 'None' for _, field in fields] for r in res]
		for r in results:
			r[-1] = url_for('get_gene', gene_id=r[-1])
		sortidx = 2
	else:
		abort(404)

	return render_template('common/view_all.html', fields=fields, sortidx=sortidx,
                        results=results, type=entity_type)


@app.route('/dietrx/faq', methods=['GET'])
def faq():
	return render_template('common/faq.html', stats=stats)


@app.route('/dietrx/how_to_use', methods=['GET'])
def how_to_use():
	return render_template('common/how_to_use.html')


@app.route('/dietrx/contact_us', methods=['GET'])
def contact_us():
	return render_template('common/contact_us.html')
