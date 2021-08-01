"""
Tellor Oracle Reporter Workflow

Overview:
- Checks the price on coingecko
- Submits the price to Tellor Mesosphere
- Waits to see 1 block confirmations on the transaction

Pre-requisites:
- set `reporter-address` in Airflow's Variables for an approved reporter
- set `tellor-address` in Airflow's Variables to the Mesosphere address

"""
from airflow import DAG
from airflow.models import Variable
from datetime import datetime, timedelta
from airflow.operators.bash_operator import BashOperator
from airflow.operators.python_operator import PythonOperator
from airflow_ethereum.web3_hook import Web3Hook
from airflow_ethereum.ethereum_transaction_confirmation_sensor import EthereumTransactionConfirmationSensor
from airflow_ethereum.tellor_oracle_operator import TellorOracleOperator
from abi.tellor import TELLOR_ABI
from json import loads
import requests

WALLET_ADDRESS = Variable.get("reporter-address", "0xe07c9696e00f23Fc7bAE76d037A115bfF33E28be")
TELLOR_CONTRACT_ADDRESS = Variable.get("tellor-address", "0xA0c5d95ec359f4A33371a06C23D89BA6Fc591A97")

default_args = {
    "owner": "ricochet",
    "depends_on_past": False,
    "start_date": datetime(2020, 3, 29),
    "email": ["mike@mikeghen.com"],
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 0,
    "retry_delay": timedelta(minutes=1)
}


dag = DAG("tellor_reporter",
          max_active_runs=1,
          catchup=False,
          default_args=default_args,
          schedule_interval="* * * * *")


def check_price(**context):
    """
    Check the price of the assets to use for updating the oracle
    """
    url = "https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd"
    response = requests.get(url)
    result = response.json()
    # Raise the price by 20 basis points and scale for Tellor
    price = int(result["ethereum"]["usd"] * 1.002 * 1000000)
    return price


done = BashOperator(
    task_id='done',
    bash_command='date',
    dag=dag,
)

price_check = PythonOperator(
    task_id="price_check",
    provide_context=True,
    python_callable=check_price,
    dag=dag
)

oracle_update = TellorOracleOperator(
    task_id="oracle_update",
    web3_conn_id="infura",
    ethereum_wallet=WALLET_ADDRESS,
    contract_address=TELLOR_CONTRACT_ADDRESS,
    # Get the price from the price_check task using Airflow XCom
    price='{{task_instance.xcom_pull(task_ids="price_check")}}',
    request_id=1,
    gas_multiplier=10,
    gas=250000,
    dag=dag,
)

# NOTE: Does not handle failed transactions, waits for block confirmations not success/failure of txns
confirm_oracle_update = EthereumTransactionConfirmationSensor(
    task_id="confirm_oracle_update",
    web3_conn_id="infura",
    transaction_hash="{{task_instance.xcom_pull(task_ids='oracle_update')}}",
    confirmations=1,
    poke_interval=20,
    dag=dag
)

done << confirm_oracle_update << oracle_update << price_check
