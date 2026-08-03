Multi-Agent Financial Research System

Overview
This project is a Milestone 1 implementation of a Multi-Agent Financial Research System using Python, MongoDB, and ChromaDB.

Features
MongoDB connection using PyMongo
CRUD operations
Collections: users, sessions, documents, chunks, embeddings, extracted_metrics, red_flags
ChromaDB vector storage
SentenceTransformer embeddings
Semantic similarity search
MongoDB + ChromaDB integration

Project Structure

test_connection.py
mongodb_helper.py
chromadb_helper.py
embedding_storage.py
embedding_search.py
integration_test.py
chromadb_test.py
chroma_storage/
README.md

Installation
Clone the repository.
Install Python 3.12 or later.
Install MongoDB Community Edition and MongoDBCompass.
Install dependencies:
pip install -r requirements.txt
Start MongoDB.
Run the project scripts.

Technologies
Python
MongoDB
MongoDB Compass
PyMongo
ChromaDB
SentenceTransformers

Milestone Summary

Day 1 - MongoDB Setup
Day 2 - ChromaDB
Day 3 - Database Schema
Day 4 - Embedding Storage
Day 5 - Integration
Day 6 - Testing
Day 7 - Documentation