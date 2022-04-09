#!/bin/bash
args=()
setup=true; migrate=true; cmd='runserver'
while (( $# )); do
  case $1 in
    --without-setup)   setup=false ;;
    --without-migrate) migrate=false ;;
    --app)             cmd='app'   app=$2 ;;
    --test)            cmd='test'  tests_app=$2 ;;
    --*)               printf 'Unknown option: %q\n\n' "$1" ;;
    *)                 args+=( "$1" ) ;;
  esac
  shift
done

echo "$cmd"
if [ "$cmd" = "app" ]; then
  echo '##############################'
  echo 'app:' $app
  echo '##############################'
elif [ "$cmd" = "test" ]; then
  echo '##############################'
  echo 'tests_app:' $tests_app
  echo '##############################'
  echo 'Removing other tests app file'
  echo '##############################'
  cd rest_api/tests/
  tests_app_file="tests_app_${tests_app}.py"
  find . -name 'tests_app_*.py' ! -name $tests_app_file -type f -exec rm {} \;
  cd ../../
fi

# setup 
if $setup ; then
  # install reqruired libraries
  sudo apt-get --assume-yes install python3-venv

  # activate virtual environment
  python3 -m venv env
  source env/bin/activate
  pip install --upgrade pip

  # install required python modules
  pip3 install -r requirements.txt
  if [ "$app" = "ker" ] || [ "$tests_app" = "ker" ]; then
    pip3 install -r apps/ker/requirements.txt
    python -m nltk.downloader stopwords punkt wordnet
    python -m spacy download en
  elif [ "$app" = "ker_ko" ] || [ "$tests_app" = "ker_ko" ]; then
    pip3 install -r apps/ker_ko/requirements.txt
    python -m spacy download en
  fi
  echo yes | python3 manage.py collectstatic
fi

# activate venv
source env/bin/activate

# migrate
if $migrate ; then
    python3 manage.py makemigrations
    python3 manage.py migrate
fi
venv_dir='./env/*'
dashboard_dir='./neo4j_dashboard/*'
unittest_dir='./rest_api/tests/*'
omit_engine='./engines/EngineFactory.py'
omit_list_ker_dirs='./apps/ker/knowledge_extraction/docextraction/*,./apps/ker/knowledge_extraction/datamodel/*,./apps/ker/knowledge_extraction/response/json_builder.py,./apps/ker/knowledge_extraction/extraction_engine.py,./apps/ker/knowledge_extraction/lg_logging.py,apps/ker/knowledge_extraction/mapping/model_no_mapper.py,apps/ker/knowledge_extraction/dialogue_manager/unit_converter.py,apps/ker/components/engine/pipeline_2.py,apps/ker/components/engine/pipeline_3.py,apps/ker/components/engine/utils.py,apps/ker/components/info_extraction/info_extraction_base.py,apps/ker/components/info_extraction/rule_based/info_extraction.py,apps/ker/components/info_extraction/utils.py,apps/ker/components/nlg/dialo_gpt/predict.py,apps/ker/components/nlg/nlg_engine.py,apps/ker/components/text_similarity/base_question_extraction.py,apps/ker/components/text_similarity/siamese_bert.py,./apps/ker/components/text_similarity/utils.py,./apps/ker/external/os_tools/uncompress_tool.py,./apps/ker/components/paraqa/paraqa.py,./apps/ker/components/paraqa/passageretrival.py,./apps/ker/external/*'
omit_list_kerko_dirs='./apps/ker_ko/knowledge_extraction/docextraction/*,./apps/ker_ko/knowledge_extraction/datamodel/*,./apps/ker_ko/knowledge_extraction/response/json_builder.py,./apps/ker_ko/knowledge_extraction/extraction_engine.py,./apps/ker_ko/lg_logging.py'
omit_list_kerko_modules='./apps/ker_ko/components/classifier/modeling.py,./apps/ker_ko/components/classifier/optimization.py,./apps/ker_ko/components/classifier/run_classifier.py,./apps/ker_ko/components/classifier/utils.py,./apps/ker_ko/components/engine/pipeline_2.py,./apps/ker_ko/components/engine/pipeline_3.py,./apps/ker_ko/components/text_similarity/base_question_extraction.py,./apps/ker_ko/components/engine/utils.py,./apps/ker_ko/components/text_similarity/siamese_bert.py,./apps/ker_ko/components/text_similarity/utils.py,./apps/ker_ko/knowledge_extraction/dialogue_manager/speckeyextractor.py,./apps/ker_ko/knowledge_extraction/dialogue_manager/unit_converter.py,./apps/ker_ko/knowledge_extraction/dialogue_manager/unithandler.py,./apps/ker_ko/knowledge_extraction/dialogue_manager/value_unit_extractor.py,./apps/ker_ko/components/info_extraction/utils.py,./apps/ker_ko/components/info_extraction/info_extraction_base.py,./apps/ker_ko/knowledge_extraction/knowledge/query/query_utils.py,./apps/ker_ko/knowledge_extraction/dialogue_manager/new_unit_converter.py,./apps/ker_ko/knowledge_extraction/dialogue_manager/spec_key_classifier.py,./apps/ker_ko/knowledge_extraction/dialogue_manager/speckeyextractor.py,./apps/ker_ko/knowledge_extraction/dialogue_manager/speckey_handler.py,./apps/ker_ko/knowledge_extraction/dialogue_manager/unit_converter.py,./apps/ker_ko/knowledge_extraction/dialogue_manager/unithandler.py,./apps/ker_ko/knowledge_extraction/dialogue_manager/value_unit_extractor.py,./apps/ker_ko/knowledge_extraction/mapping/key_mapper.py'
omit_list+=$venv_dir
omit_list+=','$dashboard_dir
omit_list+=','$unittest_dir
omit_list+=','$omit_engine
if [ "$tests_app" = "ker" ]; then
  omit_list+=','$omit_list_ker_dirs
elif [ "$tests_app" = "ker_ko" ]; then
  omit_list+=','$omit_list_kerko_dirs
  omit_list+=','$omit_list_kerko_modules
fi
case "$cmd" in
  runserver)  python3 manage.py runserver 0.0.0.0:8080 --noreload ;;
  test)       coverage erase;
              coverage run --omit=$omit_list manage.py test;
              coverage report;
              coverage html ;;
esac

