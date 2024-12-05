.. GradingAutomation documentation master file, created by
   sphinx-quickstart on Tue Dec  3 15:10:45 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

GradingAutomation Documentation
===============================

Welcome to GradingAutomation's documentation. This tool helps automate the grading process for Canvas 574 with the use of Canvas API, Google Forms API, and Python.

This project is made by Jerry Wu and Kevin Lopez.

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

#. Download the submission from Canvas
#. Verify that the files are present and correct
#. Create the pages on Canvas for the team
#. Create the feedback forms and quizzes on Canvas.
#. Remove the feedback forms and quizzes then grade the assignment based on the feedback forms.

All of the steps above will be done through the application.

Now, we will go into more detail on each step.
#. Download the submission from canvas:
   To download the submission from Canvas, the professor would need to go to the assignment in Canvas and download the submissions as a zip file.
   To automate this we added a button to download all the submissions and unzip them in the folder of the user id.
   Since only the  students presenting the application will download the files for all students.

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

Running the Application
-----------------------
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

2. Download the submissions from Canvas:

   .. image:: _static/download_submissions.png
      :width: 800
      :alt: Download Submissions Screenshot

3. Verify selected projects:

   .. image:: _static/verify_projects.png
      :width: 800
      :alt: Verify Projects Screenshot

4. Navigate to "Page Management" to create pages from group folders:

   .. image:: _static/page_management.png
      :width: 800
      :alt: Page Management Screenshot

5. Use the "Forms and Quizzes Tab" to add feedback forms and quizzes:

   .. image:: _static/forms_quizzes.png
      :width: 800
      :alt: Forms and Quizzes Screenshot

6. After grading, view the grade distribution on Canvas:

   .. image:: _static/grade_distribution.png
      :width: 800
      :alt: Grade Distribution Screenshot

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

   modules
