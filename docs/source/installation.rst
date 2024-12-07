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
