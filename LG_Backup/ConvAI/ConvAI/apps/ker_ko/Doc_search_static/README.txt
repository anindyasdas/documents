Step1:
Extract json from xml
python jsonextraction_engine.py "E:\work\Sprint 21\[MFL71728957]2046\ko-kr\xml\book\us_book.main.xml"


Output: consolidated.xml, manual.json, manual_final.json be stored at "E:\work\Sprint 21\[MFL71728957]2046\output_folder"
consolidated.xml--> It is consolidated xml file
manual.json--> first stage xml to json conversion(It has redundant tags and properties)
manual_final.json--> Final processed json file ( to be used by downstream tasks containing all sections)

Step2:

Extract Specfic section and image DB creation it will create a new json file with formatting data modelling and also
store image db

python datamodelling_engine.py

It will ask for input json file (manual_final.json) , provide the input file name in terminal

E:\work\Sprint 21\[MFL71728957]2046\output_folder\manual_final.json

It will also ask for output json file name(after data modelling and formatting)

korean_rf_MFL68864565.json


Output:
Images will be stored inside: 
\image_db

output json file  (ko_rf_MFL68864565.json) will be stored in current directory
It will also update partno_modelno_mapper.json file which contains the mapping between part_no and model_no

Step3:
Extract key values 
python keyextraction_engine.py

It will ask for json file

folder_name\ko_rf_MFL68864565.json

It will ask for name of the output file (key value)
senkey_ko_rf_MFL68864565.txt

Step4:
Generate Embeddings
embedextraction_engine.py

It will ask for key_value file as input

senkey_ko_rf_MFL68864565.txt

It will ask full path to json file as input

folder_name\ko_rf_MFL68864565.json
Output:
./Embeddings_ko/meta.json
./Embeddings_ko/emb_ko_rf_MFL68864565.json

Note:
Each time we run embedextraction_engine.py, with new key value file for new model, meta.json file gets updated with new model (retains previously computed model)
and new embedding file gets created, the naming convention of embedding file is emb_ + manual_json_file_name eg.
emb_ko_rf_MFL68864565.json in this case.





