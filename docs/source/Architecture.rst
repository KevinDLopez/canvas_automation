Architecture
=============



Overview of the Canvas Automation System
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* The project is divided into two main parts: the backend and the frontend. 
   * The backend is responsible for interacting with the Canvas API and Google Forms API to automate the grading process.  In the UML diagram the backend is represented by Orange color. 
   * The frontend is a user interface that allows users to interact with the backend system. In the UML diagram the frontend is represented by Blue color.
   
   .. image:: _static/architecture/UML.png
      :alt: UML diagram 
      :width: 800

Backend Modules
~~~~~~~~~~~~~

* The backend is further divided into the following modules:
   * `CanvasServices <CanvasServices.html>`_: This module is responsible for interacting with the Canvas API to automate the grading process.
      * With in this module there is a sub-module called `CanvasServicesAPI <CanvasServices.html>`_ which is responsible for interacting with the Canvas API.
      * With in this module there is testing file called `test_canvas_service <CanvasServices.html#test-canvas-service>`_ which is responsible for testing the CanvasServicesAPI module.
      * With in this module there is a schema file called `schemas <CanvasServices.html#schemas>`_ which is responsible for defining the data schemas used by the CanvasServices module. Using this schema file it allowed us to develop efficient code with low amount of errors.
   * `GoogleServices <GoogleServices.html>`_: This module is responsible for interacting with the Google Forms API to automate the grading process.
      *  `GoogleServicesAPI <GoogleServices.html>`_  is responsible for interacting with the Google Forms API.
      *  `test_google_service <GoogleServices.html#test-google-service>`_  is responsible for testing the GoogleServicesAPI module.
      *  `schemas <GoogleServices.html#schemas>`_  is responsible for defining the data schemas used by the GoogleServices module. Using this schema file it allowed us to develop efficient code with low amount of errors. The schemas were made using pydantic or typedict. 
   * `Logging <Logging.html>`_: This module is responsible for logging the activities of the backend or front end system.
   
   
Frontend Modules
~~~~~~~~~~~~~

* The frontend is further divided into the following modules:
   * `GradingAutomationUI <GradingAutomationUI.html>`_: This file is responsible for creating the user interface for the grading automation system.  
      * There is a `schemas <schemas>`_ file that contains schemas used in the GradingAutomationUI file.
