// MongoDB initialization script
db = db.getSiblingDB('tanya_mail');

// Create collection for PDF documents
db.createCollection('pdf_docs');

// Create indexes for better performance
db.pdf_docs.createIndex({ "filename": 1 });
db.pdf_docs.createIndex({ "doc_id": 1 }, { unique: true });
db.pdf_docs.createIndex({ "file_hash": 1 });
db.pdf_docs.createIndex({ "kategori": 1 });

print('Tanya Ma'il database initialized successfully!');
