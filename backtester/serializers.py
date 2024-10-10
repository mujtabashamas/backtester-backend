from rest_framework import serializers
from backtester.models import Strategy


class CreateStrategySerializer(serializers.ModelSerializer):
    class Meta:
        model = Strategy
        fields = ("name", "prompt")

    def create(self, validated_data):
        return Strategy.objects.create(**validated_data)


class ListStrategySerializer(serializers.ModelSerializer):
    strategy_id = serializers.IntegerField(source="id", read_only=True)

    class Meta:
        model = Strategy
        fields = (
            "strategy_id",
            "name",
            "prompt",
            "strategy_code",
            "parameters",
        )


class UpdateStrategySerializer(serializers.ModelSerializer):

    class Meta:
        model = Strategy
        fields = (
            "name",
            "prompt",
            "strategy_code",
            "parameters",
        )

    def update(self, instance, validated_data):
        instance.prompt = validated_data.get("prompt", instance.prompt)
        instance.strategy_code = validated_data.get(
            "strategy_code", instance.strategy_code
        )
        instance.parameters = validated_data.get("parameters", instance.parameters)
        instance.save()
        return instance
