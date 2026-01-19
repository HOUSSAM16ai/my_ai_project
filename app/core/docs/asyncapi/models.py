from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field

class ExternalDocumentation(BaseModel):
    description: Optional[str] = None
    url: str

class Tag(BaseModel):
    name: str
    description: Optional[str] = None
    externalDocs: Optional[ExternalDocumentation] = None

class Reference(BaseModel):
    ref: str = Field(alias="$ref")

class Schema(BaseModel):
    type: Optional[str] = None
    properties: Optional[Dict[str, Union['Schema', Reference]]] = None
    required: Optional[List[str]] = None
    description: Optional[str] = None

class Message(BaseModel):
    messageId: Optional[str] = None
    headers: Optional[Union[Schema, Reference]] = None
    payload: Optional[Union[Schema, Reference]] = None
    correlationId: Optional[Union[Schema, Reference]] = None
    schemaFormat: Optional[str] = None
    contentType: Optional[str] = None
    name: Optional[str] = None
    title: Optional[str] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[Tag]] = None
    externalDocs: Optional[ExternalDocumentation] = None
    bindings: Optional[Dict[str, object]] = None

class Parameter(BaseModel):
    description: Optional[str] = None
    schema_data: Optional[Union[Schema, Reference]] = Field(default=None, alias="schema")
    location: Optional[str] = None

class ChannelBinding(BaseModel):
    # This acts as a base for protocol specific bindings (e.g. amqp, kafka, http)
    model_config = {"extra": "allow"}

class OperationBinding(BaseModel):
    model_config = {"extra": "allow"}

class Channel(BaseModel):
    address: Optional[str] = None
    messages: Optional[Dict[str, Union[Message, Reference]]] = None
    title: Optional[str] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    servers: Optional[List[Reference]] = None
    parameters: Optional[Dict[str, Union[Parameter, Reference]]] = None
    bindings: Optional[Dict[str, Union[ChannelBinding, Reference, object]]] = None
    tags: Optional[List[Tag]] = None
    externalDocs: Optional[ExternalDocumentation] = None

class Operation(BaseModel):
    action: str  # 'send' or 'receive'
    channel: Reference
    title: Optional[str] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    security: Optional[List[Dict[str, List[str]]]] = None
    tags: Optional[List[Tag]] = None
    externalDocs: Optional[ExternalDocumentation] = None
    bindings: Optional[Dict[str, Union[OperationBinding, Reference, object]]] = None
    messages: Optional[List[Reference]] = None
    reply: Optional[object] = None

class Components(BaseModel):
    schemas: Optional[Dict[str, Union[Schema, Reference]]] = None
    servers: Optional[Dict[str, object]] = None
    channels: Optional[Dict[str, Union[Channel, Reference]]] = None
    operations: Optional[Dict[str, Union[Operation, Reference]]] = None
    messages: Optional[Dict[str, Union[Message, Reference]]] = None
    parameters: Optional[Dict[str, Union[Parameter, Reference]]] = None
    correlationIds: Optional[Dict[str, object]] = None
    operationTraits: Optional[Dict[str, object]] = None
    messageTraits: Optional[Dict[str, object]] = None
    serverBindings: Optional[Dict[str, object]] = None
    channelBindings: Optional[Dict[str, object]] = None
    operationBindings: Optional[Dict[str, object]] = None
    messageBindings: Optional[Dict[str, object]] = None

class Info(BaseModel):
    title: str
    version: str
    description: Optional[str] = None
    termsOfService: Optional[str] = None
    contact: Optional[Dict[str, object]] = None
    license: Optional[Dict[str, object]] = None

class AsyncAPI30(BaseModel):
    asyncapi: str = "3.0.0"
    id: Optional[str] = None
    info: Info
    servers: Optional[Dict[str, object]] = None
    defaultContentType: Optional[str] = None
    channels: Optional[Dict[str, Union[Channel, Reference]]] = None
    operations: Optional[Dict[str, Union[Operation, Reference]]] = None
    components: Optional[Components] = None
