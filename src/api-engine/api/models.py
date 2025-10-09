#
# SPDX-License-Identifier: Apache-2.0
#
import os
import shutil
import tarfile
from zipfile import ZipFile

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.postgres.fields import ArrayField

from api.common.enums import (
    HostStatus,
    HostType,
    K8SCredentialType,
    separate_upper_class,
    NodeStatus,
    FileType,
    FabricCAServerType,
    FabricCAUserType,
    FabricCAUserStatus,
)
from api.common.enums import (
    UserRole,
    NetworkType,
    FabricNodeType,
    FabricVersions,
)
from api.utils.common import make_uuid, random_name, hash_file
from api.config import CELLO_HOME
from api.validators import validate_url

SUPER_USER_TOKEN = getattr(settings, "ADMIN_TOKEN", "")
MAX_CAPACITY = getattr(settings, "MAX_AGENT_CAPACITY", 100)
MAX_NODE_CAPACITY = getattr(settings, "MAX_NODE_CAPACITY", 600)
MEDIA_ROOT = getattr(settings, "MEDIA_ROOT")
LIMIT_K8S_CONFIG_FILE_MB = 100
# Limit file upload size less than 100Mb
LIMIT_FILE_MB = 100
MIN_PORT = 1
MAX_PORT = 65535


class Govern(models.Model):
    id = models.UUIDField(
        primary_key=True,
        help_text="ID of govern",
        default=make_uuid,
        editable=True,
    )
    name = models.CharField(
        default="", max_length=64, help_text="Name of govern"
    )
    created_at = models.DateTimeField(auto_now_add=True)


