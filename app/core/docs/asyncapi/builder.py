from app.core.docs.asyncapi.models import (
    AsyncAPI30,
    Channel,
    Components,
    Info,
    Operation,
    Parameter,
    Reference,
)


class AsyncAPIBuilder:
    def __init__(self, title: str, version: str, description: str = ""):
        self.doc = AsyncAPI30(
            info=Info(title=title, version=version, description=description),
            channels={},
            operations={},
            components=Components(
                schemas={},
                parameters={},
                channels={},
                operations={},
                messages={},
            ),
        )

    def add_channel(
        self,
        channel_id: str,
        address: str,
        parameters: dict[str, Parameter] | None = None,
        description: str | None = None,
    ) -> str:
        """
        Adds a reusable channel definition.
        In AsyncAPI 3.0, channels are the 'address' and can be defined in components or root.
        Here we define them in components for reusability.
        """
        channel = Channel(
            address=address,
            parameters=parameters,
            description=description,
        )
        if self.doc.components.channels is None:
            self.doc.components.channels = {}

        self.doc.components.channels[channel_id] = channel
        return channel_id

    def add_operation(
        self,
        operation_id: str,
        action: str,
        channel_ref_id: str,
        summary: str | None = None,
        bindings: dict[str, object] | None = None,
    ) -> str:
        """
        Adds an operation that references a channel.
        This demonstrates the separation: Operation -> (references) -> Channel.
        """
        if channel_ref_id not in self.doc.components.channels:
            # If strictly enforcing internal consistency, we might raise error here.
            # But let's assume valid reference.
            pass

        operation = Operation(
            action=action,
            channel=Reference(**{"$ref": f"#/components/channels/{channel_ref_id}"}),
            summary=summary,
            bindings=bindings,
        )

        if self.doc.operations is None:
            self.doc.operations = {}

        self.doc.operations[operation_id] = operation
        return operation_id

    def resolve_operation_channel(self, operation_id: str) -> dict[str, object]:
        """
        'Intelligent' helper to resolve the full context of an operation,
        merging the Operation details with the referenced Channel details.

        This answers the Q2 scenario: How to get the channel parameters for a specific operation.
        """
        op = self.doc.operations.get(operation_id)
        if not op:
            raise ValueError(f"Operation {operation_id} not found")

        # Resolve Channel Reference
        ref = op.channel.ref
        if not ref.startswith("#/components/channels/"):
            raise ValueError(f"Complex resolution for {ref} not implemented in this demo")

        channel_id = ref.split("/")[-1]
        channel = self.doc.components.channels.get(channel_id)

        if not channel:
            raise ValueError(f"Channel {channel_id} not found")

        # Merge Logic:
        # The parameters belong to the Channel.
        # The binding might belong to Operation or Channel.

        return {
            "operation_id": operation_id,
            "action": op.action,
            "channel_address": channel.address,
            "channel_parameters": channel.parameters,
            "operation_bindings": op.bindings,
            "channel_bindings": channel.bindings,
        }
