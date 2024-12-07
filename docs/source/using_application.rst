Using the Application ( Manual )
-------------------------------

Start the application using one of these methods:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

   * Run Python script::

       python GradingAutomationUI.py

   * Or download and run the executable from the latest release

     Note: For macOS users, you may need to allow opening apps from unknown developers

Configure the application:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   * Enter the Canvas class ID (e.g., ``15319``)
   * Provide your Canvas access token
   * Enter the presentation module title (e.g., ``Fall 2024 - Presentation``)

   .. image:: _static/canvas_config.png
      :width: 800
      :alt: Canvas Configuration Screenshot


Download student submissions and verification:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   * First enter the the spreadsheet url for testing we used the following: https://docs.google.com/spreadsheets/u/0/d/1tuuIobh2R4KQJBxCPR60E0EFVW_jr9_l6Aaj3lx6qaQ/htmlview
   * Enter the location where the files will be downloaded. This location is used to analyze what projects are missing from the spreadsheet, does that are missing will be allowed to be downloaded.
   * Then click on verify projects to analyze the spreadsheet
   * After the spreadsheet is verified, click on download submissions to download the missing projects. 
      * The download ui only shows when there is missing projects and need to be downloaded.
   * After the files are downloaded, click on verify submissions to verify that the files are present and correct.
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
   

Navigate to "Page Management" to create pages from group folders:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   * This page is used to create the pages on Canvas for the team.
   * Here, only the pages that passed the verification step will be shown.    
      * Is done like this because we can only publish pages that have all files correctly. 

   .. image:: _static/page_management.png
      :width: 800
      :alt: Page Management Screenshot

Use the "Forms and Quizzes Tab" to add feedback forms and quizzes:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
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

After grading, view the grade distribution on Canvas:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   * After the gradin is done a image is attached to the page of the grade distribution histogram. 
   * Also, all the reposes used for grading are saved in a `.xslx` file under the same directory as the project graded. 
   
   .. image:: _static/grade_distribution.png
      :width: 800
      :alt: Grade Distribution Screenshot

Form Analysis
^^^^^^^^^^^^^
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
