.. access_amherst_backend documentation master file, created by
   sphinx-quickstart on Tue Oct 29 20:08:27 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Access Amherst's Documentation!
====================================

Access Amherst is a a web app to connect Amherst College students in a more convenient, intimate, and diverse way!

This project is made possible through i2i (Ideas 2 Innovation) initiative, a student-led venture accelerator, at Amherst College.

Getting Started
===============
To clone the app, run in terminal:

.. code-block:: python

   git clone https://github.com/ac-i2i-engineering/access-amherst.git
   cd access-amherst

Set-up a virtual environment and activate it to "containerize" the dependencies:

.. code-block:: python

   python3 -m venv env
   source env/bin/activate

To run the app locally, run:

.. code-block:: python

   pip install -r requirements.txt
   cd access_amherst_backend
   python manage.py makemigrations
   python manage.py migrate
   python manage.py runserver

Contents
===============

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   event_model
   rss_scraper
   email_scraper

