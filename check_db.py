import asyncio
import motor.motor_asyncio
from bson.objectid import ObjectId
import json
import os

class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return super().default(o)

# Load MongoDB URL from .env file if possible
def get_mongodb_url_from_env():
    env_path = 'waggy-api/.env'
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if line.startswith('MONGODB_URL='):
                    return line.split('=', 1)[1].strip()
    return None

async def check_database():
    # MongoDB URLs - local and remote
    mongo_urls = [
        "mongodb://localhost:27017",
    ]
    
    # Try to get MongoDB URL from .env file
    remote_url = get_mongodb_url_from_env()
    if remote_url:
        mongo_urls.append(remote_url)
        print(f"Found remote MongoDB URL in .env file: {remote_url}")
    else:
        print("No remote MongoDB URL found in .env file")
        # Add the MongoDB URL from the screenshot
        mongo_urls.append("mongodb+srv://gavishap:SRhan55tu!!@buddy-dog-walking-app.xuvff.mongodb.net/")
    
    for mongo_url in mongo_urls:
        print(f"\n=== Checking MongoDB connection: {mongo_url} ===")
        
        try:
            # Connect to MongoDB
            client = motor.motor_asyncio.AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=5000)
            # Test the connection
            await client.admin.command('ping')
            print("Connection successful")
            
            # Check both databases
            databases = ["waggy", "waggy_sitters"]
            
            for db_name in databases:
                print(f"\n=== Checking database: {db_name} ===")
                db = client[db_name]
                
                # Check what collections exist
                collections = await db.list_collection_names()
                print(f"Collections in database: {collections}")
                
                if "users" in collections:
                    # Check users
                    users_count = await db.users.count_documents({})
                    print(f"Found {users_count} users in the collection")
                    
                    if users_count > 0:
                        # Get a sample of users
                        print("Sample user details (up to 3):")
                        users = await db.users.find().limit(3).to_list(length=3)
                        for i, user in enumerate(users):
                            print(f"\nUser {i+1}:")
                            # Only show email for privacy
                            print(f"Email: {user.get('email', 'No email')}")
                            print(f"Type: {user.get('user_type', 'No type')}")
                else:
                    print("No users collection found in this database")
        
        except Exception as e:
            print(f"Error connecting to {mongo_url}: {str(e)}")
    
    print("\nDone checking databases")

if __name__ == "__main__":
    asyncio.run(check_database()) 
