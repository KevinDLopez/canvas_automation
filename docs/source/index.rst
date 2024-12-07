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


The goal of this project is to automate the following:

- Cross-check student's names, ID numbers, email with Canvas
- Create Google Feedback Forms for team presentations
- Create Pages on Canvas containing Team Name, Research Topic, Paper link, Presentation link, etc.
- Create Quizzes on Canvas
- Download submission for specific students
- Download Google-form results and Post the grades for team members on Canvas
- Analyze Google-form results to find the top 3 presentations, grade distribution on all presentations, student's average feedback grading, and find unfair grading outliers.


The students need to submit the following files to their assignment:

#. A PDF of their presentation named ``presentation.pdf``
#. A PDF of their paper named ``paper.pdf``
#. A Quiz JSON file with questions and answers named ``quiz.json``

A basic ``quiz.json`` file should be the format of:

.. code-block:: json

    {
        "title": "File-Based Quiz with JSON FILE ",
        "description": "A quiz created from a JSON FILE.",
        "quiz_type": "assignment",
        "time_limit": 60,
        "shuffle_answers": true,
        "allowed_attempts": 1,
        "questions": [
            {
                "question_name": "History Question 1",
                "question_text": "Who was the first President of the United States?",
                "question_type": "multiple_choice_question",
                "points_possible": 10,
                "answers": [
                    { "answer_text": "George Washington", "answer_weight": 100 },
                    { "answer_text": "Thomas Jefferson", "answer_weight": 0 },
                    { "answer_text": "Abraham Lincoln", "answer_weight": 0 },
                    { "answer_text": "John Adams", "answer_weight": 0 }
                ]
            }
        ]
    }

Getting Started
---------------

How to use the application:
^^^^^^^^^^^^^^^^^^^^^^^^^^^
The professor (user of the application) would need to follow the steps below:

#. Download the submission from Canvas ( This is Tab 1)
#. Verify that the files are present and correct ( This is Tab 1)
#. Create the pages on Canvas for the team ( This is Tab 2)
#. Create the feedback forms and quizzes on Canvas. ( This is Tab 3)
#. Remove the feedback forms and quizzes then grade the assignment based on the feedback forms. ( This is Tab 3 )

All of the steps above will be done through the application.



Prerequisites
~~~~~~~~~~~~~
* Canvas access token configured
* Google email with permissions and a ``client_secrets.json`` file for testing

Installation
~~~~~~~~~~~~

Using Conda Environment
^^^^^^^^^^^^^^^^^^^^^^^
1. Create environment::

    conda env create -f pyqt-env.yml

2. Activate environment::

    conda activate pyqt-env

3. Update packages::

    conda env update -f pyqt-env.yml --prune

Using Python Requirements File
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
1. Create virtual environment::

    python -m venv venv

2. Activate virtual environment:

   * Windows::

       venv\Scripts\activate

   * macOS/Linux::

       source venv/bin/activate

3. Install requirements::

    pip install -r requirements.txt

Using the Application
--------------------
1. Start the application using one of these methods:

   * Run Python script::

       python GradingAutomationUI.py

   * Or download and run the executable from the latest release

     Note: For macOS users, you may need to allow opening apps from unknown developers

2. Configure the application:

   * Enter the Canvas class ID (e.g., ``15319``)
   * Provide your Canvas access token
   * Enter the presentation module title (e.g., ``Fall 2024 - Presentation``)

   .. image:: _static/canvas_config.png
      :width: 800
      :alt: Canvas Configuration Screenshot


3. Download student submissions and verification:

   * 1. First enter the the spreadsheet url for testing we used the following: https://docs.google.com/spreadsheets/u/0/d/1tuuIobh2R4KQJBxCPR60E0EFVW_jr9_l6Aaj3lx6qaQ/htmlview
   * 2. Enter the location where the files will be downloaded. This location is used to analyze what projects are missing from the spreadsheet, does that are missing will be allowed to be downloaded.
   * 3. Then click on verify projects to analyze the spreadsheet
   * 4. After the spreadsheet is verified, click on download submissions to download the missing projects. 
      * The download ui only shows when there is missing projects and need to be downloaded.
   * 5. After the files are downloaded, click on verify submissions to verify that the files are present and correct.
      * If everything is wrong with the student names or emails, it will be shown in the log window,
      * if anything is wrong with the files, it will be shown in the error column of the verification table.
   
   .. image:: _static/click_download.png
      :width: 800
      :alt: Click Download Button Screenshot

   Below is how the spreadsheet looks like:
   
   .. image:: _static/spreadsheet.png
      :width: 800
      :alt: spreadsheet


   | 
