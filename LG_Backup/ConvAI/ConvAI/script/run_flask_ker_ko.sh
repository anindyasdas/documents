# Run flask main module and jar file
java -jar apps/ker_ko/dataset/models/classifier/korean_bert/lgai-mecab-1.0.0.jar & 
python -m apps.ker_ko.knowledge_extraction.server.flask_main