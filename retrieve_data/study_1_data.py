import os
import json
import logging
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

# Load credentials from secrets.toml file in .streamlit
firebase_credentials_dict = dict(st.secrets["firebase_service_account"])
credentials = credentials.Certificate(firebase_credentials_dict)

# Initialize the Firebase Admin app with credentials
if not firebase_admin._apps:
    firebase_admin.initialize_app(credentials)

# Initialize Firestore client
db = firestore.client()

def retrive_all_survey_one():
    try:
        # Reference the collection
        survey_collection = db.collection("group_one_survey_one_responses")
        docs = survey_collection.stream()
        
        # Retrieve all survey responses and save each to a separate file
        for doc in docs:
            survey_data = doc.to_dict()
            survey_response = survey_data["survey_data"]
            prolific_id = survey_data["prolific_id"]
            
            # Store each survey response in a separate JSON file
            output_directory = "retrieve_data/data"
            os.makedirs(output_directory, exist_ok=True)
            with open(os.path.join(output_directory, f"survey_one_response_{prolific_id}.json"), "w") as outfile:
                json.dump(survey_response, outfile)
                
        logging.info("All survey responses successfully retrieved and stored locally in separate files.")
        return True

    except Exception as e:
        logging.error(f"Failed to retrieve survey responses from Firebase Firestore: {e}")
        return None


def retrive_all_survey_two():
    """
    Retrieve all survey two responses from Firestore and save each to a separate file.
    """
    try:
        # Reference the collection
        survey_collection = db.collection("group_one_survey_two_responses")
        docs = survey_collection.stream()

        # Store each survey response in a separate JSON file
        output_directory = "retrieve_data/data"
        os.makedirs(output_directory, exist_ok=True)

        # Retrieve all survey responses and save each to a separate file
        for doc in docs:
            survey_data = doc.to_dict()
            prolific_id = survey_data["prolific_id"]
            survey_response = {}
            survey_response['all_detections'] = survey_data["complete_detections"]
            survey_response['necessary_options'] = survey_data["user_selections"]
            survey_response['reasons'] = survey_data['survey_info']

            # Store each survey response in a separate JSON file
            with open(os.path.join(output_directory, f"survey_two_response_{prolific_id}.json"), "w") as outfile:
                json.dump(survey_response, outfile)

        logging.info("All survey responses successfully retrieved and stored locally in separate files.")
        return True

    except Exception as e:
        logging.error(f"Failed to retrieve survey responses from Firebase Firestore: {e}")
        return None

def retrive_all_survey_three():
    try:
        # Reference the collection
        survey_collection = db.collection("group_one_survey_three_responses")
        docs = survey_collection.stream()
        
        # Retrieve all survey responses and save each to a separate file
        for doc in docs:
            survey_data = doc.to_dict()
            survey_response = survey_data["survey_data"]
            prolific_id = survey_data["prolific_id"]
            
            # Store each survey response in a separate JSON file
            output_directory = "retrieve_data/data"
            os.makedirs(output_directory, exist_ok=True)
            with open(os.path.join(output_directory, f"survey_three_response_{prolific_id}.json"), "w") as outfile:
                json.dump(survey_response, outfile)
                
        logging.info("All survey responses successfully retrieved and stored locally in separate files.")
        return True

    except Exception as e:
        logging.error(f"Failed to retrieve survey responses from Firebase Firestore: {e}")
        return None


# Define the function to retrieve all chat histories from Firestore
def retrieve_all_chat_histories():
    try:
        # Reference the collection
        chat_collection = db.collection("group_one_chat_histories")
        docs = chat_collection.stream()
        
        # Retrieve all chat histories and save each to a separate file
        for doc in docs:
            chat_data = doc.to_dict()
            chat_history = chat_data["chat_history"]
            prolific_id = chat_data["prolific_id"]
            # print(chat_data["chat_history"])
            # print(chat_data["prolific_id"])
            
            # Store each chat history in a separate JSON file
            output_directory = "retrieve_data/data"
            os.makedirs(output_directory, exist_ok=True)
            # Store each chat history in a separate JSON file
            with open(os.path.join(output_directory, f"chat_history_{prolific_id}.json"), "w") as outfile:
                json.dump(chat_history, outfile)
            # Store each chat history in a separate text file
            with open(os.path.join(output_directory, f"chat_history_{prolific_id}.txt"), "w") as outfile:
                outfile.write(chat_history)
                
        logging.info("All chat histories successfully retrieved and stored locally in separate files.")
        return True

    except Exception as e:
        logging.error(f"Failed to retrieve chat histories from Firebase Firestore: {e}")
        return None

def main():
    # Retrieve all chat histories and survey responses
    if retrieve_all_chat_histories():
        print("All chat histories retrieved and saved locally.")
    else:
        print("No chat history found or an error occurred.")
    
    # # Retrieve all survey one responses
    if retrive_all_survey_one():
        print("All survey one responses retrieved and saved locally.")
    else:
        print("No survey response found or an error occurred.")

    # # Retrieve all survey two responses
    if retrive_all_survey_two():
        print("All survey two responses retrieved and saved locally.")
    else:
        print("No survey response found or an error occurred.")

    # # Retrieve all survey three responses
    if retrive_all_survey_three():
        print("All survey three responses retrieved and saved locally.")
    else:
        print("No survey response found or an error occurred.")

if __name__ == "__main__":
    main()
