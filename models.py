from dietrx import db
from dietrx.search import add_to_index, remove_from_index

class SearchableMixin(object):
    @classmethod
    def reindex(cls, id):
        for obj in cls.query:
            add_to_index(cls.__tablename__, obj, id)



class Food(SearchableMixin, db.Model):
    __searchable__ = ['display_name', 'common_names', 'scientific_name', 'food_category']
    __searchboost__ = ['display_name^4', 'common_names', 'scientific_name', 'food_category^3']
    __separators__ = {'common_names': '; '}
    food_id = db.Column(db.String(128), primary_key=True)
    display_name = db.Column(db.String(128))
    common_names = db.Column(db.Text)
    scientific_name = db.Column(db.Text)
    food_category = db.Column(db.String(128))
    tax_id = db.Column(db.Integer)
    genes = db.relationship("Gene", secondary="food_gene")
    diseases = db.relationship("Disease", secondary="food_disease")

    def __repr__(self):
        return '<Food {}>'.format(self.display_name)



class Disease(SearchableMixin, db.Model):
    __searchable__ = ['disease_name', 'disease_synonyms', 'disease_category']
    __searchboost__ = ['disease_name^4', 'disease_synonyms', 'disease_category^3']
    __separators__ = {'disease_synonyms': '|', 'disease_category': '|'}
    disease_id = db.Column(db.String(128), primary_key=True)
    disease_name = db.Column(db.Text)
    disease_synonyms = db.Column(db.Text)
    disease_category = db.Column(db.Text)
    genes = db.relationship("Gene", secondary="disease_gene")
    foods = db.relationship("Food", secondary="food_disease")

    def __repr__(self):
        return '<Disease {}>'.format(self.disease_name)


class Gene(SearchableMixin, db.Model):
    __searchable__ = ['gene_id', 'gene_symbol', 'gene_name', 'other_symbols', 'synonyms']
    __searchboost__ = ['gene_symbol', 'gene_name^3', 'other_symbols', 'synonyms^3']
    __separators__ = {'other_symbols': '|', 'synonyms': '|'}
    gene_id = db.Column(db.String(128), primary_key=True)
    gene_name = db.Column(db.Text)
    gene_symbol = db.Column(db.String(128))
    organism = db.Column(db.Text)
    other_symbols = db.Column(db.Text)
    synonyms = db.Column(db.Text)
    diseases = db.relationship('Disease', secondary='disease_gene')
    foods = db.relationship('Food', secondary='food_gene')

    def __repr__(self):
        return '<Gene {}>'.format(self.gene_id)


class Chemical(SearchableMixin, db.Model):
    __searchable__ = ['common_name', 'iupac_name', 'synonyms']
    __autocomplete__ = ['common_name', 'synonyms']
    __searchboost__ = ['common_name^3', 'iupac_name', 'synonyms^2']
    __separators__ = {'synonyms': '|'}
    diseases = db.relationship("Disease", secondary="chemical_disease")
    foods = db.relationship("Food", secondary="food_chemical")

    pubchem_id = db.Column(db.Integer, primary_key=True)
    common_name = db.Column(db.Text, nullable=True, index=True)
    synonyms = db.Column(db.Text, nullable=True, index=True)
    database = db.Column(db.Text, nullable=True, index=True)
    iupac_name = db.Column(db.Text, nullable=True, index=True)
    molecular_formula = db.Column(db.Text, index=False)
    functional_group = db.Column(db.Text, nullable=True, index=True)
    functional_group_idx = db.Column(db.Text, nullable=True, index=True)
    smiles = db.Column(db.Text, index=False)
    isomeric_smiles = db.Column(db.Text, index=False)
    molecular_weight = db.Column(db.Float, index=False,
                                 nullable=True)
    num_hydrogen_atoms = db.Column(db.Integer, index=False, nullable=True)
    num_heavy_atoms = db.Column(db.Integer, index=False, nullable=True)
    num_rings = db.Column(db.Integer, index=False, nullable=True)
    num_rotatablebonds = db.Column(db.Integer, index=False, nullable=True)
    number_of_aromatic_bonds = db.Column(db.Integer, index=False,
                                         nullable=True)
    num_atoms = db.Column(db.Integer, index=False, nullable=True)
    hba_count = db.Column(db.Integer, index=False, nullable=True)
    hbd_count = db.Column(db.Integer, index=False, nullable=True)
    hyrophilic_index = db.Column(db.Float, index=False,
                                 nullable=True)
    alogp = db.Column(db.Float, index=False, nullable=True)

    def __repr__(self):
        return '<Molecule {}>'.format(self.pubchem_id)


