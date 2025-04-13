from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, BooleanField


class ChemicalSearchForm(FlaskForm):
    common_name = StringField('Common Name')
    iupac_name = StringField('IUPAC Name')
    pubchem_id = IntegerField('PubChem ID')
    functional_group = StringField('Functional Group')
    bitter_taste = BooleanField('Bitter')
    sweet_taste = BooleanField('Sweet')
    tasteless_taste = BooleanField('Tasteless')
    supernaturaldb = BooleanField('Super Natural II')
    flavordb = BooleanField('FlavorDB')
    drugbank = BooleanField('Drugbank')
    curateddb = BooleanField('CuratedDB')
    predicted = BooleanField('Include BitterSweet Predictions')
    smiles = StringField()
    search = SubmitField('Search')

    # Advanced search
    molecular_weight = StringField(
        'Molecular Weight',
        render_kw={"placeholder": "e.g. 500 OR 0:1000"})

    hba_count = StringField(
        'Hydrogen Bond Acceptors',
        render_kw={"placeholder": "e.g. 2 OR 3:5"})

    hbd_count = StringField(
        'Hydrogen Bond Donors',
        render_kw={"placeholder": "e.g. 4 OR 6:8"})

    number_of_aromatic_bonds = StringField(
        'Number of Aromatic Bonds',
        render_kw={"placeholder": "e.g. 2 OR 5:10"})

    num_rings = StringField(
        'Number of Rings',
        render_kw={"placeholder": "e.g. 4 OR 10:20"})

    num_rotatablebonds = StringField(
        'Number of Rotatable Bonds',
        render_kw={"placeholder": "e.g. 7 OR 1:5"})

    alogp = StringField(
        'AlogP',
        render_kw={"placeholder": "e.g. 2 OR -1:0.5"})
