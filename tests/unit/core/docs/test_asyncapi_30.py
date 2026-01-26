from app.core.docs.asyncapi.builder import AsyncAPIBuilder
from app.core.docs.asyncapi.models import Parameter, Schema


def test_asyncapi_30_separation_scenario():
    """
    Scenario:
    User is migrating from AsyncAPI 2.6 to 3.0.
    Original: 'user/signup' channel with publish operation.
    New 3.0:
        - Channel 'user/signup' defined separately.
        - Operation 'sendWelcomeEmail' (receive) -> binds to 'user/signup'
        - Operation 'logAuditTrail' (receive) -> binds to 'user/signup'

    Problem (Q2): Multiple operations interact with the same channel but require different parameter bindings.
    Solution verification: Ensure Channel Parameters are defined once (on Channel) but accessible by both operations,
    while Operations can have their own bindings (e.g., protocol specifics) or we can inspect how they share the channel def.
    """

    builder = AsyncAPIBuilder(title="User System", version="1.0.0")

    # 1. Define the Shared Channel with Parameters
    # The channel address might be 'user/signup/{region}'
    # 'region' is a channel parameter.

    region_param = Parameter(
        description="The region where the signup occurred",
        schema=Schema(type="string", properties={}),
    )

    builder.add_channel(
        channel_id="userSignupChannel",
        address="user/signup/{region}",
        parameters={"region": region_param},
        description="Channel for user signup events",
    )

    # 2. Define Operation 1: sendWelcomeEmail
    # Logic: When the app *receives* a signup event, it sends an email.
    # So action is 'receive' (from the perspective of the application).
    builder.add_operation(
        operation_id="sendWelcomeEmail",
        action="receive",
        channel_ref_id="userSignupChannel",
        summary="Sends a welcome email on signup",
        bindings={"amqp": {"queue": {"name": "welcome-email-queue"}}},
    )

    # 3. Define Operation 2: logAuditTrail
    # Logic: Also receives the same event but maybe via a different queue or consumer group (Kafka).
    builder.add_operation(
        operation_id="logAuditTrail",
        action="receive",
        channel_ref_id="userSignupChannel",
        summary="Logs the signup to audit trail",
        bindings={"kafka": {"groupId": "audit-log-group"}},
    )

    # 4. Verification / Resolution

    # Resolve Operation 1
    context1 = builder.resolve_operation_channel("sendWelcomeEmail")
    assert context1["channel_address"] == "user/signup/{region}"
    assert "region" in context1["channel_parameters"]
    # In Pydantic, if we stored it as a generic Dict or if we populated a Pydantic model with extra fields allowed,
    # we need to access it appropriately. The builder passes the raw dict into the Operation.bindings which is:
    # Optional[Dict[str, Union[OperationBinding, Reference, Any]]]
    # Since we passed a dict, and the model definition says Union[OperationBinding, Reference, Any],
    # Pydantic might have instantiated OperationBinding if it matched, or kept it as Dict if Any matched?
    # Actually OperationBinding is empty with extra=allow. So it likely instantiated OperationBinding.
    # But OperationBinding is a Pydantic model, so we can't use ["amqp"]. We must use .amqp or model_dump() or getattr.

    # However, since the input was {"amqp": ...} and OperationBinding allows extra,
    # the dictionary keys become attributes.

    # Let's check how it's actually stored.
    # The simplest fix for the test is to treat it as a dictionary if it's a model.

    bindings1 = context1["operation_bindings"]
    # If it's a dict of OperationBinding objects? No, the model says:
    # bindings: Optional[Dict[str, Union[OperationBinding, Reference, Any]]]
    # We passed `bindings={"amqp": {"queue": ...}}`.
    # Pydantic likely validates the value `{"queue": ...}` against `OperationBinding`.
    # So bindings1 is a Dict where key is "amqp" and value is OperationBinding instance (with extra fields).

    amqp_binding = bindings1["amqp"]
    # amqp_binding is an OperationBinding object. We need to access its fields.
    # Since extra="allow", we can access attributes.

    assert amqp_binding.queue["name"] == "welcome-email-queue"

    # Resolve Operation 2
    context2 = builder.resolve_operation_channel("logAuditTrail")
    assert context2["channel_address"] == "user/signup/{region}"
    assert "region" in context2["channel_parameters"]

    kafka_binding = context2["operation_bindings"]["kafka"]
    assert kafka_binding.groupId == "audit-log-group"

    print(
        "\n✅ Verification Successful: Both operations share the Channel definition (and its parameters) but maintain distinct operation bindings."
    )


if __name__ == "__main__":
    test_asyncapi_30_separation_scenario()
