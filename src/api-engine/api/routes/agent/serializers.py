#
# SPDX-License-Identifier: Apache-2.0
#
import logging

from django.core.validators import (
    RegexValidator,
    FileExtensionValidator,
)
from rest_framework import serializers

from api.common.enums import (
    LogLevel,
    K8SCredentialType,
    separate_upper_class,
)
from api.common.serializers import PageQuerySerializer, ListResponseSerializer
from api.models import Agent, KubernetesConfig, validate_agent_config_file
from api.utils.common import to_form_paras

LOG = logging.getLogger(__name__)

NameHelpText = "Name of Agent"
WorkerApiHelpText = "API address of worker"
IDHelpText = "ID of Agent"
CapacityHelpText = "Capacity of Agent"

NameMinLen = 4
NameMaxLen = 36
WorkerAPIMinLen = 6
WorkerAPIMaxLen = 128
CapacityMinValue = 1


class AgentQuery(PageQuerySerializer, serializers.ModelSerializer):
    class Meta:
        model = Agent
        fields = ("status", "name", "type", "page", "per_page", "organization")


class AgentIDSerializer(serializers.Serializer):
    id = serializers.UUIDField(help_text=IDHelpText)


class K8SParameterSerializer(serializers.ModelSerializer):
    parameters = serializers.DictField(
        help_text="Extra parameters", required=False
    )

    class Meta:
        model = KubernetesConfig
        fields = (
            "credential_type",
            "enable_ssl",
            "ssl_ca",
            "nfs_server",
            "parameters",
            "cert",
            "key",
            "username",
            "password",
        )
        extra_kwargs = {
            "credential_type": {"required": True},
            "enable_ssl": {"required": True},
            "nfs_server": {
                "validators": [
                    RegexValidator(
                        regex="^\d{1,3}\.\d{1,3}\.\d{1,3}"
                        "\.\d{1,3}:(\/+\w{0,}){0,}$",
                        message="Enter a valid nfs url.",
                    )
                ]
            },
        }

    def validate(self, attrs):
        credential_type = attrs.get("credential_type")
        if credential_type == separate_upper_class(
            K8SCredentialType.CertKey.name
        ):
            cert = attrs.get("cert")
            key = attrs.get("key")
            if not cert or not key:
                raise serializers.ValidationError("Need cert and key content")
            else:
                attrs["username"] = ""
                attrs["password"] = ""
        elif credential_type == separate_upper_class(
            K8SCredentialType.UsernamePassword.name
        ):
            username = attrs.get("username")
            password = attrs.get("password")
            if not username or not password:
                raise serializers.ValidationError("Need username and password")
            else:
                attrs["cert"] = ""
                attrs["key"] = ""
        elif credential_type == separate_upper_class(
            K8SCredentialType.Config.name
        ):
            # TODO: Add config type validation
            pass

        return attrs


class AgentCreateBody(serializers.ModelSerializer):
    # organization = serializers.UUIDField(help_text=IDHelpText)

    def to_form_paras(self):
        custom_paras = to_form_paras(self)

        return custom_paras

    class Meta:
        model = Agent
        fields = (
            "name",
            "type",
            "urls",
            "config_file",
            "organization",
        )
        extra_kwargs = {
            "type": {"required": True},
            "urls": {"required": True},
            "name": {"required": True},
            "organization": {"required": False},
            "config_file": {
                "required": False,
                "validators": [
                    FileExtensionValidator(
                        allowed_extensions=["tgz", "gz", "zip"]
                    ),
                    validate_agent_config_file,
                ],
            },
        }

    def validate(self, attrs):
        pass
        return attrs


class AgentPatchBody(serializers.Serializer):
    name = serializers.CharField(
        min_length=NameMinLen,
        max_length=NameMaxLen,
        help_text=NameHelpText,
        required=False,
        allow_null=True,
    )
    capacity = serializers.IntegerField(
        min_value=CapacityMinValue,
        required=False,
        allow_null=True,
        help_text=CapacityHelpText,
    )
    log_level = serializers.ChoiceField(
        choices=LogLevel.to_choices(),
        required=False,
        allow_null=True,
        help_text=LogLevel.get_info("Log levels:"),
    )


class AgentUpdateBody(AgentIDSerializer, serializers.ModelSerializer):
    # organization = serializers.UUIDField(
    #     help_text="Organization ID", required=True, allow_null=True
    # )

    class Meta:
        model = Agent
        fields = (
            "name",
            "type",
            "urls",
            "organization",
        )


class AgentResponseSerializer(AgentIDSerializer, serializers.ModelSerializer):
    organization = serializers.UUIDField(
        help_text="Organization ID", required=True, allow_null=True
    )

    class Meta:
        model = Agent
        fields = (
            "id",
            "name",
            "status",
            "created_at",
            "type",
            "urls",
            "organization",
        )
        extra_kwargs = {
            "id": {"required": True},
            "name": {"required": True},
            "status": {"required": True},
            "created_at": {"required": True, "read_only": False},
            "type": {"required": True},
            "organization": {"required": True},
            "urls": {"required": True},
        }


class AgentInfoSerializer(AgentIDSerializer, serializers.ModelSerializer):
    k8s_config = K8SParameterSerializer(
        help_text="Config of agent which is for kubernetes", required=False
    )
    organization_id = serializers.UUIDField(
        help_text="Organization ID", required=False, allow_null=True
    )

    class Meta:
        model = Agent
        fields = (
            "id",
            "name",
            "url",
            # "capacity",
            # "node_capacity",
            "status",
            "created_at",
            # "log_level",
            "type",
            # "schedulable",
            "k8s_config",
            "organization_id",
        )
        extra_kwargs = {
            "id": {"required": True},
            "name": {"required": True},
            "status": {"required": True},
            # "capacity": {"required": True},
            # "node_capacity": {"required": True},
            "created_at": {"required": True, "read_only": False},
            "type": {"required": True},
            # "log_level": {"required": True},
            # "schedulable": {"required": True},
        }


class AgentListResponse(ListResponseSerializer):
    data = AgentResponseSerializer(many=True, help_text="Agents data")


class AgentApplySerializer(serializers.ModelSerializer):
    class Meta:
        model = Agent
        fields = (
            "type",
            # "capacity"
        )
        extra_kwargs = {
            "type": {"required": True},
            # "capacity": {"required": True},
        }
