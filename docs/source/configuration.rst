Configuration
============

Setting up Canvas Access Token
----------------------------

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

Setting up Google API
-------------------

1. Go to Google Cloud Console ``https://console.cloud.google.com/``
2. Create a new project
3. Enable required APIs:
   * Forms API
   * Sheets API
   * Drive API
4. Enable beta users for the Google Forms API
5. Create credentials and download ``client_secrets.json``