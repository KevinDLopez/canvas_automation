# Setting up python 
1. Create Env. `conda env create -f pyqt-env.yml` 
2. Activate `conda activate pyqt-env` 
3. Update packages `conda env update -f pyqt-env.yml --prune`

# Running *canvas_data.py* script
1. Create an `.env` file and store your canvas access token as `API_TOKEN`


# Running google script
0. Setup google project with API support, allow users to test ap!
1. Download credentials
2. The credentials are not pushed to git, it should be a `./client_secrets.json` 
3. run the python script `python ./GoogleServices/GoogleServices.py/` or use the `./google_forms.ipynb`