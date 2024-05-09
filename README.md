# # Retail Ready

Retail Ready is a Flask application that helps manage and process item workflows, orders, and chargebacks for retail stores.

## Getting Started

These instructions will help you set up the project on your local machine for development and testing purposes.

### Prerequisites

- Python 3.x
- MySQL or another compatible database

### Installation

1. Clone the repository:
git clone https://github.com/your-repo/retail-ready.git

2. Create a virtual environment (recommended):
python -m venv retailready

3. Activate the virtual environment:
source retailready/bin/activate

4. Install the required dependencies:
pip install -r requirements.txt

5. Set up the database:

- Create a new database in MySQL or your preferred database management system.
- Update the `SQLALCHEMY_DATABASE_URI` in `app.py` with your database credentials.

6. Run the database migrations:
flask db upgrade

7. Start the Flask server:
flask run

The application should now be running at `http://localhost:5000`.


