# Configuration file for the Sphinx documentation builder.  # noqa: D100
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "monawhat"
copyright = "2025, DirtyVader"
author = "DirtyVader"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx_rtd_theme"
]

templates_path = ["_templates"]
exclude_patterns = [] # type: ignore


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

# html_theme = "alabaster"
html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

# -- Napoleon settings
napoleon_google_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
