from pymongo import MongoClient

# MongoDB connections
source_client = MongoClient('mongodb://admin:Cir%5EPnq%406A@51.195.235.59:27017/smFeeds?authSource=admin')
source_db = source_client['smFeeds']
source_collection = source_db['xtweets']

destination_client = MongoClient('mongodb://admin:V5%26uX%233L%5E8rQ@mongo.pnq.co.in:27017/pnq?authSource=admin')
destination_db = destination_client['pnq']
destination_collection = destination_db['xtweets']

# Copy data from source to destination
def copy_collection(source_collection, destination_collection):
    # Find all documents in the source collection
    documents = source_collection.find()

    # Insert or update documents in the destination collection
    for document in documents:
        # Use replace_one with upsert=True to update or insert documents
        destination_collection.replace_one({'_id': document['_id']}, document, upsert=True)

    print("Data copied successfully from 'xFeeds.xtweets' to 'pnq.xtweets'.")

# Run the copy operation
copy_collection(source_collection, destination_collection)

# Close connections
source_client.close()
destination_client.close()
