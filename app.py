from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
import io
from PyPDF2 import PdfReader
import requests

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:password@localhost/RetailReady'
db = SQLAlchemy(app)
migrate = Migrate(app, db)
# Enable CORS
CORS(app, resources={r"/*": {"origins": ["http://localhost:3000"]}}, methods=["GET", "POST"], allow_headers=["Content-Type"])

class ItemWorkflow(db.Model):
    __tablename__ = 'item_workflow'
    item_id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.Integer)
    item_name = db.Column(db.String(255))
    workflow_guide = db.Column(db.Text)
    package_id = db.Column(db.Integer)
    images = db.Column(db.String(255))

class PackSpecification(db.Model):
    __tablename__ = 'pack_specification'
    pack_spec_id = db.Column(db.Integer, primary_key=True)
    length = db.Column(db.Float)
    width = db.Column(db.Float)
    height = db.Column(db.Float)
    material_type = db.Column(db.String(255))

class RetailStore(db.Model):
    __tablename__ = 'retail_store'
    store_id = db.Column(db.Integer, primary_key=True)
    store_name = db.Column(db.String(255))
    # Add more metadata columns as needed

class Order(db.Model):
    __tablename__ = 'orders'
    order_id = db.Column(db.Integer, primary_key=True)
    destination = db.Column(db.String(255)) # This is the store ID
    item_ids = db.Column(db.JSON)
    status = db.Column(db.String(50))

with app.app_context():
    db.create_all()

# I am using S3 for blob storage. Keeping the user manuals in a traditional database would be a bad idea. Cost & latency.
@app.route('/upload-manual-to-s3', methods=['POST'])
def upload_manual_to_s3():
    # Retrieve the uploaded manual file from the request
    manual_file = request.files['manual']

    # Upload the manual file to an S3 bucket
    # This is where you would use the Boto3 library to interact with AWS S3
    # For the sake of this example, I'll just return a success message
    return jsonify({'message': 'Manual uploaded to S3 successfully'})
    
@app.route('/create-new-item', methods=['POST'])
def create_new_item():
    # Parameters: item_name (or item_id), store_id
    # Goal: Create a new item in the Item Workflow table

    # This function will grab the user manual for the specified store. 
    # It will then go though the manual and produce a workflow for that item (using LLMs).
    # It will add that item to the database (Item Workflow)
    return "Success"

@app.route('/process-manual', methods=['POST'])
def process_manual():
    if request.method == 'OPTIONS':
        # Preflight request. Reply successfully:
        response = jsonify({'result': 'Preflight request successful'})
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        response.headers.add('Access-Control-Max-Age', '3600')  # cache for 1 hour
        return response
    # Retrieve the uploaded user manual file from the request
    manual_file = request.files['manual']

    # Create a BytesIO object to read the file data
    file_data = io.BytesIO(manual_file.read())

    # Create a PDF reader object
    pdf_reader = PdfReader(file_data)

    # Get the first page of the PDF
    page = pdf_reader.pages[0]

    # Extract the text from the page
    text = page.extract_text()

    # Split the text into words
    words = text.split()

    # Get the first ten words
    first_ten_words = words[:10]

    # Join the words into a string
    result = ' '.join(first_ten_words)

    response = jsonify({'result': result})
    response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'POST')
    response.headers.add('Access-Control-Max-Age', '3600')
    return response

    # Process the user manual using the LLM
    # ...

    # Extract relevant information and store it in the database
    # ...

    # Return a success response

@app.route('/process-order', methods=['POST'])
def process_order():
    # Retrieve the uploaded order PDF file from the request
    order_file = request.files['order']

    # Create a BytesIO object to read the file data
    file_data = io.BytesIO(order_file.read())

    # Create a PDF reader object
    pdf_reader = PdfReader(file_data)

    # [NOTE] For the sake of brevity I am using a basic splitter. In a real implementation I would use a LLM potentially to grab all the items within the order.
    # I am also making the assumption that these PDFs are modern PDFs and are not scanned documents. Unstructured is a tool that can help with this down the line.

    # Get the first page of the PDF
    page = pdf_reader.pages[0]

    # Extract the text from the page
    text = page.extract_text()

    # Split the text into lines
    lines = text.split('\n')

    # Extract the order items from the lines (assuming each line represents an item)
    order_items = [line.strip() for line in lines if line.strip()]

    # Initialize an empty list to store the workflow guides
    workflow_guides = []

    # Iterate over each order item
    for item in order_items:
        # Check if the item exists in the item workflow table
        # I am making assumptions here as I don't know what a real order looks like. This would change if items have IDs vs Names, etc.
        item_workflow = ItemWorkflow.query.filter_by(item_name=item).first()

        if item_workflow:
            # If the item exists, retrieve its workflow guide and append it to the list
            workflow_guides.append(item_workflow.workflow_guide)
        else:
            # If the item doesn't exist, create a new item in the database
            # This would be a good place to call the create_new_item function
            response = requests.post('http://localhost:5000/create-new-item', json={'item_name': item})

    # Join the workflow guides into a single string
    tablet_workflow = '\n'.join(workflow_guides)

    # Return the tablet workflow as a JSON response
    response = jsonify({'workflow': tablet_workflow})
    response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'POST')
    response.headers.add('Access-Control-Max-Age', '3600')
    return response

# This endpoint 
@app.route('/update-item-workflow', methods=['POST'])
def update_item_workflow():
    # Retrieve the item ID and the updated workflow guide from the request
    item_id = request.json['item_id']
    chargeback_reason = request.json['chargeback_reason']

    # This would be highly experimental. I'd probably elect to do this manually at first. 
    # But what you could do is is fetch the workflow for the item based on the item_id. 
    # You could then grab the user manual from the Item Workflow Table using the item_id
    # Then you could use the LLM to update the workflow based on the chargeback reason.

    return jsonify({'message': 'Workflow guide updated successfully'})