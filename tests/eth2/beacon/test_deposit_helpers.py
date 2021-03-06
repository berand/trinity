import pytest

from eth_utils import (
    ValidationError,
)

from eth2.beacon.deposit_helpers import (
    add_pending_validator,
    process_deposit,
    validate_proof_of_possession,
)
from eth2.beacon.types.states import BeaconState
from eth2.beacon.types.validator_records import ValidatorRecord
from eth2.beacon.types.deposit_input import DepositInput

from eth2.beacon.tools.builder.validator import (
    sign_proof_of_possession,
)


def test_add_pending_validator(sample_beacon_state_params,
                               sample_validator_record_params):

    validator_registry_len = 2
    state = BeaconState(**sample_beacon_state_params).copy(
        validator_registry=[
            ValidatorRecord(**sample_validator_record_params)
            for _ in range(validator_registry_len)
        ],
        validator_balances=(100,) * validator_registry_len,
    )
    validator = ValidatorRecord(**sample_validator_record_params)
    amount = 5566
    state = add_pending_validator(
        state,
        validator,
        amount,
    )

    assert state.validator_registry[-1] == validator


@pytest.mark.parametrize(
    "expected",
    (
        (True),
        (ValidationError),
    ),
)
def test_validate_proof_of_possession(
        epoch_length,
        sample_beacon_state_params,
        pubkeys,
        privkeys,
        expected):
    state = BeaconState(**sample_beacon_state_params)

    privkey = privkeys[0]
    pubkey = pubkeys[0]
    withdrawal_credentials = b'\x34' * 32

    deposit_input = DepositInput(
        pubkey=pubkey,
        withdrawal_credentials=withdrawal_credentials,
    )
    if expected is True:
        proof_of_possession = sign_proof_of_possession(
            deposit_input,
            privkey,
            state.fork,
            state.slot,
            epoch_length,
        )

        validate_proof_of_possession(
            state=state,
            pubkey=pubkey,
            proof_of_possession=proof_of_possession,
            withdrawal_credentials=withdrawal_credentials,
            epoch_length=epoch_length,
        )
    else:
        proof_of_possession = b'\x11' * 96
        with pytest.raises(ValidationError):
            validate_proof_of_possession(
                state=state,
                pubkey=pubkey,
                proof_of_possession=proof_of_possession,
                withdrawal_credentials=withdrawal_credentials,
                epoch_length=epoch_length,
            )


def test_process_deposit(epoch_length,
                         sample_beacon_state_params,
                         privkeys,
                         pubkeys,
                         max_deposit_amount):
    state = BeaconState(**sample_beacon_state_params).copy(
        slot=1,
        validator_registry=(),
    )

    privkey_1 = privkeys[0]
    pubkey_1 = pubkeys[0]
    amount = max_deposit_amount
    withdrawal_credentials = b'\x34' * 32

    deposit_input = DepositInput(
        pubkey=pubkey_1,
        withdrawal_credentials=withdrawal_credentials,
    )
    proof_of_possession = sign_proof_of_possession(
        deposit_input,
        privkey_1,
        state.fork,
        state.slot,
        epoch_length,
    )

    # Add the first validator
    result_state = process_deposit(
        state=state,
        pubkey=pubkey_1,
        amount=amount,
        proof_of_possession=proof_of_possession,
        withdrawal_credentials=withdrawal_credentials,
        epoch_length=epoch_length,
    )

    assert len(result_state.validator_registry) == 1
    index = 0
    assert result_state.validator_registry[0].pubkey == pubkey_1
    assert result_state.validator_registry[index].withdrawal_credentials == withdrawal_credentials
    assert result_state.validator_balances[index] == amount
    # test immutable
    assert len(state.validator_registry) == 0

    # Add the second validator
    privkey_2 = privkeys[1]
    pubkey_2 = pubkeys[1]
    deposit_input = DepositInput(
        pubkey=pubkey_2,
        withdrawal_credentials=withdrawal_credentials,
    )
    proof_of_possession = sign_proof_of_possession(
        deposit_input,
        privkey_2,
        state.fork,
        state.slot,
        epoch_length,
    )
    result_state = process_deposit(
        state=result_state,
        pubkey=pubkey_2,
        amount=amount,
        proof_of_possession=proof_of_possession,
        withdrawal_credentials=withdrawal_credentials,
        epoch_length=epoch_length,
    )
    assert len(result_state.validator_registry) == 2
    assert result_state.validator_registry[1].pubkey == pubkey_2
