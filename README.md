# Tellor Airflow
This repository contains [Apache Airflow DAGs](https://airflow.apache.org/docs/apache-airflow/stable/concepts/dags.html) for executing `submitValue` transactions to Tellor Oracles.

# Usage
You will need to run this using Docker and Docker Compose.
```
docker-compose up
```
:information_source: This will take a while the first time you do it
:warning: You may need to increase your Docker memory to > 4GB, default is 2GB
# Setup
After starting up Airflow, navigate to `Admin > Connections` and setup the following:
* A `HTTP` connection called `infura` with the connection's `Extra` as:
```
{
"http_endpoint_uri": "YOUR_INFURA_HTTP_URI",
"wss_endpoint_uri": "YOUR_INFURA_WSS_URI"
}
```
* Another `HTTP` connection called `YOUR_REPORTER_WALLET_ADDRESS`, that is, name this connection as the address you plan to use for reporting values to Tellor
  * Set the `Login` to `YOUR_REPORTER_WALLET_ADDRESS`
  * Set the `Password` to `YOUR_PRIVATE_KEY` (private key is needed to execute txns automatically)

Lastly, navigate to `Admin > Variables` and add the following:
* `tellor-address` - the contract address for the Tellor Oracle
* `reporter-address` - the address used for reporting to the oracle


Once things have booted up, log in with username `airflow` and password  `airflow`.
