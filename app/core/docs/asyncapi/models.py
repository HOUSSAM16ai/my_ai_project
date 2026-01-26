# ruff: noqa: N815

from typing import Union

from pydantic import BaseModel, Field


class ExternalDocumentation(BaseModel):
    description: str | None = None
    url: str


class Tag(BaseModel):
    name: str
    description: str | None = None
    externalDocs: ExternalDocumentation | None = None


class Reference(BaseModel):
    ref: str = Field(alias="$ref")


class Schema(BaseModel):
    type: str | None = None
    properties: dict[str, Union["Schema", Reference]] | None = None
    required: list[str] | None = None
    description: str | None = None


class Message(BaseModel):
    messageId: str | None = None
    headers: Schema | Reference | None = None
    payload: Schema | Reference | None = None
    correlationId: Schema | Reference | None = None
    schemaFormat: str | None = None
    contentType: str | None = None
    name: str | None = None
    title: str | None = None
    summary: str | None = None
    description: str | None = None
    tags: list[Tag] | None = None
    externalDocs: ExternalDocumentation | None = None
    bindings: dict[str, object] | None = None


class Parameter(BaseModel):
    description: str | None = None
    schema_data: Schema | Reference | None = Field(default=None, alias="schema")
    location: str | None = None


class ChannelBinding(BaseModel):
    # This acts as a base for protocol specific bindings (e.g. amqp, kafka, http)
    model_config = {"extra": "allow"}


class OperationBinding(BaseModel):
    model_config = {"extra": "allow"}


class Channel(BaseModel):
    address: str | None = None
    messages: dict[str, Message | Reference] | None = None
    title: str | None = None
    summary: str | None = None
    description: str | None = None
    servers: list[Reference] | None = None
    parameters: dict[str, Parameter | Reference] | None = None
    bindings: dict[str, ChannelBinding | Reference | object] | None = None
    tags: list[Tag] | None = None
    externalDocs: ExternalDocumentation | None = None


class Operation(BaseModel):
    action: str  # 'send' or 'receive'
    channel: Reference
    title: str | None = None
    summary: str | None = None
    description: str | None = None
    security: list[dict[str, list[str]]] | None = None
    tags: list[Tag] | None = None
    externalDocs: ExternalDocumentation | None = None
    bindings: dict[str, OperationBinding | Reference | object] | None = None
    messages: list[Reference] | None = None
    reply: object | None = None


class Components(BaseModel):
    schemas: dict[str, Schema | Reference] | None = None
    servers: dict[str, object] | None = None
    channels: dict[str, Channel | Reference] | None = None
    operations: dict[str, Operation | Reference] | None = None
    messages: dict[str, Message | Reference] | None = None
    parameters: dict[str, Parameter | Reference] | None = None
    correlationIds: dict[str, object] | None = None
    operationTraits: dict[str, object] | None = None
    messageTraits: dict[str, object] | None = None
    serverBindings: dict[str, object] | None = None
    channelBindings: dict[str, object] | None = None
    operationBindings: dict[str, object] | None = None
    messageBindings: dict[str, object] | None = None


class Info(BaseModel):
    title: str
    version: str
    description: str | None = None
    termsOfService: str | None = None
    contact: dict[str, object] | None = None
    license: dict[str, object] | None = None


class AsyncAPI30(BaseModel):
    asyncapi: str = "3.0.0"
    id: str | None = None
    info: Info
    servers: dict[str, object] | None = None
    defaultContentType: str | None = None
    channels: dict[str, Channel | Reference] | None = None
    operations: dict[str, Operation | Reference] | None = None
    components: Components | None = None
