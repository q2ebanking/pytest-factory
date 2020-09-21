"""
this module writes pytest-factory tests created by parameterization
with fixtures ready to go to a file for the user to review, modify
and execute.
TODO writes tests. probably using some templates
TODO gets called by CLI
TODO gets invoked in pytest_generate_tests after tests created
"""
from pytest import Item
# from jinja import template


def takin_yer_jerb(item: Item):
    """
    generates code from item
    """
    item.session