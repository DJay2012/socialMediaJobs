from pymongo import MongoClient
from datetime import datetime, timedelta
import pytz
from concurrent.futures import ThreadPoolExecutor, as_completed

# MongoDB connection URI
MONGO_URI = 'mongodb://admin:Cir%5EPnq%246A@57.128.169.41:27017/'


def process_document(document, destination_collection):
    ist = pytz.timezone("Asia/Kolkata")
    
    
    if 'createdAt' in document:
        document['createdAt'] = document['createdAt'].astimezone(ist)
    
    
    destination_collection.replace_one({'_id': document['_id']}, document, upsert=True)


def copy_collection_by_date(source_collection, destination_collection, start_date, end_date):
    current_date = start_date

    
    with ThreadPoolExecutor(max_workers=5) as executor:  # Adjust `max_workers` as needed
        futures = []

        while current_date <= end_date:
            next_date = current_date + timedelta(days=1)

            
            documents = source_collection.find({
                'createdAt': {
                    '$gte': current_date,
                    '$lt': next_date
                }
            })

           
            for document in documents:
                
                futures.append(executor.submit(process_document, document, destination_collection))

            print(f"Submitted tasks for date: {current_date.strftime('%Y-%m-%d')} in IST.")
            current_date = next_date

      
        for future in as_completed(futures):
            try:
                future.result()  
            except Exception as e:
                print(f"Error processing document: {e}")

    print("Data copy by date with multithreading completed successfully.")


def main():
    
    source_client = MongoClient(MONGO_URI)
    source_db = source_client['xFeeds']
    source_collection = source_db['facebook']

    destination_client = MongoClient(MONGO_URI)
    destination_db = destination_client['pnq']
    destination_collection = destination_db['Newfacebook']

    
    end_date = datetime.now(pytz.utc) - timedelta(days=2)
    start_date = datetime.now(pytz.utc)

   
    copy_collection_by_date(source_collection, destination_collection, start_date, end_date)

    
    source_client.close()
    destination_client.close()


if __name__ == "__main__":
    main()
