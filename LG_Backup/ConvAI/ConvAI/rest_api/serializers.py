'''
Define serialization/deserialization methods.

The serializer provides a way to serialize or deserialize our defined model instances in JSON-like form.
You can also customize the serializer to change how instances are created or modified.
We implemented serializer to enable serialization/deserialization between data and model instances using ModelSerializer.
'''

from rest_framework import serializers


class DynamicFieldsSerializer(serializers.Serializer):
    """
    A DynamicFieldsSerializer that takes an additional `fields` argument that
    controls which fields should be displayed.
    """

    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        fields = kwargs.pop('fields', None)

        # Instantiate the superclass normally
        super(DynamicFieldsSerializer, self).__init__(*args, **kwargs)

        if fields is not None:
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)


class RetrievePostSerializer(serializers.Serializer):
    """
    A RetrievePostSerializer, "from" is a python reserved word
    """
    frm = serializers.CharField()
    to = serializers.CharField()
    ontology_id = serializers.CharField()
    process = serializers.CharField()
    query = serializers.JSONField()

    class Meta:
        model = None
        fields = '__all__'


class ConstructPostSerializer(serializers.Serializer):
    """
    A ConstructPostSerializer has json fields, "from" is a python reserved word
    """
    frm = serializers.CharField()
    to = serializers.CharField()
    ontology_id = serializers.CharField()
    process = serializers.CharField()
    application = serializers.CharField(required=False)

    class Meta:
        model = None
        fields = '__all__'

# "from" is a reserved word. So, the below is the workaroud for "from"
RetrievePostSerializer._declared_fields['from'] = RetrievePostSerializer._declared_fields['frm']
del RetrievePostSerializer._declared_fields['frm']
ConstructPostSerializer._declared_fields['from'] = ConstructPostSerializer._declared_fields['frm']
del ConstructPostSerializer._declared_fields['frm']
