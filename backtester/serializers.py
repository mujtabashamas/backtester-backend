from rest_framework import serializers
from user_auth.serializers import UserSerializer
from backtester.models import Strategy


class StrategySerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    strategy_id = serializers.IntegerField(source="id", read_only=True)

    class Meta:
        model = Strategy
        fields = ["strategy_id", "prompt", "strategy_code", "parameters", "user"]
        read_only_fields = ["strategy_id", "user"]

    def create(self, validated_data):
        return Strategy.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.prompt = validated_data.get("prompt", instance.prompt)
        instance.strategy_code = validated_data.get(
            "strategy_code", instance.strategy_code
        )
        instance.parameters = validated_data.get("parameters", instance.parameters)
        instance.save()
        return instance
