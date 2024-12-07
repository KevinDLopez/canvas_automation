.. GradingAutomation documentation master file, created by
   sphinx-quickstart on Tue Dec  3 15:10:45 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

GradingAutomation Documentation
===============================

This project was developed by:

* Kevin Lopez (Kevin.LopezChavez01@student.csulb.edu)
* Jerry Wu (jerry.wu01@student.csulb.edu)

Welcome to GradingAutomation's documentation. This tool helps automate the grading process for Canvas 574 with the use of
`Canvas API <https://canvas.instructure.com/doc/api/index.html>`_,
`Google Forms API <https://developers.google.com/forms/api/reference/rest>`_,
`pydantic <https://docs.pydantic.dev/latest/>`_ for schema verification,
`pandas <https://pandas.pydata.org/>`_ for data analysis,
and `Python <https://www.python.org/>`_ for the programming language.

Project Goals
-------------
The goal of this project is to automate the following:

- Cross-check student's names, ID numbers, email with Canvas
- Create Google Feedback Forms for team presentations
- Create Pages on Canvas containing Team Name, Research Topic, Paper link, Presentation link, etc.
- Create Quizzes on Canvas
- Download submission for specific students
- Download Google-form results and Post the grades for team members on Canvas
- Analyze Google-form results to find the top 3 presentations, grade distribution on all presentations, student's average feedback grading, and find unfair grading outliers.

Table of Contents
-----------------

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   prerequisites
   installation
   using_application

.. toctree::
   :maxdepth: 2
   :caption: Configuration

   setting_up_canvas_access_token
   setting_up_google_api

.. toctree::
   :maxdepth: 2
   :caption: Development

   modules