class Food_disease(db.Model):
    food_id = db.Column(db.String(128), db.ForeignKey('food.food_id'), primary_key=True)
    disease_id = db.Column(db.String(128), db.ForeignKey('disease.disease_id'), primary_key=True)
    positive_pmid = db.Column(db.String(512), index=False)
    negative_pmid = db.Column(db.String(512), index=False)
    pubchem_id = db.Column(db.String(512), index=False)
    weight = db.Column(db.Integer, index=True)
    food = db.relationship("Food", backref=db.backref('food_disease'))
    disease = db.relationship("Disease", backref=db.backref('food_disease'))

    def __repr__(self):
        return '<Food Disease {} {}>'.format(self.food_id, self.disease_id)


class Disease_gene(db.Model):
    gene_id = db.Column(db.String(128), db.ForeignKey('gene.gene_id'), primary_key=True)
    disease_id = db.Column(db.String(128), db.ForeignKey('disease.disease_id'), primary_key=True)
    reference = db.Column(db.String(100))
    via_chemicals = db.Column(db.String(512), index=False)
    disease = db.relationship("Disease", backref=db.backref('disease_gene'))
    gene = db.relationship("Gene", backref=db.backref('disease_gene'))

    def __repr__(self):
        return '<Disease Gene {}>'.format(self.gene_id)


class Food_gene(db.Model):
    food_id = db.Column(db.String(128), db.ForeignKey('food.food_id'), primary_key=True)
    gene_id = db.Column(db.String(128), db.ForeignKey('gene.gene_id'), primary_key=True)
    via_diseases = db.Column(db.String(512), index=False)
    via_chemicals = db.Column(db.String(512), index=False)
    food = db.relationship("Food", backref=db.backref('food_gene'))
    gene = db.relationship("Gene", backref=db.backref('food_gene'))

    def __repr__(self):
        return '<Food Gene {}>'.format(self.food_id)


class References(db.Model):
    pmid = db.Column(db.Integer, primary_key=True)
    authors = db.Column(db.String(512))
    date = db.Column(db.String(128))
    journal_name = db.Column(db.String(512))
    journal_name_abbr = db.Column(db.String(512))
    publication_type = db.Column(db.String(512))
    title = db.Column(db.String(1024))

    def __repr__(self):
        return '<References {}>'.format(self.pmid)


class Chemical_disease(db.Model):
    pubchem_id = db.Column(db.String(128), db.ForeignKey('chemical.pubchem_id'), primary_key=True)
    disease_id = db.Column(db.String(128), db.ForeignKey('disease.disease_id'), primary_key=True)
    type_relation = db.Column(db.String(512))
    via_genes = db.Column(db.String(512), index=False)
    chemical = db.relationship("Chemical", backref=db.backref('chemical_disease'))
    disease = db.relationship("Disease", backref=db.backref('chemical_disease'))

    def __repr__(self):
        return '<Chemical Disease {}>'.format(self.pubchem_id)


class Chemical_gene(db.Model):
    pubchem_id = db.Column(db.String(128), db.ForeignKey(
        'chemical.pubchem_id'), primary_key=True)
    gene_id = db.Column(db.String(128), db.ForeignKey(
        'gene.gene_id'), primary_key=True)
    interaction_actions = db.Column(db.Text)
    via_diseases = db.Column(db.String(512), index=False)
    chemical = db.relationship(
        "Chemical", backref=db.backref('chemical_gene'))
    gene = db.relationship(
        "Gene", backref=db.backref('chemical_gene'))

    def __repr__(self):
        return '<Chemical Gene {}>'.format(self.pubchem_id)


class Food_chemical(db.Model):
    food_id = db.Column(db.String(128), db.ForeignKey(
        'food.food_id'), primary_key=True)
    pubchem_id = db.Column(db.String(128), db.ForeignKey(
        'chemical.pubchem_id'), primary_key=True)
    content = db.Column(db.Text)
    references = db.Column(db.Text)
    type_relation = db.Column(db.String(100))
    inference_network = db.Column(db.Text)
    food = db.relationship("Food", backref=db.backref('food_chemical'))
    chemical = db.relationship(
        "Chemical", backref=db.backref('food_chemical'))

    def __repr__(self):
        return '<Food Chemical {}>'.format(self.food_id)
