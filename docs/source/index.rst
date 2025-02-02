.. Access Amherst documentation master file, created by
   sphinx-quickstart on Tue Oct 29 20:08:27 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Access Amherst's Documentation!
====================================================

Access Amherst is a web application created to connect Amherst College students through organized, accessible, and diverse event updates on campus. The platform provides real-time information on campus events, allowing students to plan their schedules effectively.

This project is made possible through i2i (Ideas 2 Innovation) initiative, a student-led venture accelerator, at Amherst College.

Overview
========

Access Amherst aims to make it easier for students to discover and participate in events around the campus, fostering a stronger community.

Getting Started
===============

To clone the app, run in terminal:

.. code-block:: bash

   git clone https://github.com/ac-i2i-engineering/access-amherst.git
   cd access-amherst

Set up a virtual environment and activate it to "containerize" the dependencies:

.. code-block:: bash

   python3 -m venv env
   source env/bin/activate

To run the app locally, run:

.. code-block:: bash

   pip install -r requirements.txt
   cd access_amherst_backend
   python manage.py makemigrations
   python manage.py migrate
   python manage.py runserver

Contents
========

.. toctree::
   :maxdepth: 1
   :caption: Contents:

   event_model
   rss_scraper
   email_scraper
   calendar_scraper
   parse_database
   generate_map   

Additional Resources
====================

For more information on how to contribute, report issues, or request features, please refer to our [GitHub repository](https://github.com/ac-i2i-engineering/access-amherst).
