from components.classifier.classifier_engine import ClassifierEngine

cs = ClassifierEngine()
result = cs.get_classifier_output("What are the causes of  PE error ?")
print(result) #Troubleshooting
cs = ClassifierEngine()
result = cs.get_classifier_output("What about the gas specifications for my washer?")
print(result) #Specification
#Two instanes of engine are created just to cehck if there is any clash between variables

#Evaluate on a file
cs = ClassifierEngine(saved_model=True)
cs.evaluate_on_file()