.. raw:: html

   <div style="clear: both; height: 40px;"></div>
   

4. Navigate to "Page Management" to create pages from group folders:
   * This page is used to create the pages on Canvas for the team.
   * Here, only the pages that passed the verification step will be shown.    
      * Is done like this because we can only publish pages that have all files correctly. 

   .. image:: _static/page_management.png
      :width: 800
      :alt: Page Management Screenshot

5. Use the "Forms and Quizzes Tab" to add feedback forms and quizzes:
   * This page is used to add the feedback forms and quizzes to the Canvas pages, and grade the assignment based on the feedback forms.
   * At the entrance of this tab, the program fetches the pages and see on what feedback they're on and postes it for every page. 
      * The status can be:
         * ``Not Created`` - means that the page is not created by the application.
         * ``Quiz and Feedback added``` - means that the quiz and feedback forms are added to the page.
         * ``Done`` - means that the page is created and graded by the application.
         * ``No Local, No Spreadsheet`` - means that the page is not created because there are no local files and the page is not in the spreadsheet.
         * ``No Local, Yes Spreadsheet`` - means that the page is not created because there are no local files but the page is in the spreadsheet.
         * ``Evaluation Form`` - means that the page was manually. Keyword ``Evaluation`` is added by the professor, not by the application.
   * We have made it sot that it is not necessary for the page to be made by the application, pages made by manually can also be graded.
      * The requirements is that the feedback form ID needs to be added to the spreadsheet. 

   .. image:: _static/forms_quizzes.png
      :width: 800
      :alt: Forms and Quizzes Screenshot

6. After grading, view the grade distribution on Canvas:

   * After the gradin is done a image is attached to the page of the grade distribution histogram. 
   * Also, all the reposes used for grading are saved in a `.xslx` file under the same directory as the project graded. 
   
   .. image:: _static/grade_distribution.png
      :width: 800
      :alt: Grade Distribution Screenshot

7. Form Analysis

   * The last tab is used to analyze the feedback forms and find the top 3 presentations using the spreadsheet url from step 3.
   * First click the ``Aggregate Responses`` to fetch the responses from the feedback forms.
   * Then click on the ``Analyze Responses`` to analyze the responses.
   * The following analysis are done:
      * Distribution for all presentations - Shows the grade distribution across all team presentations
      * Each student average grading for others - Displays how each student grades their peers on average
      * Top 3 Presentations - Identifies the three highest rated presentations based on peer feedback
      * Student Outliers - Detects students who consistently grade significantly higher or lower than their peers. It uses the quartile method to find outliers (same as boxplot). 
      
   .. image:: _static/form_analysis.png
      :width: 800
      :alt: Form Analysis Screenshot

Setting up Canvas Access Token
------------------------------

1. Login to Canvas and navigate to Account Settings:

   .. image:: _static/canvas_settings.png
      :width: 200
      :alt: Canvas Settings Screenshot

2. Find the Approved Integrations section and click "New Access Token":

   .. image:: _static/access_token.png
      :width: 400
      :alt: Access Token Screenshot

3. Create your token:

   .. image:: _static/create_token.png
      :width: 500
      :alt: Create Token Screenshot

.. toctree::
   :maxdepth: 4
   :caption: Contents:




Setting up Google API
---------------------

* Go to Google Cloud Console ``https://console.cloud.google.com/`` 
* Create a new project
* Enable the Google Forms API. 
   * Enable Forms API  - ``https://console.cloud.google.com/apis/library/forms.googleapis.com``
   * Enable Sheets API - ``https://console.cloud.google.com/apis/library/sheets.googleapis.com``
   * Enable Drive API - ``https://console.cloud.google.com/apis/library/drive.googleapis.com``
* Enable beta users for the Google Forms API. ( Add users by their emails)
   ``https://console.cloud.google.com/apis/credentials/consent``
* Create credentials and download the ``client_secrets.json`` file. ( Create Credentials ->  OAuth Client ID )
   ``https://console.cloud.google.com/apis/credentials``