class Organization(models.Model):
    id = models.UUIDField(
        primary_key=True,
        help_text="ID of organization",
        default=make_uuid,
        editable=True,
    )
    name = models.CharField(
        default="", max_length=64, help_text="Name of organization"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    msp = models.TextField(help_text="msp of organization", null=True)
    tls = models.TextField(help_text="tls of organization", null=True)
    agents = models.CharField(
        help_text="agent of organization",
        max_length=128,
        default="",
    )
    network = models.ForeignKey(
        "Network",
        help_text="Network to which the organization belongs",
        null=True,
        related_name="organization",
        on_delete=models.SET_NULL,
    )
    # channel = models.ForeignKey(
    #     "Channel",
    #     help_text="channel to which the organization belongs",
    #     null=True,
    #     related_name="channel",
    #     on_delete=models.SET_NULL
    # )

    class Meta:
        ordering = ("-created_at",)


class UserProfile(AbstractUser):
    id = models.UUIDField(
        primary_key=True,
        help_text="ID of user",
        default=make_uuid,
        editable=True,
    )
    email = models.EmailField(db_index=True, unique=True)
    username = models.CharField(
        default="", max_length=64, help_text="Name of user"
    )
    role = models.CharField(
        choices=UserRole.to_choices(True),
        default=UserRole.User.value,
        max_length=64,
    )
    organization = models.ForeignKey(
        Organization,
        null=True,
        on_delete=models.CASCADE,
        related_name="users",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "User Info"
        verbose_name_plural = verbose_name
        ordering = ["-date_joined"]

    def __str__(self):
        return self.username

    @property
    def is_admin(self):
        return self.role == UserRole.Admin.name.lower()

    @property
    def is_operator(self):
        return self.role == UserRole.Operator.name.lower()

    @property
    def is_common_user(self):
        return self.role == UserRole.User.name.lower()


def get_agent_config_file_path(instance, file):
    file_ext = file.split(".")[-1]
    filename = "%s.%s" % (hash_file(instance.config_file), file_ext)

    return os.path.join("config_files/%s" % str(instance.id), filename)


def validate_agent_config_file(file):
    file_size = file.size
    if file_size > LIMIT_K8S_CONFIG_FILE_MB * 1024 * 1024:
        raise ValidationError(
            "Max file size is %s MB" % LIMIT_K8S_CONFIG_FILE_MB
        )


class Agent(models.Model):
    id = models.UUIDField(
        primary_key=True,
        help_text="ID of agent",
        default=make_uuid,
        editable=True,
    )
    name = models.CharField(
        help_text="Agent name, can be generated automatically.",
        max_length=64,
        blank=True
    )
    urls = models.CharField(
        help_text="Agent URL", null=True, blank=True, validators=[validate_url]
    )
    organization = models.ForeignKey(
        "Organization",
        null=True,
        on_delete=models.CASCADE,
        help_text="Organization of agent",
        related_name="agent",
    )
    status = models.CharField(
        help_text="Status of agent",
        choices=HostStatus.to_choices(True),
        max_length=10,
        default=HostStatus.Active.name.lower(),
    )
    type = models.CharField(
        help_text="Type of agent",
        choices=HostType.to_choices(True),
        max_length=32,
        default=HostType.Docker.name.lower(),
    )
    config_file = models.FileField(
        help_text="Config file for agent",
        max_length=256,
        blank=True,
        upload_to=get_agent_config_file_path,
    )
    created_at = models.DateTimeField(
        help_text="Create time of agent", auto_now_add=True
    )

    # free_port = models.IntegerField(
    #     help_text="Agent free port.",
    #     default=30000,
    # )
    free_ports = ArrayField(
        models.IntegerField(blank=True),
        help_text="Agent free ports.",
        null=True,
    )

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = random_name("agent")
        super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        if self.config_file:
            if os.path.isfile(self.config_file.path):
                os.remove(self.config_file.path)
                shutil.rmtree(
                    os.path.dirname(self.config_file.path), ignore_errors=True
                )

        super(Agent, self).delete(using, keep_parents)

    class Meta:
        ordering = ("-created_at",)


@receiver(post_save, sender=Agent)
def extract_file(sender, instance, created, *args, **kwargs):
    if created:
        if instance.config_file:
            file_format = instance.config_file.name.split(".")[-1]
            if file_format in ["tgz", "gz"]:
                tar = tarfile.open(instance.config_file.path)
                tar.extractall(path=os.path.dirname(instance.config_file.path))
            elif file_format == "zip":
                with ZipFile(instance.config_file.path, "r") as zip_file:
                    zip_file.extractall(
                        path=os.path.dirname(instance.config_file.path)
                    )


class KubernetesConfig(models.Model):
    credential_type = models.CharField(
        help_text="Credential type of k8s",
        choices=K8SCredentialType.to_choices(separate_class_name=True),
        max_length=32,
        default=separate_upper_class(K8SCredentialType.CertKey.name),
    )
    enable_ssl = models.BooleanField(
        help_text="Whether enable ssl for api", default=False
    )
    ssl_ca = models.TextField(
        help_text="Ca file content for ssl", default="", blank=True
    )
    nfs_server = models.CharField(
        help_text="NFS server address for k8s",
        default="",
        max_length=256,
        blank=True,
    )
    parameters = models.JSONField(
        help_text="Extra parameters for kubernetes",
        default=dict,
        null=True,
        blank=True,
    )
    cert = models.TextField(
        help_text="Cert content for k8s", default="", blank=True
    )
    key = models.TextField(
        help_text="Key content for k8s", default="", blank=True
    )
    username = models.CharField(
        help_text="Username for k8s credential",
        default="",
        max_length=128,
        blank=True,
    )
    password = models.CharField(
        help_text="Password for k8s credential",
        default="",
        max_length=128,
        blank=True,
    )
    agent = models.ForeignKey(
        Agent,
        help_text="Agent of kubernetes config",
        on_delete=models.CASCADE,
        null=True,
    )


class Network(models.Model):
    id = models.UUIDField(
        primary_key=True,
        help_text="ID of network",
        default=make_uuid,
        editable=True,
    )
    name = models.CharField(
        help_text="network name, can be generated automatically.",
        max_length=64,
        unique=True,
        blank=True,
    )
    type = models.CharField(
        help_text="Type of network, %s" % NetworkType.values(),
        max_length=64,
        default=NetworkType.Fabric.value,
    )
    version = models.CharField(
        help_text="""
    Version of network.
    Fabric supported versions: %s
    """
        % (FabricVersions.values()),
        max_length=64,
        default="",
    )
    created_at = models.DateTimeField(
        help_text="Create time of network", auto_now_add=True
    )
    consensus = models.CharField(
        help_text="Consensus of network",
        max_length=128,
        default="raft",
    )
    genesisblock = models.TextField(
        help_text="genesis block",
        null=True,
    )
    database = models.CharField(
        help_text="database of network",
        max_length=128,
        default="leveldb",
    )

    class Meta:
        ordering = ("-created_at",)

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = random_name("network")
        super().save(*args, **kwargs)


def get_compose_file_path(instance, file):
    return os.path.join(
        "org/%s/agent/docker/compose_files/%s"
        % (str(instance.organization.id), str(instance.id)),
        "docker-compose.yml",
    )


def get_ca_certificate_path(instance, file):
    return os.path.join(
        "fabric/ca/certificates/%s" % str(instance.id), file.name
    )


def get_node_file_path(instance, file):
    """
    Get the file path where will be stored in
    :param instance: database object of this db record
    :param file: file object.
    :return: path of file system which will store the file.
    """
    file_ext = file.split(".")[-1]
    filename = "%s.%s" % (hash_file(instance.file), file_ext)

    return os.path.join(
        "files/%s/node/%s" % (str(instance.organization.id), str(instance.id)),
        filename,
    )


class FabricCA(models.Model):
    admin_name = models.CharField(
        help_text="Admin username for ca server",
        default="admin",
        max_length=32,
    )
    admin_password = models.CharField(
        help_text="Admin password for ca server",
        default="adminpw",
        max_length=32,
    )
    hosts = models.JSONField(
        help_text="Hosts for ca", null=True, blank=True, default=list
    )
    type = models.CharField(
        help_text="Fabric ca server type",
        default=FabricCAServerType.Signature.value,
        choices=FabricCAServerType.to_choices(),
        max_length=32,
    )


class PeerCaUser(models.Model):
    user = models.ForeignKey(
        "NodeUser",
        help_text="User of ca node",
        null=True,
        on_delete=models.CASCADE,
    )
    username = models.CharField(
        help_text="If user not set, set username/password",
        max_length=64,
        default="",
    )
    password = models.CharField(
        help_text="If user not set, set username/password",
        max_length=64,
        default="",
    )
    type = models.CharField(
        help_text="User type of ca",
        max_length=64,
        choices=FabricCAUserType.to_choices(),
        default=FabricCAUserType.User.value,
    )
    peer_ca = models.ForeignKey(
        "PeerCa",
        help_text="Peer Ca configuration",
        null=True,
        on_delete=models.CASCADE,
    )


class PeerCa(models.Model):
    node = models.ForeignKey(
        "Node",
        help_text="CA node of peer",
        null=True,
        on_delete=models.CASCADE,
    )
    peer = models.ForeignKey(
        "FabricPeer",
        help_text="Peer node",
        null=True,
        on_delete=models.CASCADE,
    )
    address = models.CharField(
        help_text="Node Address of ca", default="", max_length=128
    )
    certificate = models.FileField(
        help_text="Certificate file for ca node.",
        max_length=256,
        upload_to=get_ca_certificate_path,
        blank=True,
        null=True,
    )
    type = models.CharField(
        help_text="Type of ca node for peer",
        choices=FabricCAServerType.to_choices(),
        max_length=64,
        default=FabricCAServerType.Signature.value,
    )


class FabricPeer(models.Model):
    name = models.CharField(
        help_text="Name of peer node", max_length=64, default=""
    )
    gossip_use_leader_reflection = models.BooleanField(
        help_text="Gossip use leader reflection", default=True
    )
    gossip_org_leader = models.BooleanField(
        help_text="Gossip org leader", default=False
    )
    gossip_skip_handshake = models.BooleanField(
        help_text="Gossip skip handshake", default=True
    )
    local_msp_id = models.CharField(
        help_text="Local msp id of peer node", max_length=64, default=""
    )


class Node(models.Model):
    id = models.UUIDField(
        primary_key=True,
        help_text="ID of node",
        default=make_uuid,
        editable=True,
    )
    name = models.CharField(
        help_text="Node name", max_length=64, unique=True, blank=True
    )
    type = models.CharField(
        help_text="""
    Node type defined for network.
    Fabric available types: %s
    """
        % (FabricNodeType.names()),
        max_length=64,
    )
    urls = models.JSONField(
        help_text="URL configurations for node",
        null=True,
        blank=True,
        default=dict,
    )
    user = models.ForeignKey(
        UserProfile,
        help_text="User of node",
        null=True,
        on_delete=models.CASCADE,
    )
    organization = models.ForeignKey(
        Organization,
        help_text="Organization of node",
        null=True,
        related_name="node",
        on_delete=models.CASCADE,
    )
    agent = models.ForeignKey(
        Agent,
        help_text="Agent of node",
        null=True,
        related_name="node",
        on_delete=models.CASCADE,
    )
    # network = models.ForeignKey(
    #     Network,
    #     help_text="Network which node joined.",
    #     on_delete=models.CASCADE,
    #     null=True,
    # )
    created_at = models.DateTimeField(
        help_text="Create time of network", auto_now_add=True
    )
    status = models.CharField(
        help_text="Status of node",
        choices=NodeStatus.to_choices(True),
        max_length=64,
        default=NodeStatus.Created.name.lower(),
    )
    config_file = models.TextField(
        help_text="Config file of node",
        null=True,
    )
    msp = models.TextField(
        help_text="msp of node",
        null=True,
    )
    tls = models.TextField(
        help_text="tls of node",
        null=True,
    )
    cid = models.CharField(
        help_text="id used in agent, such as container id",
        max_length=256,
        default="",
    )

    class Meta:
        ordering = ("-created_at",)

    def get_compose_file_path(self):
        return "%s/org/%s/agent/docker/compose_files/%s/docker-compose.yml" % (
            MEDIA_ROOT,
            str(self.organization.id),
            str(self.id),
        )

    def save(
        self,
        force_insert=False,
        force_update=False,
        using=None,
        update_fields=None,
    ):
        if not self.name:
            self.name = random_name(self.type)
        super(Node, self).save(
            force_insert, force_update, using, update_fields
        )

    # def delete(self, using=None, keep_parents=False):
    #     if self.compose_file:
    #         compose_file_path = Path(self.compose_file.path)
    #         if os.path.isdir(os.path.dirname(compose_file_path)):
    #             shutil.rmtree(os.path.dirname(compose_file_path))
    #
    #     # remove related files of node
    #     if self.file:
    #         file_path = Path(self.file.path)
    #         if os.path.isdir(os.path.dirname(file_path)):
    #             shutil.rmtree(os.path.dirname(file_path))
    #
    #     if self.ca:
    #         self.ca.delete()
    #
    #     super(Node, self).delete(using, keep_parents)


class NodeUser(models.Model):
    name = models.CharField(
        help_text="User name of node", max_length=64, default=""
    )
    secret = models.CharField(
        help_text="User secret of node", max_length=64, default=""
    )
    user_type = models.CharField(
        help_text="User type of node",
        choices=FabricCAUserType.to_choices(),
        default=FabricCAUserType.Peer.value,
        max_length=64,
    )
    node = models.ForeignKey(
        Node, help_text="Node of user", on_delete=models.CASCADE, null=True
    )
    status = models.CharField(
        help_text="Status of node user",
        choices=FabricCAUserStatus.to_choices(),
        default=FabricCAUserStatus.Registering.value,
        max_length=32,
    )
    attrs = models.CharField(
        help_text="Attributes of node user", default="", max_length=512
    )

    class Meta:
        ordering = ("id",)


class Port(models.Model):
    node = models.ForeignKey(
        Node,
        help_text="Node of port",
        on_delete=models.CASCADE,
        null=True,
        related_name="port",
    )
    external = models.IntegerField(
        help_text="External port",
        default=0,
        validators=[MinValueValidator(MIN_PORT), MaxValueValidator(MAX_PORT)],
    )
    internal = models.IntegerField(
        help_text="Internal port",
        default=0,
        validators=[MinValueValidator(MIN_PORT), MaxValueValidator(MAX_PORT)],
    )

    class Meta:
        ordering = ("external",)


def get_file_path(instance, file):
    """
    Get the file path where will be stored in
    :param instance: database object of this db record
    :param file: file object.
    :return: path of file system which will store the file.
    """
    file_ext = file.split(".")[-1]
    filename = "%s.%s" % (hash_file(instance.file), file_ext)

    return os.path.join(
        "files/%s/%s" % (str(instance.organization.id), str(instance.id)),
        filename,
    )


def validate_file(file):
    """
    Validate file of upload
    :param file: file object
    :return: raise exception if validate failed
    """
    file_size = file.size
    if file_size > LIMIT_FILE_MB * 1024 * 1024:
        raise ValidationError("Max file size is %s MB" % LIMIT_FILE_MB)


class File(models.Model):
    id = models.UUIDField(
        primary_key=True,
        help_text="ID of file",
        default=make_uuid,
        editable=True,
    )
    organization = models.ForeignKey(
        Organization,
        help_text="Organization of file",
        null=True,
        on_delete=models.CASCADE,
    )
    name = models.CharField(help_text="File name", max_length=64, default="")
    file = models.FileField(
        help_text="File", max_length=256, blank=True, upload_to=get_file_path
    )
    created_at = models.DateTimeField(
        help_text="Create time of agent", auto_now_add=True
    )
    type = models.CharField(
        choices=FileType.to_choices(True),
        max_length=32,
        help_text="File type",
        default=FileType.Certificate.name.lower(),
    )

    class Meta:
        ordering = ("-created_at",)

    class User(models.Model):
        id = models.UUIDField(
            primary_key=True,
            help_text="ID of user",
            default=make_uuid,
            editable=True,
        )
        name = models.CharField(help_text="user name", max_length=128)
        roles = models.CharField(help_text="roles of user", max_length=128)
        organization = models.ForeignKey(
            "Organization", on_delete=models.CASCADE
        )
        attributes = models.CharField(
            help_text="attributes of user", max_length=128
        )
        revoked = models.CharField(help_text="revoked of user", max_length=128)
        create_ts = models.DateTimeField(
            help_text="Create time of user", auto_now_add=True
        )
        msp = models.TextField(
            help_text="msp of user",
            null=True,
        )
        tls = models.TextField(
            help_text="tls of user",
            null=True,
        )


class Channel(models.Model):
    id = models.UUIDField(
        primary_key=True,
        help_text="ID of Channel",
        default=make_uuid,
        editable=False,
        unique=True,
    )
    name = models.CharField(help_text="name of channel", max_length=128)
    organizations = models.ManyToManyField(
        to="Organization",
        help_text="the organization of the channel",
        related_name="channels",
        # on_delete=models.SET_NULL
    )
    create_ts = models.DateTimeField(
        help_text="Create time of Channel", auto_now_add=True
    )
    network = models.ForeignKey("Network", on_delete=models.CASCADE)
    orderers = models.ManyToManyField(
        to="Node",
        help_text="Orderer list in the channel",
    )
    config = models.JSONField(
        help_text="Channel config",
        default=dict,
        null=True,
        blank=True,
    )

    def get_channel_config_path(self):
        return "/var/www/server/" + self.name + "_config.block"

    def get_channel_artifacts_path(self, artifact):
        return CELLO_HOME + "/" + self.network.name + "/" + artifact

    # class ChainCode(models.Model):
    #     id = models.UUIDField(
    #         primary_key=True,
    #         help_text="ID of chainCode",
    #         default=make_uuid,
    #         editable=False,
    #         unique=True
    #     )
    #     name = models.CharField(
    #         help_text="ChainCode name", max_length=128
    #     )
    #     version = models.CharField(
    #         help_text="version of chainCode", max_length=128
    #     )
    #     creator = models.CharField(
    #         help_text="creator of chainCode", max_length=128
    #     )
    #     language = models.CharField(
    #         help_text="language of chainCode", max_length=128
    #     )
    #     channel = models.ManyToManyField("Channel")
    #     install_times = models.DateTimeField(
    #         help_text="Create time of install", auto_now_add=True
    #     )
    #     instantiate_times = models.DateTimeField(
    #         help_text="Create time of instantiate", auto_now_add=True
    #     )
    #     node = models.ManyToManyField("Node", related_name='node')
    #     status = models.CharField(
    #         help_text="status of chainCode", max_length=128
    #     )


class ChainCode(models.Model):
    id = models.UUIDField(
        primary_key=True,
        help_text="ID of ChainCode",
        default=make_uuid,
        editable=False,
        unique=True,
    )
    package_id = models.CharField(
        help_text="package_id of chainCode",
        max_length=128,
        editable=False,
        unique=True,
    )
    label = models.CharField(help_text="label of chainCode", max_length=128)
    creator = models.CharField(
        help_text="creator of chainCode", max_length=128
    )
    language = models.CharField(
        help_text="language of chainCode", max_length=128
    )
    description = models.CharField(
        help_text="description of chainCode",
        max_length=128,
        blank=True,
        null=True,
    )
    create_ts = models.DateTimeField(
        help_text="Create time of chainCode", auto_now_add=True
    )
